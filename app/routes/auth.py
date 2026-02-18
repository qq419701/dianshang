# -*- coding: utf-8 -*-
"""
==============================================
  认证路由
  功能：登录页面、登录接口、登出接口
==============================================
"""

import logging
from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from app.services.auth_service import login_user, logout_user, get_current_user

# 创建蓝图
auth_bp = Blueprint("auth", __name__)

# 日志记录器
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["GET"])
def login():
    """
    登录页面
    """
    # 如果已登录，重定向到管理首页
    user = get_current_user()
    if user:
        return redirect(url_for("admin.dashboard"))
    
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"])
def do_login():
    """
    登录接口（AJAX）
    """
    try:
        # 获取表单数据
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember", "0") == "1"
        
        # 参数验证
        if not username or not password:
            return jsonify({"success": False, "message": "用户名和密码不能为空"})
        
        # 执行登录
        success, message, user = login_user(username, password, remember)
        
        if success:
            return jsonify({
                "success": True,
                "message": message,
                "redirect": url_for("admin.dashboard")
            })
        else:
            return jsonify({"success": False, "message": message})
        
    except Exception as e:
        logger.exception("登录处理异常")
        return jsonify({"success": False, "message": "登录失败，请稍后重试"})


@auth_bp.route("/logout")
def logout():
    """
    登出接口
    """
    logout_user()
    return redirect(url_for("auth.login"))
