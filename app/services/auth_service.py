# -*- coding: utf-8 -*-
"""
==============================================
  认证服务
  功能：用户登录、登出、权限检查
==============================================
"""

import logging
from datetime import datetime
from flask import session, request
from app import db
from app.models.user import User
from app.models.operation_log import OperationLog

logger = logging.getLogger(__name__)


def login_user(username, password, remember=False):
    """
    用户登录
    
    参数：
        username: 用户名
        password: 密码
        remember: 是否记住登录
    
    返回：
        (success: bool, message: str, user: User)
    """
    try:
        # 查找用户
        user = User.query.filter_by(username=username).first()
        if not user:
            logger.warning(f"登录失败：用户不存在 - {username}")
            return False, "用户名或密码错误", None
        
        # 检查用户状态
        if not user.is_active():
            logger.warning(f"登录失败：账号已禁用 - {username}")
            return False, "账号已被禁用", None
        
        # 验证密码
        if not user.check_password(password):
            logger.warning(f"登录失败：密码错误 - {username}")
            return False, "用户名或密码错误", None
        
        # 更新登录信息
        user.last_login_time = datetime.utcnow()
        user.last_login_ip = get_client_ip()
        
        # 设置Session
        session.permanent = remember
        session["user_id"] = user.id
        session["username"] = user.username
        session["role_id"] = user.role_id
        session["merchant_id"] = user.merchant_id
        
        # 记录操作日志
        log_operation(
            user=user,
            operation="用户登录",
            module="auth",
            status=1
        )
        
        db.session.commit()
        logger.info(f"用户登录成功：{username}")
        return True, "登录成功", user
        
    except Exception as e:
        logger.exception("登录处理异常")
        db.session.rollback()
        return False, "登录失败，请稍后重试", None


def logout_user():
    """
    用户登出
    """
    try:
        user_id = session.get("user_id")
        username = session.get("username")
        
        if user_id:
            # 记录操作日志
            log_operation(
                user_id=user_id,
                username=username,
                operation="用户登出",
                module="auth",
                status=1
            )
        
        # 清除Session
        session.clear()
        logger.info(f"用户登出：{username}")
        return True, "登出成功"
        
    except Exception as e:
        logger.exception("登出处理异常")
        return False, "登出失败"


def get_current_user():
    """
    获取当前登录用户
    
    返回：
        User对象或None
    """
    user_id = session.get("user_id")
    if not user_id:
        return None
    
    user = User.query.get(user_id)
    if not user or not user.is_active():
        return None
    
    return user


def check_permission(permission):
    """
    检查当前用户是否拥有指定权限
    
    参数：
        permission: 权限代码，如 "user:view"
    
    返回：
        bool
    """
    user = get_current_user()
    if not user:
        return False
    
    return user.has_permission(permission)


def get_client_ip():
    """
    获取客户端IP地址
    """
    if request.environ.get("HTTP_X_FORWARDED_FOR"):
        return request.environ["HTTP_X_FORWARDED_FOR"].split(",")[0].strip()
    elif request.environ.get("HTTP_X_REAL_IP"):
        return request.environ["HTTP_X_REAL_IP"]
    else:
        return request.environ.get("REMOTE_ADDR", "")


def log_operation(user=None, user_id=None, username=None, operation="", module="", 
                 method="", path="", request_data="", response_data="", 
                 status=1, error_message=""):
    """
    记录操作日志
    
    参数：
        user: User对象（可选）
        user_id: 用户ID（可选）
        username: 用户名（可选）
        operation: 操作名称
        module: 模块名称
        method: 请求方法
        path: 请求路径
        request_data: 请求数据
        response_data: 响应数据
        status: 状态（0=失败, 1=成功）
        error_message: 错误信息
    """
    try:
        if user:
            user_id = user.id
            username = user.username
        
        log = OperationLog(
            user_id=user_id,
            username=username or "",
            operation=operation,
            module=module,
            method=method or request.method,
            path=path or request.path,
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent", "")[:500],
            request_data=request_data,
            response_data=response_data,
            status=status,
            error_message=error_message
        )
        
        db.session.add(log)
        db.session.commit()
        
    except Exception as e:
        logger.exception("记录操作日志失败")
        db.session.rollback()
