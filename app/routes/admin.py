# -*- coding: utf-8 -*-
"""
==============================================
  后台管理 — 路由控制器
  功能：
    1. 管理首页（仪表盘）
    2. 订单管理（查看/搜索订单）
    3. 商户配置管理（京东通用交易/游戏点卡/阿奇索）
    4. 回调日志查看
    5. 接口地址生成（输入店铺ID自动生成接口地址）
  所有页面均为中文界面
==============================================
"""

import json
import logging
from flask import Blueprint, request, render_template, jsonify, redirect, url_for

from app import db
from app.models.order import Order
from app.models.merchant_config import MerchantJdConfig, AgisoConfig
from app.models.callback_log import JdCallback, AgisoLog
from app.utils.crypto import system_aes_encrypt
from app.services.agiso_service import is_agiso_enabled

# 创建蓝图
admin_bp = Blueprint("admin", __name__)

# 日志记录器
logger = logging.getLogger(__name__)


@admin_bp.route("/")
def dashboard():
    """
    管理后台首页 — 仪表盘
    展示：
        - 今日订单统计
        - 各状态订单数量
        - 最近订单列表
    """
    from datetime import datetime, timedelta

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # 统计数据
    total_orders = Order.query.count()
    today_orders = Order.query.filter(Order.create_time >= today).count()
    success_orders = Order.query.filter_by(order_status=1).count()
    pending_orders = Order.query.filter_by(order_status=3).count()

    # 最近10条订单
    recent_orders = Order.query.order_by(Order.create_time.desc()).limit(10).all()

    return render_template(
        "dashboard.html",
        total_orders=total_orders,
        today_orders=today_orders,
        success_orders=success_orders,
        pending_orders=pending_orders,
        recent_orders=recent_orders,
    )


