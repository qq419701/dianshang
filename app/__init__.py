# -*- coding: utf-8 -*-
"""
==============================================
  Flask 应用工厂
  功能：创建并配置 Flask 应用实例，注册蓝图和数据库
==============================================
"""

from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta

# 创建全局数据库实例
db = SQLAlchemy()


def create_app():
    """
    应用工厂函数
    创建 Flask 应用，加载配置，注册数据库和路由蓝图
    返回：Flask 应用实例
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # 加载配置
    app.config.from_object("config.Config")
    
    # Session 配置
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图 — 京东通用交易接口
    from app.routes.jd_general import jd_general_bp
    app.register_blueprint(jd_general_bp, url_prefix="/api/jd/general")

    # 注册蓝图 — 京东游戏点卡接口
    from app.routes.jd_game import jd_game_bp
    app.register_blueprint(jd_game_bp, url_prefix="/api/jd/game")

    # 注册蓝图 — 阿奇索开放平台接口
    from app.routes.agiso import agiso_bp
    app.register_blueprint(agiso_bp, url_prefix="/api/agiso")

    # 注册蓝图 — 用户认证
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    
    # 注册蓝图 — 用户管理
    from app.routes.user import user_bp
    app.register_blueprint(user_bp, url_prefix="/user")
    
    # 注册蓝图 — 商户管理
    from app.routes.merchant import merchant_bp
    app.register_blueprint(merchant_bp, url_prefix="/merchant")
    
    # 注册蓝图 — 通知管理
    from app.routes.notification import notification_bp
    app.register_blueprint(notification_bp, url_prefix="/notification")

    # 注册蓝图 — 后台管理页面
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # 在应用上下文中创建数据库表
    with app.app_context():
        from app.models import (
            merchant_config, order, callback_log,
            merchant, user, notification, operation_log
        )  # noqa: F401
        db.create_all()
    
    # 注册上下文处理器（提供全局变量给模板）
    @app.context_processor
    def inject_user():
        """注入当前用户和未读消息数到模板"""
        from app.services.auth_service import get_current_user
        from app.services.notification_service import get_unread_count
        
        user = get_current_user()
        unread_count = get_unread_count(user.id) if user else 0
        
        return {
            'current_user': user,
            'unread_count': unread_count
        }

    return app
