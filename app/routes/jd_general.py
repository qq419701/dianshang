# -*- coding: utf-8 -*-
"""
==============================================
  京东通用交易平台 — 路由控制器
  功能：
    1. /beginDistill — 接收京东提交充值/提取卡密请求
    2. /findDistill  — 接收京东生产反查请求
  请求方向：京东 → 我方
  请求方式：HTTP POST, Content-Type: application/x-www-form-urlencoded
==============================================
"""

import logging
from flask import Blueprint, request, jsonify

from app.services.jd_general_service import handle_begin_distill, handle_find_distill

# 创建蓝图
jd_general_bp = Blueprint("jd_general", __name__)

# 日志记录器
logger = logging.getLogger(__name__)

# 默认商户ID（实际应从请求中获取或通过 vendorId 映射）
DEFAULT_MERCHANT_ID = 1


@jd_general_bp.route("/beginDistill", methods=["POST"])
def begin_distill():
    """
    提交充值 & 提取卡密接口
    接口说明：
        - 京东支付完成后调用此接口，提交充值或卡密提取请求
        - 必须做防重处理（同一 jdOrderNo 不重复创建）
        - 同步生产 tp999 ≤ 600ms
    请求参数：
        sign, signType, timestamp, jdOrderNo, payTime,
        notifyUrl, produceAccount, quantity, wareNo,
        totalPrice, vendorId, expand
    返回：
        sign, signType, timestamp, code, jdOrderNo,
        agentOrderNo, produceStatus, product
    """
    # 获取 POST 表单参数
    params = request.form.to_dict()
    logger.info(f"[通用交易] 收到 beginDistill 请求，京东订单号: {params.get('jdOrderNo')}")

    # 通过 vendorId 确定商户（简化处理：使用默认商户）
    merchant_id = DEFAULT_MERCHANT_ID

    # 调用业务服务处理
    result = handle_begin_distill(params, merchant_id)

    return jsonify(result)


@jd_general_bp.route("/findDistill", methods=["POST"])
def find_distill():
    """
    生产反查接口
    接口说明：
        - 京东未收到生产结果时，主动调用此接口反查订单状态
        - 返回生产中（produceStatus=3）时，京东会继续反查
        - 超过反查次数后，仅依赖我方回调
    请求参数：
        sign, signType, timestamp, jdOrderNo
    返回：
        sign, signType, timestamp, code, jdOrderNo,
        agentOrderNo, produceStatus, product
    """
    params = request.form.to_dict()
    logger.info(f"[通用交易] 收到 findDistill 请求，京东订单号: {params.get('jdOrderNo')}")

    merchant_id = DEFAULT_MERCHANT_ID

    result = handle_find_distill(params, merchant_id)

    return jsonify(result)
