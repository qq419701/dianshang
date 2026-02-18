# -*- coding: utf-8 -*-
"""
==============================================
  通知管理路由
  功能：通知列表、配置管理、标记已读
==============================================
"""

import logging
from flask import Blueprint, request, render_template, jsonify
from app import db
from app.models.notification import Notification, NotificationConfig
from app.utils.auth_decorator import login_required, permission_required
from app.services.auth_service import get_current_user

# 创建蓝图
notification_bp = Blueprint("notification", __name__)

# 日志记录器
logger = logging.getLogger(__name__)


@notification_bp.route("/")
@login_required
def notification_list():
    """
    通知列表页（当前用户的站内消息）
    """
    user = get_current_user()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    is_read = request.args.get("is_read", -1, type=int)
    
    query = Notification.query.filter_by(user_id=user.id)
    
    # 筛选条件
    if is_read >= 0:
        query = query.filter_by(is_read=is_read)
    
    # 分页查询
    pagination = query.order_by(Notification.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        "notification/list.html",
        notifications=pagination.items,
        pagination=pagination,
        is_read=is_read
    )


@notification_bp.route("/mark-read", methods=["POST"])
@login_required
def mark_as_read():
    """
    标记消息为已读
    """
    try:
        notification_id = request.form.get("notification_id", type=int)
        user = get_current_user()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user.id
        ).first()
        
        if not notification:
            return jsonify({"success": False, "message": "消息不存在"})
        
        notification.mark_as_read()
        db.session.commit()
        
        return jsonify({"success": True, "message": "已标记为已读"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("标记已读失败")
        return jsonify({"success": False, "message": "操作失败"})


@notification_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    """
    标记所有消息为已读
    """
    try:
        user = get_current_user()
        
        notifications = Notification.query.filter_by(
            user_id=user.id,
            is_read=0
        ).all()
        
        for notification in notifications:
            notification.mark_as_read()
        
        db.session.commit()
        
        return jsonify({"success": True, "message": f"已标记 {len(notifications)} 条消息为已读"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("批量标记已读失败")
        return jsonify({"success": False, "message": "操作失败"})


@notification_bp.route("/config")
@login_required
@permission_required("config:view")
def config_list():
    """
    通知配置列表（管理员查看）
    """
    merchant_id = request.args.get("merchant_id", 1, type=int)
    
    configs = NotificationConfig.query.filter_by(merchant_id=merchant_id).all()
    
    return render_template(
        "notification/config.html",
        configs=configs,
        merchant_id=merchant_id
    )


@notification_bp.route("/config/save", methods=["POST"])
@login_required
@permission_required("config:update")
def save_config():
    """
    保存通知配置
    """
    try:
        merchant_id = request.form.get("merchant_id", type=int)
        scene = request.form.get("scene", "").strip()
        
        if not scene:
            return jsonify({"success": False, "message": "场景不能为空"})
        
        # 查找或创建配置
        config = NotificationConfig.query.filter_by(
            merchant_id=merchant_id,
            scene=scene
        ).first()
        
        if not config:
            config = NotificationConfig(
                merchant_id=merchant_id,
                scene=scene
            )
            db.session.add(config)
        
        # 更新配置
        config.enable_email = request.form.get("enable_email", 0, type=int)
        config.email_to = request.form.get("email_to", "").strip()
        config.enable_webhook = request.form.get("enable_webhook", 0, type=int)
        config.webhook_url = request.form.get("webhook_url", "").strip()
        config.enable_site_msg = request.form.get("enable_site_msg", 1, type=int)
        
        db.session.commit()
        
        logger.info(f"保存通知配置成功：merchant_id={merchant_id}, scene={scene}")
        return jsonify({"success": True, "message": "保存成功"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("保存通知配置失败")
        return jsonify({"success": False, "message": "保存失败"})
