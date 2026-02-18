import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.order import Order
from app.models.shop import Shop
from app.services.notification import send_order_notification

order_bp = Blueprint('order', __name__)


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


@order_bp.route('/notify-success/<int:order_id>', methods=['POST'])
@login_required
def notify_success(order_id):
    """Direct charge: notify success (update status to completed)."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')

    if not current_user.is_admin and not current_user.has_shop_permission(order.shop_id):
        return jsonify(success=False, message='无权限')

    if not current_user.is_admin and not current_user.can_deliver:
        return jsonify(success=False, message='无发货权限')

    order.order_status = 2
    order.deliver_time = datetime.utcnow()
    order.notify_status = 1
    order.notify_time = datetime.utcnow()
    db.session.commit()

    return jsonify(success=True, message='操作成功')


@order_bp.route('/notify-refund/<int:order_id>', methods=['POST'])
@login_required
def notify_refund(order_id):
    """Notify refund (update status to cancelled)."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')

    if not current_user.is_admin and not current_user.has_shop_permission(order.shop_id):
        return jsonify(success=False, message='无权限')

    if not current_user.is_admin and not current_user.can_refund:
        return jsonify(success=False, message='无退款权限')

    order.order_status = 3
    order.notify_status = 1
    order.notify_time = datetime.utcnow()
    db.session.commit()

    return jsonify(success=True, message='退款通知成功')


@order_bp.route('/deliver-card/<int:order_id>', methods=['POST'])
@login_required
def deliver_card(order_id):
    """Card key delivery: submit card numbers and passwords."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')

    if not current_user.is_admin and not current_user.has_shop_permission(order.shop_id):
        return jsonify(success=False, message='无权限')

    if not current_user.is_admin and not current_user.can_deliver:
        return jsonify(success=False, message='无发货权限')

    data = request.get_json()
    cards = data.get('cards', [])

    if not cards or len(cards) != order.quantity:
        return jsonify(success=False, message=f'需要提供{order.quantity}组卡密信息')

    order.card_info = json.dumps(cards, ensure_ascii=False)
    order.order_status = 2
    order.deliver_time = datetime.utcnow()
    order.notify_status = 1
    order.notify_time = datetime.utcnow()
    db.session.commit()

    return jsonify(success=True, message='卡密发货成功')


@order_bp.route('/self-debug/<int:order_id>', methods=['POST'])
@login_required
def self_debug(order_id):
    """Self-debug: directly change order status without callback."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')

    if not current_user.is_admin and not current_user.has_shop_permission(order.shop_id):
        return jsonify(success=False, message='无权限')

    data = request.get_json()
    status = data.get('status')

    status_map = {
        'success': 2,  # 充值成功
        'processing': 1,  # 充值中
        'failed': 3,  # 充值失败
    }

    if status not in status_map:
        return jsonify(success=False, message='无效的状态')

    order.order_status = status_map[status]
    db.session.commit()

    return jsonify(success=True, message='状态已更新')


@order_bp.route('/agiso-deliver/<int:order_id>', methods=['POST'])
@login_required
def agiso_deliver(order_id):
    """Agiso delivery placeholder."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(success=False, message='订单不存在')

    if not current_user.is_admin and not current_user.has_shop_permission(order.shop_id):
        return jsonify(success=False, message='无权限')

    shop = db.session.get(Shop, order.shop_id)
    if not shop or shop.agiso_enabled != 1:
        return jsonify(success=False, message='未启用阿奇索')

    # Placeholder: actual Agiso API integration would go here
    return jsonify(success=False, message='阿奇索接口对接中，暂不可用')
