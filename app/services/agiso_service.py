# -*- coding: utf-8 -*-
"""
==============================================
  阿奇索开放平台 — 业务服务层
  功能：
    1. 订单拉取（从阿奇索拉取待发货的京东订单列表）
    2. 自动发货（提交发货信息）
    3. 发货状态查询
    4. 商品库存查询
  ⚠️ 此模块为可选模块，未配置时不加载不执行不报错
==============================================
"""

import json
import logging

import requests

from app import db
from app.models.merchant_config import AgisoConfig
from app.models.callback_log import AgisoLog
from app.utils.sign import agiso_sign

# 日志记录器
logger = logging.getLogger(__name__)


def is_agiso_enabled(merchant_id: int) -> bool:
    """
    检查商户是否启用了阿奇索自动发货
    规则：未配置不执行、不报错、按钮隐藏
    参数：
        merchant_id — 商户ID
    返回：
        True=已启用，False=未启用
    """
    config = AgisoConfig.query.filter_by(
        merchant_id=merchant_id, is_enabled=1
    ).first()
    return config is not None


def pull_orders(merchant_id: int) -> dict:
    """
    从阿奇索平台拉取待发货订单
    请求方向：我方 → 阿奇索
    参数：
        merchant_id — 商户ID
    返回：
        {"success": True/False, "data": [...], "message": "..."}
    """
    config = _get_config(merchant_id)
    if not config:
        return {"success": False, "message": "阿奇索配置不存在或未启用", "data": []}

    # 构建请求参数
    params = {
        "appId": config.app_id,
        "method": "order.pull",
        "timestamp": _get_timestamp(),
    }

    return _send_request(config, params, "订单拉取")


def auto_deliver(merchant_id: int, order_id: str, delivery_info: dict) -> dict:
    """
    向阿奇索平台提交发货信息
    请求方向：我方 → 阿奇索
    参数：
        merchant_id   — 商户ID
        order_id      — 订单ID
        delivery_info — 发货信息（卡密/充值结果等）
    返回：
        {"success": True/False, "message": "..."}
    """
    config = _get_config(merchant_id)
    if not config:
        return {"success": False, "message": "阿奇索配置不存在或未启用"}

    params = {
        "appId": config.app_id,
        "method": "order.deliver",
        "orderId": order_id,
        "deliveryInfo": json.dumps(delivery_info, ensure_ascii=False),
        "timestamp": _get_timestamp(),
    }

    return _send_request(config, params, "自动发货")


def query_delivery_status(merchant_id: int, order_id: str) -> dict:
    """
    查询阿奇索平台发货状态
    请求方向：我方 → 阿奇索
    参数：
        merchant_id — 商户ID
        order_id    — 订单ID
    返回：
        {"success": True/False, "data": {...}, "message": "..."}
    """
    config = _get_config(merchant_id)
    if not config:
        return {"success": False, "message": "阿奇索配置不存在或未启用"}

    params = {
        "appId": config.app_id,
        "method": "order.status",
        "orderId": order_id,
        "timestamp": _get_timestamp(),
    }

    return _send_request(config, params, "发货状态查询")


def query_stock(merchant_id: int, product_id: str = "") -> dict:
    """
    查询阿奇索平台商品库存
    请求方向：我方 → 阿奇索
    参数：
        merchant_id — 商户ID
        product_id  — 商品ID（可选）
    返回：
        {"success": True/False, "data": [...], "message": "..."}
    """
    config = _get_config(merchant_id)
    if not config:
        return {"success": False, "message": "阿奇索配置不存在或未启用"}

    params = {
        "appId": config.app_id,
        "method": "stock.query",
        "timestamp": _get_timestamp(),
    }
    if product_id:
        params["productId"] = product_id

    return _send_request(config, params, "库存查询")


# ==============================
#  内部辅助函数
# ==============================

def _get_config(merchant_id: int):
    """
    获取商户阿奇索配置（启用状态）
    参数：
        merchant_id — 商户ID
    返回：
        AgisoConfig 对象或 None
    """
    return AgisoConfig.query.filter_by(
        merchant_id=merchant_id, is_enabled=1
    ).first()


def _get_timestamp() -> str:
    """获取当前时间戳字符串"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _send_request(config: AgisoConfig, params: dict, api_name: str) -> dict:
    """
    发送请求到阿奇索平台
    参数：
        config   — 阿奇索配置对象
        params   — 请求参数字典
        api_name — 接口名称（用于日志记录）
    返回：
        统一格式的结果字典
    """
    # 解密应用密钥
    try:
        from app.utils.crypto import system_aes_decrypt
        app_secret = system_aes_decrypt(config.app_secret)
        access_token = system_aes_decrypt(config.access_token) if config.access_token else ""
    except Exception:
        logger.exception("解密阿奇索密钥失败")
        return {"success": False, "message": "解密配置失败"}

    # 计算签名
    params["sign"] = agiso_sign(params, app_secret)

    # 构建请求URL
    base_url = config.host or "https://open.agiso.com"
    if config.port:
        base_url = f"{base_url}:{config.port}"

    # 设置请求头
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {access_token}",
        "ApiVersion": "1",
    }

    # 记录日志
    agiso_log = AgisoLog(
        merchant_id=config.merchant_id,
        api_name=api_name,
        request_data=json.dumps(
            {k: v for k, v in params.items() if k != "sign"},
            ensure_ascii=False,
        ),
    )

    try:
        resp = requests.post(base_url, data=params, headers=headers, timeout=15)
        resp_data = resp.json()
        agiso_log.result_code = str(resp_data.get("code", ""))
        agiso_log.result_message = resp_data.get("message", "")
        agiso_log.response_data = json.dumps(resp_data, ensure_ascii=False)

        logger.info(f"阿奇索{api_name}成功：商户={config.merchant_id}")
        result = {"success": True, "data": resp_data.get("data", []), "message": "成功"}
    except Exception:
        agiso_log.result_code = "EXCEPTION"
        agiso_log.result_message = "请求异常"
        logger.exception(f"阿奇索{api_name}失败：商户={config.merchant_id}")
        result = {"success": False, "message": "请求阿奇索平台失败"}

    db.session.add(agiso_log)
    db.session.commit()

    return result
