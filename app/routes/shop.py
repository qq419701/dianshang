# -*- coding: utf-8 -*-
"""
==============================================
  店铺管理路由
  功能：店铺CRUD、店铺配置管理
==============================================
"""

import logging
from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models.shop import Shop
from app.services import shop_service
from app.utils.auth_decorator import login_required, permission_required
from app.services.auth_service import log_operation, get_current_user

# 创建蓝图
shop_bp = Blueprint("shop", __name__)

# 日志记录器
logger = logging.getLogger(__name__)


@shop_bp.route("/list/<int:merchant_id>")
@login_required
@permission_required("shop:view")
def shop_list(merchant_id):
    """
    获取商户下的店铺列表
    """
    try:
        biz_type = request.args.get("biz_type", type=int)
        shops = shop_service.get_shops_by_merchant(merchant_id, biz_type)
        
        # 构建返回数据
        result = []
        for shop in shops:
            result.append({
                'id': shop.id,
                'shop_name': shop.shop_name,
                'shop_code': shop.shop_code,
                'biz_type': shop.biz_type,
                'biz_type_name': shop.get_biz_type_name(),
                'is_enabled': shop.is_enabled,
                'order_count': shop.get_order_count(),
                'config_complete': shop.check_config_complete(),
                'create_time': shop.create_time.strftime('%Y-%m-%d %H:%M:%S') if shop.create_time else '',
                'remark': shop.remark or ''
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.exception("获取店铺列表失败")
        return jsonify({'success': False, 'message': '获取失败'})


@shop_bp.route("/detail/<int:shop_id>")
@login_required
@permission_required("shop:view")
def shop_detail(shop_id):
    """
    获取店铺详情（含解密后的配置）
    """
    try:
        config = shop_service.get_shop_config_decrypted(shop_id)
        if not config:
            return jsonify({'success': False, 'message': '店铺不存在'})
        
        # 获取当前用户
        user = get_current_user()
        
        # 权限检查：操作员只能查看自己商户的店铺
        if user.merchant_id and user.merchant_id != config['merchant_id']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 掩码敏感信息（非超级管理员）
        if user.role and user.role.code != 'super_admin':
            if config.get('md5_secret'):
                config['md5_secret'] = '******'
            if config.get('aes_secret'):
                config['aes_secret'] = '******'
        
        return jsonify({'success': True, 'data': config})
        
    except Exception as e:
        logger.exception("获取店铺详情失败")
        return jsonify({'success': False, 'message': '获取失败'})


@shop_bp.route("/create", methods=["POST"])
@login_required
@permission_required("shop:create")
def create_shop():
    """
    创建店铺
    """
    try:
        data = request.get_json() if request.is_json else request.form
        
        merchant_id = data.get("merchant_id", type=int)
        shop_name = data.get("shop_name", "").strip()
        shop_code = data.get("shop_code", "").strip()
        biz_type = data.get("biz_type", type=int)
        
        # 参数验证
        if not all([merchant_id, shop_name, biz_type]):
            return jsonify({'success': False, 'message': '必填参数不能为空'})
        
        if biz_type not in [1, 2]:
            return jsonify({'success': False, 'message': '业务类型错误'})
        
        # 获取当前用户
        user = get_current_user()
        
        # 权限检查：操作员只能为自己的商户创建店铺
        if user.merchant_id and user.merchant_id != merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 构建配置参数
        config = {
            'is_enabled': data.get('is_enabled', 1),
            'remark': data.get('remark', '').strip(),
            'our_api_url': data.get('our_api_url', '').strip(),
            'md5_secret': data.get('md5_secret', '').strip(),
            'aes_secret': data.get('aes_secret', '').strip()
        }
        
        # 业务类型相关配置
        if biz_type == 1:
            config['vendor_id'] = data.get('vendor_id', type=int)
            config['jd_callback_url'] = data.get('jd_callback_url', '').strip()
        elif biz_type == 2:
            config['customer_id'] = data.get('customer_id', type=int)
            config['jd_direct_callback_url'] = data.get('jd_direct_callback_url', '').strip()
            config['jd_card_callback_url'] = data.get('jd_card_callback_url', '').strip()
        
        # 创建店铺
        success, message, shop = shop_service.create_shop(
            merchant_id=merchant_id,
            shop_name=shop_name,
            shop_code=shop_code,
            biz_type=biz_type,
            **config
        )
        
        if success:
            # 记录操作日志
            log_operation(
                user=user,
                operation=f"创建店铺：{shop_name}",
                module="shop",
                status=1
            )
            return jsonify({'success': True, 'message': message, 'shop_id': shop.id})
        else:
            return jsonify({'success': False, 'message': message})
        
    except Exception as e:
        logger.exception("创建店铺失败")
        return jsonify({'success': False, 'message': '创建失败'})


@shop_bp.route("/update/<int:shop_id>", methods=["POST"])
@login_required
@permission_required("shop:update")
def update_shop(shop_id):
    """
    更新店铺配置
    """
    try:
        data = request.get_json() if request.is_json else request.form
        
        # 验证店铺存在
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({'success': False, 'message': '店铺不存在'})
        
        # 获取当前用户
        user = get_current_user()
        
        # 权限检查：操作员只能更新自己商户的店铺
        if user.merchant_id and user.merchant_id != shop.merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 构建更新参数
        updates = {}
        
        if 'shop_name' in data:
            updates['shop_name'] = data['shop_name'].strip()
        if 'shop_code' in data:
            updates['shop_code'] = data['shop_code'].strip()
        if 'is_enabled' in data:
            updates['is_enabled'] = int(data['is_enabled'])
        if 'remark' in data:
            updates['remark'] = data['remark'].strip()
        if 'our_api_url' in data:
            updates['our_api_url'] = data['our_api_url'].strip()
        if 'md5_secret' in data:
            updates['md5_secret'] = data['md5_secret'].strip()
        if 'aes_secret' in data:
            updates['aes_secret'] = data['aes_secret'].strip()
        
        # 业务类型相关配置
        if shop.biz_type == 1:
            if 'vendor_id' in data:
                vendor_id_val = data['vendor_id']
                updates['vendor_id'] = int(vendor_id_val) if vendor_id_val and str(vendor_id_val).strip() != '' else None
            if 'jd_callback_url' in data:
                updates['jd_callback_url'] = data['jd_callback_url'].strip()
        elif shop.biz_type == 2:
            if 'customer_id' in data:
                customer_id_val = data['customer_id']
                updates['customer_id'] = int(customer_id_val) if customer_id_val and str(customer_id_val).strip() != '' else None
            if 'jd_direct_callback_url' in data:
                updates['jd_direct_callback_url'] = data['jd_direct_callback_url'].strip()
            if 'jd_card_callback_url' in data:
                updates['jd_card_callback_url'] = data['jd_card_callback_url'].strip()
        
        # 更新店铺
        success, message = shop_service.update_shop(shop_id, **updates)
        
        if success:
            # 记录操作日志
            log_operation(
                user=user,
                operation=f"更新店铺：{shop.shop_name}",
                module="shop",
                status=1
            )
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
        
    except Exception as e:
        logger.exception("更新店铺失败")
        return jsonify({'success': False, 'message': '更新失败'})


@shop_bp.route("/delete/<int:shop_id>", methods=["POST"])
@login_required
@permission_required("shop:delete")
def delete_shop(shop_id):
    """
    删除店铺（软删除）
    """
    try:
        # 验证店铺存在
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({'success': False, 'message': '店铺不存在'})
        
        # 获取当前用户
        user = get_current_user()
        
        # 权限检查：操作员只能删除自己商户的店铺
        if user.merchant_id and user.merchant_id != shop.merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        force = request.args.get('force', 'false').lower() == 'true'
        
        # 删除店铺
        success, message = shop_service.delete_shop(shop_id, force=force)
        
        if success:
            # 记录操作日志
            log_operation(
                user=user,
                operation=f"删除店铺：{shop.shop_name}",
                module="shop",
                status=1
            )
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
        
    except Exception as e:
        logger.exception("删除店铺失败")
        return jsonify({'success': False, 'message': '删除失败'})


@shop_bp.route("/statistics/<int:shop_id>")
@login_required
@permission_required("shop:view")
def shop_statistics(shop_id):
    """
    获取店铺统计数据
    """
    try:
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({'success': False, 'message': '店铺不存在'})
        
        # 获取当前用户
        user = get_current_user()
        
        # 权限检查
        if user.merchant_id and user.merchant_id != shop.merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取统计数据
        stats = shop.get_order_statistics()
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        logger.exception("获取店铺统计失败")
        return jsonify({'success': False, 'message': '获取失败'})
