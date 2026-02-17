# -*- coding: utf-8 -*-
"""
==============================================
  京东通用交易平台 — 业务服务层
  功能：
    1. 处理京东提交充值/提取卡密请求（beginDistill）
    2. 处理京东生产反查请求（findDistill）
    3. 异步回调通知京东生产结果
==============================================
"""

import json
import uuid
import logging
from datetime import datetime

import requests

from app import db
from app.models.order import Order
from app.models.callback_log import JdCallback
from app.models.merchant_config import MerchantJdConfig
from app.utils.sign import jd_general_sign, verify_jd_general_sign
from app.utils.crypto import aes_encrypt, aes_decrypt

# 日志记录器
logger = logging.getLogger(__name__)


def generate_order_no():
    """
    生成我方唯一订单号
    格式：GT + 年月日时分秒 + 8位随机字符
    返回：唯一订单号字符串
    """
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"GT{now}{short_uuid}"


def handle_begin_distill(params: dict, merchant_id: int) -> dict:
    """
    处理京东通用交易 — 提交充值/提取卡密请求
    业务流程：
        1. 验证签名
        2. 防重处理（同一 jdOrderNo 不重复创建）
        3. 创建本地订单
        4. 返回生产结果
    参数：
        params      — 京东请求参数字典
        merchant_id — 商户ID
    返回：
        响应参数字典
    """
    # 查询商户配置
    config = MerchantJdConfig.query.filter_by(
        merchant_id=merchant_id, biz_type=1, is_enabled=1
    ).first()

    if not config or not config.md5_secret:
        logger.error(f"商户 {merchant_id} 通用交易配置不存在或未启用")
        return _build_error_response("JDO_500", "系统错误", params.get("jdOrderNo"))

    # 解密存储的密钥
    try:
        from app.utils.crypto import system_aes_decrypt
        private_key = system_aes_decrypt(config.md5_secret)
    except Exception:
        logger.exception("解密MD5密钥失败")
        return _build_error_response("JDO_500", "系统错误", params.get("jdOrderNo"))

    # 验证签名
    if not verify_jd_general_sign(params, private_key):
        logger.warning(f"京东通用交易签名验证失败，京东订单号: {params.get('jdOrderNo')}")
        return _build_error_response("JDO_304", "验证签名不正确", params.get("jdOrderNo"))

    jd_order_no = str(params.get("jdOrderNo", ""))

    # 防重处理 — 同一京东订单号不重复创建
    existing_order = Order.query.filter_by(jd_order_no=jd_order_no, biz_type=1).first()
    if existing_order:
        logger.info(f"京东订单 {jd_order_no} 已存在，返回当前状态")
        return _build_success_response(existing_order, private_key)

    # 创建新订单
    order_no = generate_order_no()
    try:
        new_order = Order(
            merchant_id=merchant_id,
            biz_type=1,
            order_no=order_no,
            jd_order_no=jd_order_no,
            order_status=3,  # 初始状态：生产中
            amount=int(params.get("totalPrice", 0)),
            quantity=int(params.get("quantity", 1)),
            ware_no=params.get("wareNo", ""),
            produce_account=params.get("produceAccount", ""),
            notify_url=params.get("notifyUrl", ""),
            pay_time=_parse_jd_time(params.get("payTime")),
        )
        db.session.add(new_order)
        db.session.commit()
        logger.info(f"创建通用交易订单成功：我方订单号={order_no}, 京东订单号={jd_order_no}")
    except Exception:
        db.session.rollback()
        logger.exception("创建订单失败")
        return _build_error_response("JDO_500", "系统错误", jd_order_no)

    return _build_success_response(new_order, private_key)


def handle_find_distill(params: dict, merchant_id: int) -> dict:
    """
    处理京东通用交易 — 生产反查请求
    业务流程：
        1. 验证签名
        2. 查询订单状态
        3. 返回当前生产状态
    参数：
        params      — 京东请求参数字典
        merchant_id — 商户ID
    返回：
        响应参数字典
    """
    # 查询商户配置
    config = MerchantJdConfig.query.filter_by(
        merchant_id=merchant_id, biz_type=1, is_enabled=1
    ).first()

    if not config or not config.md5_secret:
        return _build_error_response("JDO_500", "系统错误", params.get("jdOrderNo"))

    # 解密密钥
    try:
        from app.utils.crypto import system_aes_decrypt
        private_key = system_aes_decrypt(config.md5_secret)
    except Exception:
        logger.exception("解密MD5密钥失败")
        return _build_error_response("JDO_500", "系统错误", params.get("jdOrderNo"))

    # 验证签名
    if not verify_jd_general_sign(params, private_key):
        return _build_error_response("JDO_304", "验证签名不正确", params.get("jdOrderNo"))

    jd_order_no = str(params.get("jdOrderNo", ""))

    # 查询订单
    order = Order.query.filter_by(jd_order_no=jd_order_no, biz_type=1).first()
    if not order:
        return _build_error_response("JDO_302", "没有对应的商品", jd_order_no)

    return _build_success_response(order, private_key)


