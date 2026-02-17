# -*- coding: utf-8 -*-
"""
==============================================
  阿奇索开放平台 — 路由控制器
  功能：
    1. /pull    — 拉取待发货订单
    2. /deliver — 自动发货
    3. /status  — 查询发货状态
    4. /stock   — 查询商品库存
  ⚠️ 可选模块：未配置时接口返回提示信息，不产生错误
==============================================
"""

import logging
from flask import Blueprint, request, jsonify

from app.services.agiso_service import (
    is_agiso_enabled,
    pull_orders,
    auto_deliver,
    query_delivery_status,
    query_stock,
)

# 创建蓝图
agiso_bp = Blueprint("agiso", __name__)

# 日志记录器
logger = logging.getLogger(__name__)

# 默认商户ID
DEFAULT_MERCHANT_ID = 1


@agiso_bp.route("/pull", methods=["POST"])
def pull():
    """
    拉取待发货订单
    接口说明：
        - 从阿奇索平台拉取待发货的京东订单列表
        - 未配置阿奇索时返回提示
    """
    merchant_id = request.form.get("merchant_id", DEFAULT_MERCHANT_ID, type=int)

    if not is_agiso_enabled(merchant_id):
        return jsonify({"success": False, "message": "阿奇索自动发货未配置或未启用"})

    result = pull_orders(merchant_id)
    return jsonify(result)


@agiso_bp.route("/deliver", methods=["POST"])
def deliver():
    """
    自动发货
    接口说明：
        - 向阿奇索平台提交发货信息
        - 未配置时不执行
    """
    merchant_id = request.form.get("merchant_id", DEFAULT_MERCHANT_ID, type=int)
    order_id = request.form.get("order_id", "")
    delivery_info = request.form.get("delivery_info", "{}")

    if not is_agiso_enabled(merchant_id):
        return jsonify({"success": False, "message": "阿奇索自动发货未配置或未启用"})

    import json
    try:
        info = json.loads(delivery_info)
    except Exception:
        return jsonify({"success": False, "message": "发货信息格式错误"})

    result = auto_deliver(merchant_id, order_id, info)
    return jsonify(result)


@agiso_bp.route("/status", methods=["POST"])
def status():
    """
    查询发货状态
    接口说明：
        - 查询阿奇索平台的发货结果
    """
    merchant_id = request.form.get("merchant_id", DEFAULT_MERCHANT_ID, type=int)
    order_id = request.form.get("order_id", "")

    if not is_agiso_enabled(merchant_id):
        return jsonify({"success": False, "message": "阿奇索自动发货未配置或未启用"})

    result = query_delivery_status(merchant_id, order_id)
    return jsonify(result)


@agiso_bp.route("/stock", methods=["POST"])
def stock():
    """
    查询商品库存
    接口说明：
        - 查询阿奇索平台可用商品库存
    """
    merchant_id = request.form.get("merchant_id", DEFAULT_MERCHANT_ID, type=int)
    product_id = request.form.get("product_id", "")

    if not is_agiso_enabled(merchant_id):
        return jsonify({"success": False, "message": "阿奇索自动发货未配置或未启用"})

    result = query_stock(merchant_id, product_id)
    return jsonify(result)
