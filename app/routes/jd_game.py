# -*- coding: utf-8 -*-
"""
==============================================
  京东游戏点卡平台 — 路由控制器
  功能：
    1. /preCheck     — 提单校验接口（商品是否可售）
    2. /directCharge — 直充接单接口
    3. /directQuery  — 直充订单查询接口
    4. /cardOrder    — 卡密接单接口
    5. /cardQuery    — 卡密订单查询接口
  请求方向：京东 → 我方
  请求方式：HTTP POST
  公共参数：customerId, data, timestamp, sign, version
==============================================
"""

import logging
from flask import Blueprint, request, jsonify

from app.services.jd_game_service import (
    handle_pre_check,
    handle_direct_charge,
    handle_direct_query,
    handle_card_order,
    handle_card_query,
)

# 创建蓝图
jd_game_bp = Blueprint("jd_game", __name__)

# 日志记录器
logger = logging.getLogger(__name__)

# 默认商户ID
DEFAULT_MERCHANT_ID = 1


@jd_game_bp.route("/preCheck", methods=["POST"])
def pre_check():
    """
    提单校验接口
    接口说明：
        - 京东提单前调用，校验商品是否可售
        - 性能要求：平均 ≤ 200ms，最长 ≤ 400ms
    请求参数：
        customerId, data(Base64编码的JSON), timestamp, sign
    返回：
        retCode, retMessage, data(Base64编码的JSON)
    """
    params = request.form.to_dict()
    logger.info(f"[游戏点卡] 收到提单校验请求")

    merchant_id = DEFAULT_MERCHANT_ID
    result = handle_pre_check(params, merchant_id)

    return jsonify(result)


@jd_game_bp.route("/directCharge", methods=["POST"])
def direct_charge():
    """
    直充接单接口
    接口说明：
        - 接收京东直充订单（话费、Q币等直接充值类）
        - 性能要求：tp99 ≤ 1000ms
    请求参数：
        customerId, data(Base64编码的JSON), timestamp, sign
    返回：
        retCode, retMessage
    """
    params = request.form.to_dict()
    logger.info(f"[游戏点卡] 收到直充接单请求")

    merchant_id = DEFAULT_MERCHANT_ID
    result = handle_direct_charge(params, merchant_id)

    return jsonify(result)


@jd_game_bp.route("/directQuery", methods=["POST"])
def direct_query():
    """
    直充订单查询接口
    接口说明：
        - 查询直充订单的充值状态
        - 性能要求：tp99 ≤ 1000ms
    请求参数：
        customerId, data(Base64编码的JSON包含orderId), timestamp, sign
    返回：
        retCode, retMessage, data(Base64编码的JSON包含orderStatus)
    """
    params = request.form.to_dict()
    logger.info(f"[游戏点卡] 收到直充查询请求")

    merchant_id = DEFAULT_MERCHANT_ID
    result = handle_direct_query(params, merchant_id)

    return jsonify(result)


@jd_game_bp.route("/cardOrder", methods=["POST"])
def card_order():
    """
    卡密接单接口
    接口说明：
        - 接收京东卡密订单（游戏点卡、充值卡等）
        - 性能要求：tp99 ≤ 1000ms
    请求参数：
        customerId, data(Base64编码的JSON), timestamp, sign
    返回：
        retCode, retMessage, data(含cardinfos的Base64)
    """
    params = request.form.to_dict()
    logger.info(f"[游戏点卡] 收到卡密接单请求")

    merchant_id = DEFAULT_MERCHANT_ID
    result = handle_card_order(params, merchant_id)

    return jsonify(result)


@jd_game_bp.route("/cardQuery", methods=["POST"])
def card_query():
    """
    卡密订单查询接口
    接口说明：
        - 查询卡密订单的状态和卡密信息
        - 性能要求：tp99 ≤ 1000ms
    请求参数：
        customerId, data(Base64编码的JSON包含orderId), timestamp, sign
    返回：
        retCode, retMessage, data(含orderStatus和cardinfos的Base64)
    """
    params = request.form.to_dict()
    logger.info(f"[游戏点卡] 收到卡密查询请求")

    merchant_id = DEFAULT_MERCHANT_ID
    result = handle_card_query(params, merchant_id)

    return jsonify(result)