@admin_bp.route("/orders")
def order_list():
    """
    订单管理 — 订单列表页
    支持：
        - 按京东订单号搜索
        - 按业务类型筛选（通用交易/游戏点卡）
        - 按订单状态筛选
        - 分页浏览
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    biz_type = request.args.get("biz_type", 0, type=int)
    status = request.args.get("status", -1, type=int)

    query = Order.query

    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                Order.jd_order_no.like(f"%{search}%"),
                Order.order_no.like(f"%{search}%"),
            )
        )
    if biz_type > 0:
        query = query.filter_by(biz_type=biz_type)
    if status >= 0:
        query = query.filter_by(order_status=status)

    # 分页查询
    pagination = query.order_by(Order.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "orders.html",
        orders=pagination.items,
        pagination=pagination,
        search=search,
        biz_type=biz_type,
        status=status,
    )


@admin_bp.route("/config")
def config_page():
    """
    商户配置管理页
    展示：
        - 京东通用交易配置
        - 京东游戏点卡配置
        - 阿奇索开放平台配置
        - 接口地址预览
    """
    # 获取商户配置（默认商户ID=1）
    merchant_id = request.args.get("merchant_id", 1, type=int)

    general_config = MerchantJdConfig.query.filter_by(
        merchant_id=merchant_id, biz_type=1
    ).first()
    game_config = MerchantJdConfig.query.filter_by(
        merchant_id=merchant_id, biz_type=2
    ).first()
    agiso_config = AgisoConfig.query.filter_by(merchant_id=merchant_id).first()

    return render_template(
        "config.html",
        merchant_id=merchant_id,
        general_config=general_config,
        game_config=game_config,
        agiso_config=agiso_config,
    )


@admin_bp.route("/config/save", methods=["POST"])
def save_config():
    """
    保存商户配置
    接收前端表单提交的配置数据并保存到数据库
    敏感字段（密钥）使用系统AES加密存储
    """
    merchant_id = request.form.get("merchant_id", 1, type=int)
    config_type = request.form.get("config_type", "")

    try:
        if config_type == "general":
            # 保存通用交易配置
            config = MerchantJdConfig.query.filter_by(
                merchant_id=merchant_id, biz_type=1
            ).first()
            if not config:
                config = MerchantJdConfig(merchant_id=merchant_id, biz_type=1)
                db.session.add(config)

            config.vendor_id = request.form.get("vendor_id", type=int)
            config.our_api_url = request.form.get("our_api_url", "")
            config.jd_callback_url = request.form.get("jd_callback_url", "")

            # 密钥使用系统AES加密存储
            md5_secret = request.form.get("md5_secret", "")
            if md5_secret and md5_secret != "******":
                config.md5_secret = system_aes_encrypt(md5_secret)
            aes_secret = request.form.get("aes_secret", "")
            if aes_secret and aes_secret != "******":
                config.aes_secret = system_aes_encrypt(aes_secret)

            config.is_enabled = 1 if request.form.get("is_enabled") else 0

        elif config_type == "game":
            # 保存游戏点卡配置
            config = MerchantJdConfig.query.filter_by(
                merchant_id=merchant_id, biz_type=2
            ).first()
            if not config:
                config = MerchantJdConfig(merchant_id=merchant_id, biz_type=2)
                db.session.add(config)

            config.customer_id = request.form.get("customer_id", type=int)
            config.our_api_url = request.form.get("our_api_url", "")
            config.jd_direct_callback_url = request.form.get("jd_direct_callback_url", "")
            config.jd_card_callback_url = request.form.get("jd_card_callback_url", "")

            md5_secret = request.form.get("md5_secret", "")
            if md5_secret and md5_secret != "******":
                config.md5_secret = system_aes_encrypt(md5_secret)

            config.is_enabled = 1 if request.form.get("is_enabled") else 0

        elif config_type == "agiso":
            # 保存阿奇索配置
            config = AgisoConfig.query.filter_by(merchant_id=merchant_id).first()
            if not config:
                config = AgisoConfig(merchant_id=merchant_id)
                db.session.add(config)

            config.host = request.form.get("host", "")
            config.port = request.form.get("port", type=int)
            config.app_id = request.form.get("app_id", "")
            config.general_trade_route = request.form.get("general_trade_route", "")
            config.game_card_route = request.form.get("game_card_route", "")

            app_secret = request.form.get("app_secret", "")
            if app_secret and app_secret != "******":
                config.app_secret = system_aes_encrypt(app_secret)
            access_token = request.form.get("access_token", "")
            if access_token and access_token != "******":
                config.access_token = system_aes_encrypt(access_token)

            config.is_enabled = 1 if request.form.get("is_enabled") else 0

        db.session.commit()
        logger.info(f"保存商户 {merchant_id} 的 {config_type} 配置成功")
        return jsonify({"success": True, "message": "配置保存成功"})

    except Exception:
        db.session.rollback()
        logger.exception("保存配置失败")
        return jsonify({"success": False, "message": "保存配置失败"})


@admin_bp.route("/generate-urls", methods=["POST"])
def generate_urls():
    """
    生成接口地址
    输入域名，自动生成所有需要提交给京东的接口地址
    """
    domain = request.form.get("domain", "").strip().rstrip("/")
    if not domain:
        return jsonify({"success": False, "message": "请输入域名"})

    urls = {
        "general": {
            "提交充值|提取卡密请求地址": f"{domain}/api/jd/general/beginDistill",
            "反查充值|提取接口地址": f"{domain}/api/jd/general/findDistill",
        },
        "game": {
            "直充接单接口地址": f"{domain}/api/jd/game/directCharge",
            "直充查询接口地址": f"{domain}/api/jd/game/directQuery",
            "卡券接单接口地址": f"{domain}/api/jd/game/cardOrder",
            "卡券查询接口地址": f"{domain}/api/jd/game/cardQuery",
            "提单校验接口地址": f"{domain}/api/jd/game/preCheck",
        },
    }

    return jsonify({"success": True, "data": urls})


@admin_bp.route("/callbacks")
def callback_list():
    """
    回调日志 — 查看所有回调记录
    支持：
        - 按回调类型筛选
        - 按时间范围筛选
        - 分页浏览
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    callback_type = request.args.get("type", 0, type=int)

    query = JdCallback.query
    if callback_type > 0:
        query = query.filter_by(callback_type=callback_type)

    pagination = query.order_by(JdCallback.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "callbacks.html",
        callbacks=pagination.items,
        pagination=pagination,
        callback_type=callback_type,
    )
