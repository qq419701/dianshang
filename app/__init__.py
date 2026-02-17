# -*- coding: utf-8 -*-
"""
==============================================
  Flask 应用工厂
  功能：创建并配置 Flask 应用实例，注册蓝图和数据库
==============================================
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

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

    # 注册蓝图 — 后台管理页面
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # 在应用上下文中创建数据库表
    with app.app_context():
        from app.models import merchant_config, order, callback_log  # noqa: F401
        db.create_all()

    return app
