# -*- coding: utf-8 -*-
"""
==============================================
  用户管理路由
  功能：用户CRUD、角色列表
==============================================
"""

import logging
from flask import Blueprint, request, render_template, jsonify
from app import db
from app.models.user import User, Role
from app.utils.auth_decorator import login_required, permission_required
from app.services.auth_service import log_operation, get_current_user

# 创建蓝图
user_bp = Blueprint("user", __name__)

# 日志记录器
logger = logging.getLogger(__name__)


@user_bp.route("/")
@login_required
@permission_required("user:view")
def user_list():
    """
    用户列表页
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    
    query = User.query
    
    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                User.username.like(f"%{search}%"),
                User.real_name.like(f"%{search}%"),
                User.email.like(f"%{search}%")
            )
        )
    
    # 分页查询
    pagination = query.order_by(User.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取所有角色（用于下拉选择）
    roles = Role.query.filter_by(status=1).all()
    
    return render_template(
        "user/list.html",
        users=pagination.items,
        pagination=pagination,
        roles=roles,
        search=search
    )


@user_bp.route("/roles")
@login_required
def role_list():
    """
    获取角色列表（JSON）
    """
    try:
        roles = Role.query.filter_by(status=1).all()
        data = [{
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "description": role.description
        } for role in roles]
        
        return jsonify({"success": True, "data": data})
    
    except Exception as e:
        logger.exception("获取角色列表失败")
        return jsonify({"success": False, "message": "获取角色列表失败"})


@user_bp.route("/create", methods=["POST"])
@login_required
@permission_required("user:create")
def create_user():
    """
    创建用户
    """
    try:
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        real_name = request.form.get("real_name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        role_id = request.form.get("role_id", type=int)
        merchant_id = request.form.get("merchant_id", type=int)
        
        # 参数验证
        if not username:
            return jsonify({"success": False, "message": "用户名不能为空"})
        if not password:
            return jsonify({"success": False, "message": "密码不能为空"})
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({"success": False, "message": "用户名已存在"})
        
        # 创建用户
        user = User(
            username=username,
            real_name=real_name,
            email=email,
            mobile=mobile,
            role_id=role_id,
            merchant_id=merchant_id,
            status=1
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # 记录操作日志
        log_operation(
            user=get_current_user(),
            operation=f"创建用户：{username}",
            module="user",
            status=1
        )
        
        logger.info(f"创建用户成功：{username}")
        return jsonify({"success": True, "message": "创建成功"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("创建用户失败")
        return jsonify({"success": False, "message": "创建失败"})


@user_bp.route("/update", methods=["POST"])
@login_required
@permission_required("user:update")
def update_user():
    """
    更新用户
    """
    try:
        user_id = request.form.get("user_id", type=int)
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "用户不存在"})
        
        # 更新字段
        user.real_name = request.form.get("real_name", "").strip()
        user.email = request.form.get("email", "").strip()
        user.mobile = request.form.get("mobile", "").strip()
        user.role_id = request.form.get("role_id", type=int)
        user.merchant_id = request.form.get("merchant_id", type=int)
        user.status = request.form.get("status", 1, type=int)
        
        # 如果提供了新密码，则更新密码
        new_password = request.form.get("password", "").strip()
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        
        # 记录操作日志
        log_operation(
            user=get_current_user(),
            operation=f"更新用户：{user.username}",
            module="user",
            status=1
        )
        
        logger.info(f"更新用户成功：{user.username}")
        return jsonify({"success": True, "message": "更新成功"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("更新用户失败")
        return jsonify({"success": False, "message": "更新失败"})


@user_bp.route("/delete", methods=["POST"])
@login_required
@permission_required("user:delete")
def delete_user():
    """
    删除用户（软删除，禁用）
    """
    try:
        user_id = request.form.get("user_id", type=int)
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "用户不存在"})
        
        # 不能删除自己
        current_user = get_current_user()
        if current_user.id == user_id:
            return jsonify({"success": False, "message": "不能删除当前登录用户"})
        
        # 软删除：设置状态为禁用
        user.status = 0
        db.session.commit()
        
        # 记录操作日志
        log_operation(
            user=current_user,
            operation=f"删除用户：{user.username}",
            module="user",
            status=1
        )
        
        logger.info(f"删除用户成功：{user.username}")
        return jsonify({"success": True, "message": "删除成功"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("删除用户失败")
        return jsonify({"success": False, "message": "删除失败"})
