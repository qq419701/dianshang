import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.order import Order
from app.models.shop import Shop
from app.services.notification import send_order_notification
from app.services.jd_game import (
    callback_game_direct_success,
    callback_game_card_deliver,
    callback_game_refund,
)
from app.services.jd_general import (
    callback_general_success,
    callback_general_card_deliver,
    callback_general_refund,
)
from app.services.agiso import agiso_auto_deliver
import logging


logger = logging.getLogger(__name__)

order_bp = Blueprint('order', __name__)

# 回调状态常量：0=未回调 1=成功 2=失败
NOTIFY_STATUS_SUCCESS = 1
NOTIFY_STATUS_FAILED = 2


@order_bp.route('/')
@login_required
def order_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Order.query

    # Permission filtering
    if not current_user.is_admin:
        permitted_ids = current_user.get_permitted_shop_ids()
        if permitted_ids is not None:
            query = query.filter(Order.shop_id.in_(permitted_ids)) if permitted_ids else query.filter(db.false())

    # Filters
    shop_id = request.args.get('shop_id', type=int)
    shop_type = request.args.get('shop_type', type=int)
    order_type = request.args.get('order_type', type=int)
    order_status = request.args.get('order_status', type=int)
    jd_order_no = request.args.get('jd_order_no', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    if shop_id:
        query = query.filter(Order.shop_id == shop_id)
    if shop_type:
        query = query.filter(Order.shop_type == shop_type)
    if order_type:
        query = query.filter(Order.order_type == order_type)
    if order_status is not None and order_status != -1:
        query = query.filter(Order.order_status == order_status)
    if jd_order_no:
        query = query.filter(Order.jd_order_no.like(f'%{jd_order_no}%'))
    if start_date:
        try:
            query = query.filter(Order.create_time >= datetime.strptime(start_date, '%Y-%m-%d'))
        except ValueError:
            pass
    if end_date:
        try:
            query = query.filter(Order.create_time <= datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        except ValueError:
            pass

    pagination = query.order_by(Order.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items

    # Get shops for filter dropdown
    if current_user.is_admin:
        shops = Shop.query.order_by(Shop.shop_name).all()
    else:
        permitted_ids = current_user.get_permitted_shop_ids()
        shops = Shop.query.filter(Shop.id.in_(permitted_ids)).order_by(Shop.shop_name).all() if permitted_ids else []

    return render_template('order/list.html', orders=orders, pagination=pagination, shops=shops)


@order_bp.route('/detail/<int:order_id>')
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash('订单不存在', 'danger')
        return redirect(url_for('order.order_list'))

    if not current_user.is_admin and not current_user.has_shop_permission(order.shop_id):
        flash('无权限查看此订单', 'danger')
        return redirect(url_for('order.order_list'))

    return render_template('order/detail.html', order=order)


@order_bp.route('/<int:order_id>/save-cards', methods=['POST'])
@login_required
def save_cards(order_id):
    """保存卡密信息"""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')
    
    if order.order_type != 2:
        return jsonify(success=False, message='该订单不是卡密订单')
    
    data = request.get_json()
    cards = data.get('cards', [])
    
    if len(cards) != order.quantity:
        return jsonify(success=False, message=f'卡密数量不匹配，需要{order.quantity}组')
    
    # 保存卡密
    order.set_card_info(cards)
    db.session.commit()
    
    logger.info(f"订单 {order.order_no} 保存了 {len(cards)} 组卡密")
    
    return jsonify(success=True, message=f'成功保存{len(cards)}组卡密')


@order_bp.route('/<int:order_id>/notify-success', methods=['POST'])
@login_required
def notify_success(order_id):
    """通知京东订单成功"""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')
    
    shop = order.shop
    if not shop:
        return jsonify(success=False, message='店铺不存在')
    
    # 如果是卡密订单，检查是否已填写卡密
    if order.order_type == 2:
        if not order.card_info_parsed:
            return jsonify(success=False, message='请先填写卡密信息')
    
    # 根据店铺类型和订单类型调用不同的回调接口
    try:
        if shop.shop_type == 1:
            # 游戏点卡平台
            if order.order_type == 1:
                # 直充订单
                success, message = callback_game_direct_success(shop, order)
            else:
                # 卡密订单
                success, message = callback_game_card_deliver(shop, order, order.card_info_parsed)
        else:
            # 通用交易平台
            if order.order_type == 1:
                # 直充订单
                success, message = callback_general_success(shop, order)
            else:
                # 卡密订单
                success, message = callback_general_card_deliver(shop, order, order.card_info_parsed)
        
        if success:
            # 更新订单状态
            order.order_status = 2
            order.notify_status = NOTIFY_STATUS_SUCCESS
            order.notify_time = datetime.now()
            db.session.commit()
            
            logger.info(f"订单 {order.order_no} 通知成功")
            return jsonify(success=True, message='通知成功')
        else:
            order.notify_status = NOTIFY_STATUS_FAILED
            db.session.commit()
            return jsonify(success=False, message=message)
    
    except Exception as e:
        logger.error(f"订单 {order.order_no} 通知失败：{e}")
        order.notify_status = NOTIFY_STATUS_FAILED
        db.session.commit()
        return jsonify(success=False, message=f'通知失败：{str(e)}')


@order_bp.route('/<int:order_id>/notify-refund', methods=['POST'])
@login_required
def notify_refund(order_id):
    """通知京东订单退款"""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')
    
    shop = order.shop
    if not shop:
        return jsonify(success=False, message='店铺不存在')
    
    # 检查是否可以退款
    if order.order_status == 4:
        return jsonify(success=False, message='订单已退款')
    
    # 根据店铺类型调用对应的退款回调
    try:
        if shop.shop_type == 1:
            # 游戏点卡平台
            success, message = callback_game_refund(shop, order)
        else:
            # 通用交易平台
            success, message = callback_general_refund(shop, order)
        
        if success:
            # 更新订单状态为已退款
            order.order_status = 4
            order.notify_status = NOTIFY_STATUS_SUCCESS
            order.notify_time = datetime.now()
            db.session.commit()
            
            logger.info(f"订单 {order.order_no} 退款通知成功")
            return jsonify(success=True, message='退款通知已发送')
        else:
            order.notify_status = NOTIFY_STATUS_FAILED
            db.session.commit()
            return jsonify(success=False, message=message)
    
    except Exception as e:
        logger.error(f"订单 {order.order_no} 退款通知失败：{e}")
        order.notify_status = NOTIFY_STATUS_FAILED
        db.session.commit()
        return jsonify(success=False, message=f'退款通知失败：{str(e)}')


@order_bp.route('/<int:order_id>/agiso-deliver', methods=['POST'])
@login_required
def agiso_deliver(order_id):
    """使用阿奇索自动发货"""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')
    
    shop = order.shop
    if not shop:
        return jsonify(success=False, message='店铺不存在')
    
    # 调用阿奇索自动发货服务
    success, message, data = agiso_auto_deliver(shop, order)
    
    if success:
        # 更新订单状态
        order.order_status = 2
        order.notify_status = NOTIFY_STATUS_SUCCESS
        order.notify_time = datetime.now()
        db.session.commit()
        
        logger.info(f"订单 {order.order_no} 阿奇索发货成功")
        return jsonify(success=True, message=message)
    else:
        return jsonify(success=False, message=message)


@order_bp.route('/<int:order_id>/debug-success', methods=['POST'])
@login_required
def debug_success(order_id):
    """自助联调：标记订单为充值成功(不触发回调)"""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')
    
    # 更新订单状态为2(已完成)
    order.order_status = 2
    db.session.commit()
    
    logger.info(f"订单 {order.order_no} 自助联调标记为充值成功")
    return jsonify(success=True, message='订单已标记为充值成功')


@order_bp.route('/<int:order_id>/debug-processing', methods=['POST'])
@login_required
def debug_processing(order_id):
    """自助联调：标记订单为充值中"""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')
    
    # 更新订单状态为1(处理中)
    order.order_status = 1
    db.session.commit()
    
    logger.info(f"订单 {order.order_no} 自助联调标记为充值中")
    return jsonify(success=True, message='订单已标记为充值中')


@order_bp.route('/<int:order_id>/debug-failed', methods=['POST'])
@login_required
def debug_failed(order_id):
    """自助联调：标记订单为充值失败"""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')
    
    # 更新订单状态为3(已取消)
    order.order_status = 3
    db.session.commit()
    
    logger.info(f"订单 {order.order_no} 自助联调标记为充值失败")
    return jsonify(success=True, message='订单已标记为充值失败')


@order_bp.route('/<int:order_id>/detail-html', methods=['GET'])
@login_required
def order_detail_html(order_id):
    """返回订单详情HTML片段（用于弹窗）"""
    order = db.session.get(Order, order_id)
    if not order:
        return '<div class="alert alert-error">订单不存在</div>', 404
    
    # 渲染详情页模板的主体部分（不包含外层布局）
    return render_template('order/detail_modal.html', order=order)
