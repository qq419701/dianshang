# -*- coding: utf-8 -*-
"""
==============================================
  认证装饰器
  功能：登录验证、权限验证、角色验证
==============================================
"""

from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from app.services.auth_service import get_current_user, check_permission
import logging

logger = logging.getLogger(__name__)


def login_required(f):
    """
    登录验证装饰器
    未登录用户将被重定向到登录页面
    
    使用示例：
        @login_required
        def my_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            # AJAX请求返回JSON
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": "未登录或登录已过期"}), 401
            # 普通请求重定向到登录页
            return redirect(url_for("auth.login", next=request.url))
        
        return f(*args, **kwargs)
    
    return decorated_function


def permission_required(permission):
    """
    权限验证装饰器
    检查用户是否拥有指定权限
    
    参数：
        permission: 权限代码，如 "user:view"
    
    使用示例：
        @login_required
        @permission_required("user:view")
        def user_list():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_permission(permission):
                logger.warning(f"权限不足：{permission}")
                # AJAX请求返回JSON
                if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"success": False, "message": "权限不足"}), 403
                # 普通请求返回403页面
                return "权限不足", 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def role_required(*role_codes):
    """
    角色验证装饰器
    检查用户是否属于指定角色
    
    参数：
        role_codes: 角色代码列表，如 "super_admin", "admin"
    
    使用示例：
        @login_required
        @role_required("super_admin", "admin")
        def admin_panel():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user or not user.role:
                logger.warning("用户未登录或无角色")
                if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"success": False, "message": "权限不足"}), 403
                return "权限不足", 403
            
            if user.role.code not in role_codes:
                logger.warning(f"角色不匹配：需要 {role_codes}, 当前 {user.role.code}")
                if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"success": False, "message": "权限不足"}), 403
                return "权限不足", 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