def send_callback_to_jd(order: Order, merchant_id: int):
    """
    异步回调通知京东 — 生产结果
    请求方向：我方 → 京东（POST 请求）
    地址：{notifyUrl}/produce/result
    参数：
        order       — 订单对象
        merchant_id — 商户ID
    """
    config = MerchantJdConfig.query.filter_by(
        merchant_id=merchant_id, biz_type=1, is_enabled=1
    ).first()
    if not config:
        logger.error(f"商户 {merchant_id} 配置不存在，无法回调")
        return

    try:
        from app.utils.crypto import system_aes_decrypt
        private_key = system_aes_decrypt(config.md5_secret)
    except Exception:
        logger.exception("解密MD5密钥失败，无法回调")
        return

    # 构建回调参数
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    callback_params = {
        "timestamp": timestamp,
        "vendorId": str(config.vendor_id),
        "jdOrderNo": order.jd_order_no,
        "agentOrderNo": order.order_no,
        "produceStatus": order.order_status,
        "quantity": order.quantity or 1,
    }

    # 如果有卡密信息，加密后附加
    if order.product_info and order.order_status == 1:
        try:
            aes_key = system_aes_decrypt(config.aes_secret)
            callback_params["product"] = aes_encrypt(order.product_info, aes_key)
        except Exception:
            logger.exception("加密卡密信息失败")

    # 计算签名
    callback_params["sign"] = jd_general_sign(callback_params, private_key)

    # 发送回调请求
    notify_url = order.notify_url
    if not notify_url:
        logger.error(f"订单 {order.order_no} 没有回调地址")
        return

    callback_url = f"{notify_url}/produce/result"

    # 记录回调日志
    callback_log = JdCallback(
        order_id=order.id,
        callback_type=1,
        callback_direction=2,  # 我方调京东
        request_params=json.dumps(
            {k: v for k, v in callback_params.items() if k != "product"},
            ensure_ascii=False
        ),
    )

    try:
        resp = requests.post(callback_url, data=callback_params, timeout=10)
        resp_data = resp.json()
        callback_log.result_code = str(resp_data.get("code", ""))
        callback_log.result_message = resp_data.get("message", "")
        callback_log.response_data = json.dumps(resp_data, ensure_ascii=False)
        logger.info(f"回调京东成功：订单={order.order_no}, 返回码={resp_data.get('code')}")
    except Exception:
        callback_log.result_code = "EXCEPTION"
        callback_log.result_message = "回调请求异常"
        callback_log.retry_count = (callback_log.retry_count or 0) + 1
        logger.exception(f"回调京东失败：订单={order.order_no}")

    db.session.add(callback_log)
    db.session.commit()


# ==============================
#  内部辅助函数
# ==============================

def _build_success_response(order: Order, private_key: str) -> dict:
    """
    构建通用交易成功响应
    参数：
        order       — 订单对象
        private_key — 签名私钥（明文）
    返回：
        包含签名的响应字典
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    resp = {
        "signType": "MD5",
        "timestamp": timestamp,
        "code": "JDO_200" if order.order_status == 1 else "JDO_201",
        "jdOrderNo": order.jd_order_no,
        "agentOrderNo": order.order_no,
        "produceStatus": order.order_status,
    }

    # 如果生产成功且有卡密，附加加密后的卡密信息
    if order.order_status == 1 and order.product_info:
        config = MerchantJdConfig.query.filter_by(
            merchant_id=order.merchant_id, biz_type=1
        ).first()
        if config and config.aes_secret:
            try:
                from app.utils.crypto import system_aes_decrypt
                aes_key = system_aes_decrypt(config.aes_secret)
                resp["product"] = aes_encrypt(order.product_info, aes_key)
            except Exception:
                logger.exception("加密卡密信息失败")

    # 计算签名
    resp["sign"] = jd_general_sign(resp, private_key)
    return resp


def _build_error_response(code: str, message: str, jd_order_no=None) -> dict:
    """
    构建通用交易错误响应
    参数：
        code         — 错误码
        message      — 错误信息
        jd_order_no  — 京东订单号（可选）
    返回：
        错误响应字典
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    resp = {
        "signType": "MD5",
        "timestamp": timestamp,
        "code": code,
        "produceStatus": 4 if code == "JDO_500" else 2,
    }
    if jd_order_no:
        resp["jdOrderNo"] = str(jd_order_no)
    return resp


def _parse_jd_time(time_str: str):
    """
    解析京东时间格式（yyyyMMddHHmmss）为 datetime 对象
    参数：
        time_str — 时间字符串，格式：yyyyMMddHHmmss
    返回：
        datetime 对象，解析失败返回 None
    """
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%Y%m%d%H%M%S")
    except ValueError:
        return None
