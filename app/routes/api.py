"""External API endpoints for JD order callbacks and internal API."""
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.order import Order
from app.models.shop import Shop
from app.services.notification import send_order_notification, send_test_notification

api_bp = Blueprint('api', __name__)


@api_bp.route('/order/create', methods=['POST'])
def create_order():
    """Receive order from JD platform."""
    data = request.get_json()
    if not data:
        return jsonify(success=False, message='无效请求数据'), 400

    shop_code = data.get('shop_code')
    shop = Shop.query.filter_by(shop_code=shop_code, is_enabled=1).first()
    if not shop:
        return jsonify(success=False, message='店铺不存在或已禁用'), 400

    order_no = f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    order = Order(
        order_no=order_no,
        jd_order_no=data.get('jd_order_no', ''),
        shop_id=shop.id,
        shop_type=shop.shop_type,
        order_type=int(data.get('order_type', 1)),
        order_status=int(data.get('order_status', 0)),
        sku_id=data.get('sku_id'),
        product_info=data.get('product_info'),
        amount=int(data.get('amount', 0)),
        quantity=int(data.get('quantity', 1)),
        produce_account=data.get('produce_account'),
        notify_url=data.get('notify_url'),
    )

    db.session.add(order)
    db.session.commit()

    # Send notification if enabled
    try:
        send_order_notification(order, shop)
    except Exception:
        pass  # Don't fail order creation if notification fails

    return jsonify(success=True, message='订单创建成功', order_no=order_no)


@api_bp.route('/shop/test-notification', methods=['POST'])
def api_test_notification():
    """Send test notification for a shop."""
    data = request.get_json()
    if not data:
        return jsonify(success=False, message='无效请求数据'), 400

    shop_id = data.get('shop_id')
    notify_type = data.get('notify_type', 'dingtalk')

    shop = db.session.get(Shop, shop_id)
    if not shop:
        return jsonify(success=False, message='店铺不存在')

    ok, msg = send_test_notification(shop, notify_type)
    return jsonify(success=ok, message=msg)


@api_bp.route('/notification/resend', methods=['POST'])
def api_resend_notification():
    """Resend a notification."""
    from app.services.notification import resend_notification

    data = request.get_json()
    log_id = data.get('log_id')
    if not log_id:
        return jsonify(success=False, message='缺少日志ID')

    ok, msg = resend_notification(log_id)
    return jsonify(success=ok, message=msg)
