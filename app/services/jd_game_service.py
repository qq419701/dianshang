# -*- coding: utf-8 -*-
"""
==============================================
  京东游戏点卡平台 — 业务服务层
  功能：
    1. 提单校验（检查商品是否可售）
    2. 直充接单（接收直充订单）
    3. 直充订单查询（查询直充状态）
    4. 卡密接单（接收卡密订单）
    5. 卡密订单查询（查询卡密状态）
    6. 直充回调（通知京东充值结果）
    7. 卡密回调（通知京东卡密结果）
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
from app.utils.sign import jd_game_sign, verify_jd_game_sign
from app.utils.crypto import (
    base64_encode_utf8, base64_decode_utf8,
    base64_encode_gbk, base64_decode_gbk,
)

# 日志记录器
logger = logging.getLogger(__name__)


def generate_game_order_no():
    """
    生成游戏点卡唯一订单号
    格式：GC + 年月日时分秒 + 8位随机字符
    返回：唯一订单号字符串
    """
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"GC{now}{short_uuid}"


def handle_pre_check(params: dict, merchant_id: int) -> dict:
    """
    处理提单校验请求
    京东在用户提交订单前调用此接口，校验商品是否可售
    参数：
        params      — 京东请求参数字典（含 customerId, data, timestamp, sign）
        merchant_id — 商户ID
    返回：
        响应字典 {"retCode": "100", "retMessage": "成功", "data": "..."}
    """
    # 获取商户配置
    config = _get_config(merchant_id)
    if not config:
        return {"retCode": "999", "retMessage": "系统错误：商户配置不存在"}

    # 验证签名
    if not _verify_sign(params, config):
        return {"retCode": "106", "retMessage": "验证摘要串验证失败"}

    # 解码业务数据
    try:
        biz_data = json.loads(base64_decode_utf8(params.get("data", "")))
    except Exception:
        return {"retCode": "104", "retMessage": "传入的参数有误"}

    logger.info(f"提单校验请求：SKU={biz_data.get('skuId')}, 数量={biz_data.get('buyNum')}")

    # 默认返回可售（实际业务需根据库存等判断）
    result_data = json.dumps({"status": "0"})
    return {
        "retCode": "100",
        "retMessage": "成功",
        "data": base64_encode_utf8(result_data),
    }


def handle_direct_charge(params: dict, merchant_id: int) -> dict:
    """
    处理直充接单请求
    京东用户支付完成后调用此接口，提交直充订单
    参数：
        params      — 京东请求参数字典
        merchant_id — 商户ID
    返回：
        响应字典
    """
    config = _get_config(merchant_id)
    if not config:
        return {"retCode": "999", "retMessage": "系统错误：商户配置不存在"}

    if not _verify_sign(params, config):
        return {"retCode": "106", "retMessage": "验证摘要串验证失败"}

    try:
        biz_data = json.loads(base64_decode_utf8(params.get("data", "")))
    except Exception:
        return {"retCode": "104", "retMessage": "传入的参数有误"}

    jd_order_id = str(biz_data.get("orderId", ""))

    # 防重处理
    existing = Order.query.filter_by(jd_order_no=jd_order_id, biz_type=2).first()
    if existing:
        return {"retCode": "102", "retMessage": "订单号不允许重复"}

    # 创建订单
    order_no = generate_game_order_no()
    try:
        new_order = Order(
            merchant_id=merchant_id,
            biz_type=2,
            order_no=order_no,
            jd_order_no=jd_order_id,
            order_status=1,  # 充值中
            amount=int(float(biz_data.get("totalPrice", 0)) * 100),  # 转为分
            quantity=int(biz_data.get("buyNum", 1)),
            sku_id=str(biz_data.get("skuId", "")),
            produce_account=biz_data.get("gameAccount", ""),
        )
        db.session.add(new_order)
        db.session.commit()
        logger.info(f"创建直充订单成功：我方订单号={order_no}, 京东订单号={jd_order_id}")
    except Exception:
        db.session.rollback()
        logger.exception("创建直充订单失败")
        return {"retCode": "999", "retMessage": "系统错误"}

    return {"retCode": "100", "retMessage": "成功"}


def handle_direct_query(params: dict, merchant_id: int) -> dict:
    """
    处理直充订单查询请求
    京东查询直充订单的充值状态
    参数：
        params      — 京东请求参数字典
        merchant_id — 商户ID
    返回：
        响应字典（含 orderStatus）
    """
    config = _get_config(merchant_id)
    if not config:
        return {"retCode": "999", "retMessage": "系统错误：商户配置不存在"}

    if not _verify_sign(params, config):
        return {"retCode": "106", "retMessage": "验证摘要串验证失败"}

    try:
        biz_data = json.loads(base64_decode_utf8(params.get("data", "")))
    except Exception:
        return {"retCode": "104", "retMessage": "传入的参数有误"}

    jd_order_id = str(biz_data.get("orderId", ""))
    order = Order.query.filter_by(jd_order_no=jd_order_id, biz_type=2).first()

    if not order:
        return {"retCode": "101", "retMessage": "订单不存在"}

    # orderStatus: 0=充值成功, 1=充值中
    order_status = 0 if order.order_status == 0 else 1
    result_data = json.dumps({"orderStatus": order_status})

    return {
        "retCode": "100",
        "retMessage": "查询成功",
        "data": base64_encode_utf8(result_data),
    }


def handle_card_order(params: dict, merchant_id: int) -> dict:
    """
    处理卡密接单请求
    京东用户支付完成后调用此接口，提交卡密订单
    参数：
        params      — 京东请求参数字典
        merchant_id — 商户ID
    返回：
        响应字典（成功时含卡密信息）
    """
    config = _get_config(merchant_id)
    if not config:
        return {"retCode": "999", "retMessage": "系统错误：商户配置不存在"}

    if not _verify_sign(params, config):
        return {"retCode": "106", "retMessage": "验证摘要串验证失败"}

    try:
        biz_data = json.loads(base64_decode_utf8(params.get("data", "")))
    except Exception:
        return {"retCode": "104", "retMessage": "传入的参数有误"}

    jd_order_id = str(biz_data.get("orderId", ""))

    # 防重处理
    existing = Order.query.filter_by(jd_order_no=jd_order_id, biz_type=2).first()
    if existing:
        return {"retCode": "102", "retMessage": "订单号不允许重复"}

    # 创建卡密订单
    order_no = generate_game_order_no()
    try:
        new_order = Order(
            merchant_id=merchant_id,
            biz_type=2,
            order_no=order_no,
            jd_order_no=jd_order_id,
            order_status=1,  # 处理中
            amount=int(float(biz_data.get("totalPrice", 0)) * 100),
            quantity=int(biz_data.get("buyNum", 1)),
            sku_id=str(biz_data.get("skuId", "")),
        )
        db.session.add(new_order)
        db.session.commit()
        logger.info(f"创建卡密订单成功：我方订单号={order_no}, 京东订单号={jd_order_id}")
    except Exception:
        db.session.rollback()
        logger.exception("创建卡密订单失败")
        return {"retCode": "999", "retMessage": "系统错误"}

    return {"retCode": "100", "retMessage": "成功"}


def handle_card_query(params: dict, merchant_id: int) -> dict:
    """
    处理卡密订单查询请求
    京东查询卡密订单的状态和卡密信息
    参数：
        params      — 京东请求参数字典
        merchant_id — 商户ID
    返回：
        响应字典（含 orderStatus 和 cardinfos）
    """
    config = _get_config(merchant_id)
    if not config:
        return {"retCode": "999", "retMessage": "系统错误：商户配置不存在"}

    if not _verify_sign(params, config):
        return {"retCode": "106", "retMessage": "验证摘要串验证失败"}

    try:
        biz_data = json.loads(base64_decode_utf8(params.get("data", "")))
    except Exception:
        return {"retCode": "104", "retMessage": "传入的参数有误"}

    jd_order_id = str(biz_data.get("orderId", ""))
    order = Order.query.filter_by(jd_order_no=jd_order_id, biz_type=2).first()

    if not order:
        return {"retCode": "101", "retMessage": "订单不存在"}

    # 构建返回数据
    result = {"orderStatus": "0" if order.order_status == 0 else "1"}

    # 如果订单已完成且有卡密信息
    if order.order_status == 0 and order.product_info:
        try:
            from app.utils.crypto import system_aes_decrypt
            card_info_json = system_aes_decrypt(order.product_info)
            result["cardinfos"] = json.loads(card_info_json)
        except Exception:
            logger.exception("解密卡密信息失败")

    result_data = json.dumps(result, ensure_ascii=False)
    return {
        "retCode": "100",
        "retMessage": "充值成功" if order.order_status == 0 else "充值中",
        "data": base64_encode_utf8(result_data),
    }


def send_direct_callback(order: Order, merchant_id: int):
    """
    直充回调 — 通知京东直充结果
    请求方向：我方 → 京东
    ⚠️ 回调的 data 字段需使用 GBK 编码后 Base64
    参数：
        order       — 订单对象
        merchant_id — 商户ID
    """
    config = _get_config(merchant_id)
    if not config:
        logger.error(f"商户 {merchant_id} 配置不存在，无法发送直充回调")
        return

    callback_url = config.jd_direct_callback_url
    if not callback_url:
        logger.error(f"商户 {merchant_id} 未配置直充回调地址")
        return

    # 构建业务数据（⚠️ 需 GBK 编码后 Base64）
    biz_data = {
        "orderId": int(order.jd_order_no),
        "orderStatus": 0 if order.order_status == 0 else 2,  # 0=成功, 其他=失败
    }

    # 失败时附加失败原因
    if order.order_status != 0:
        biz_data["failedCode"] = 1
        biz_data["failedReason"] = order.remark or "充值失败"

    data_str = json.dumps(biz_data, ensure_ascii=False)
    encoded_data = base64_encode_gbk(data_str)

    # 获取签名密钥
    try:
        from app.utils.crypto import system_aes_decrypt
        private_key = system_aes_decrypt(config.md5_secret)
    except Exception:
        logger.exception("解密签名密钥失败")
        return

    # 构建请求参数
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    request_params = {
        "customerId": str(config.customer_id),
        "data": encoded_data,
        "timestamp": timestamp,
    }
    request_params["sign"] = jd_game_sign(request_params, private_key)

    # 记录回调日志
    callback_log = JdCallback(
        order_id=order.id,
        callback_type=2,  # 直充回调
        callback_direction=2,  # 我方调京东
        request_params=json.dumps({"orderId": order.jd_order_no}, ensure_ascii=False),
    )

    try:
        resp = requests.post(callback_url, data=request_params, timeout=10)
        resp_data = resp.json()
        callback_log.result_code = resp_data.get("retCode", "")
        callback_log.result_message = resp_data.get("retMessage", "")
        callback_log.response_data = json.dumps(resp_data, ensure_ascii=False)
        logger.info(f"直充回调成功：订单={order.order_no}, 返回码={resp_data.get('retCode')}")
    except Exception:
        callback_log.result_code = "EXCEPTION"
        callback_log.result_message = "回调请求异常"
        logger.exception(f"直充回调失败：订单={order.order_no}")

    db.session.add(callback_log)
    db.session.commit()


def send_card_callback(order: Order, merchant_id: int):
    """
    卡密回调 — 通知京东卡密结果
    请求方向：我方 → 京东
    ⚠️ 回调的 data 字段需使用 GBK 编码后 Base64
    参数：
        order       — 订单对象
        merchant_id — 商户ID
    """
    config = _get_config(merchant_id)
    if not config:
        logger.error(f"商户 {merchant_id} 配置不存在，无法发送卡密回调")
        return

    callback_url = config.jd_card_callback_url
    if not callback_url:
        logger.error(f"商户 {merchant_id} 未配置卡密回调地址")
        return

    # 构建业务数据
    biz_data = {
        "orderId": int(order.jd_order_no),
        "orderStatus": 0 if order.order_status == 0 else 2,
    }

    # 成功时附加卡密信息
    if order.order_status == 0 and order.product_info:
        try:
            from app.utils.crypto import system_aes_decrypt
            card_info_json = system_aes_decrypt(order.product_info)
            biz_data["cardinfos"] = json.loads(card_info_json)
        except Exception:
            logger.exception("解密卡密信息失败")

    # 失败时附加失败原因
    if order.order_status != 0:
        biz_data["failedCode"] = 1
        biz_data["failedReason"] = order.remark or "充值失败"

    # ⚠️ GBK 编码后 Base64
    data_str = json.dumps(biz_data, ensure_ascii=False)
    encoded_data = base64_encode_gbk(data_str)

    # 获取签名密钥
    try:
        from app.utils.crypto import system_aes_decrypt
        private_key = system_aes_decrypt(config.md5_secret)
    except Exception:
        logger.exception("解密签名密钥失败")
        return

    # 构建请求参数
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    request_params = {
        "customerId": str(config.customer_id),
        "data": encoded_data,
        "timestamp": timestamp,
    }
    request_params["sign"] = jd_game_sign(request_params, private_key)

    # 记录回调日志
    callback_log = JdCallback(
        order_id=order.id,
        callback_type=3,  # 卡密回调
        callback_direction=2,  # 我方调京东
        request_params=json.dumps({"orderId": order.jd_order_no}, ensure_ascii=False),
    )

    try:
        resp = requests.post(callback_url, data=request_params, timeout=10)
        resp_data = resp.json()
        callback_log.result_code = resp_data.get("retCode", "")
        callback_log.result_message = resp_data.get("retMessage", "")
        callback_log.response_data = json.dumps(resp_data, ensure_ascii=False)
        logger.info(f"卡密回调成功：订单={order.order_no}, 返回码={resp_data.get('retCode')}")
    except Exception:
        callback_log.result_code = "EXCEPTION"
        callback_log.result_message = "回调请求异常"
        logger.exception(f"卡密回调失败：订单={order.order_no}")

    db.session.add(callback_log)
    db.session.commit()


# ==============================
#  内部辅助函数
# ==============================

def _get_config(merchant_id: int):
    """
    获取商户游戏点卡配置
    参数：
        merchant_id — 商户ID
    返回：
        MerchantJdConfig 对象或 None
    """
    return MerchantJdConfig.query.filter_by(
        merchant_id=merchant_id, biz_type=2, is_enabled=1
    ).first()


def _verify_sign(params: dict, config: MerchantJdConfig) -> bool:
    """
    验证京东游戏点卡平台签名
    参数：
        params — 请求参数字典
        config — 商户配置对象
    返回：
        True=签名匹配，False=签名不匹配
    """
    if not config.md5_secret:
        return False
    try:
        from app.utils.crypto import system_aes_decrypt
        private_key = system_aes_decrypt(config.md5_secret)
    except Exception:
        logger.exception("解密签名密钥失败")
        return False

    return verify_jd_game_sign(params, private_key)
