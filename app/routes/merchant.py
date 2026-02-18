# -*- coding: utf-8 -*-
"""
==============================================
  商户管理路由
  功能：商户CRUD
==============================================
"""

import logging
from flask import Blueprint, request, render_template, jsonify
from app import db
from app.models.merchant import Merchant
from app.utils.auth_decorator import login_required, permission_required
from app.services.auth_service import log_operation, get_current_user

# 创建蓝图
merchant_bp = Blueprint("merchant", __name__)

# 日志记录器
logger = logging.getLogger(__name__)


@merchant_bp.route("/")
@login_required
@permission_required("merchant:view")
def merchant_list():
    """
    商户列表页
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    
    query = Merchant.query
    
    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                Merchant.name.like(f"%{search}%"),
                Merchant.code.like(f"%{search}%")
            )
        )
    
    # 分页查询
    pagination = query.order_by(Merchant.create_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        "merchant/list.html",
        merchants=pagination.items,
        pagination=pagination,
        search=search
    )


@merchant_bp.route("/create", methods=["POST"])
@login_required
@permission_required("merchant:create")
def create_merchant():
    """
    创建商户
    """
    try:
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        contact_name = request.form.get("contact_name", "").strip()
        contact_mobile = request.form.get("contact_mobile", "").strip()
        contact_email = request.form.get("contact_email", "").strip()
        remark = request.form.get("remark", "").strip()
        
        # 参数验证
        if not name:
            return jsonify({"success": False, "message": "商户名称不能为空"})
        
        # 检查商户代码是否已存在
        if code and Merchant.query.filter_by(code=code).first():
            return jsonify({"success": False, "message": "商户代码已存在"})
        
        # 创建商户
        merchant = Merchant(
            name=name,
            code=code,
            contact_name=contact_name,
            contact_mobile=contact_mobile,
            contact_email=contact_email,
            remark=remark,
            status=1
        )
        
        db.session.add(merchant)
        db.session.commit()
        
        # 记录操作日志
        log_operation(
            user=get_current_user(),
            operation=f"创建商户：{name}",
            module="merchant",
            status=1
        )
        
        logger.info(f"创建商户成功：{name}")
        return jsonify({"success": True, "message": "创建成功"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("创建商户失败")
        return jsonify({"success": False, "message": "创建失败"})


@merchant_bp.route("/update", methods=["POST"])
@login_required
@permission_required("merchant:update")
def update_merchant():
    """
    更新商户
    """
    try:
        merchant_id = request.form.get("merchant_id", type=int)
        merchant = Merchant.query.get(merchant_id)
        
        if not merchant:
            return jsonify({"success": False, "message": "商户不存在"})
        
        # 更新字段
        merchant.name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        
        # 检查商户代码是否已被其他商户使用
        if code and code != merchant.code:
            if Merchant.query.filter_by(code=code).first():
                return jsonify({"success": False, "message": "商户代码已存在"})
            merchant.code = code
        
        merchant.contact_name = request.form.get("contact_name", "").strip()
        merchant.contact_mobile = request.form.get("contact_mobile", "").strip()
        merchant.contact_email = request.form.get("contact_email", "").strip()
        merchant.remark = request.form.get("remark", "").strip()
        merchant.status = request.form.get("status", 1, type=int)
        
        db.session.commit()
        
        # 记录操作日志
        log_operation(
            user=get_current_user(),
            operation=f"更新商户：{merchant.name}",
            module="merchant",
            status=1
        )
        
        logger.info(f"更新商户成功：{merchant.name}")
        return jsonify({"success": True, "message": "更新成功"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("更新商户失败")
        return jsonify({"success": False, "message": "更新失败"})


@merchant_bp.route("/delete", methods=["POST"])
@login_required
@permission_required("merchant:delete")
def delete_merchant():
    """
    删除商户（软删除，禁用）
    """
    try:
        merchant_id = request.form.get("merchant_id", type=int)
        merchant = Merchant.query.get(merchant_id)
        
        if not merchant:
            return jsonify({"success": False, "message": "商户不存在"})
        
        # 软删除：设置状态为禁用
        merchant.status = 0
        db.session.commit()
        
        # 记录操作日志
        log_operation(
            user=get_current_user(),
            operation=f"删除商户：{merchant.name}",
            module="merchant",
            status=1
        )
        
        logger.info(f"删除商户成功：{merchant.name}")
        return jsonify({"success": True, "message": "删除成功"})
        
    except Exception as e:
        db.session.rollback()
        logger.exception("删除商户失败")
        return jsonify({"success": False, "message": "删除失败"})
