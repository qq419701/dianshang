"""外部API接口 - 京东平台订单回调及内部API。

支持京东游戏点卡平台和京东通用交易平台的订单接收，
包含MD5签名验证功能。
"""
import json
import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.order import Order
from app.models.shop import Shop
from app.services.notification import send_order_notification, send_test_notification
from app.services.jd_game import verify_game_sign
from app.services.jd_general import verify_general_sign

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/order/create', methods=['POST'])
def create_order():
    """接收京东平台订单。

    支持京东游戏点卡平台和通用交易平台的订单推送。
    根据店铺类型自动选择对应的签名验证方式。
    """
    data = request.get_json()
    if not data:
        return jsonify(success=False, message='无效请求数据'), 400

    shop_code = data.get('shop_code')
    shop = Shop.query.filter_by(shop_code=shop_code, is_enabled=1).first()
    if not shop:
        return jsonify(success=False, message='店铺不存在或已禁用'), 400

    # 根据店铺类型验证签名
    if shop.shop_type == 1 and shop.game_md5_secret:
        # 京东游戏点卡平台 - MD5签名验证
        if not verify_game_sign(data, shop.game_md5_secret):
            logger.warning("游戏点卡订单签名验证失败: shop=%s", shop.shop_code)
            return jsonify(success=False, message='签名验证失败'), 403
    elif shop.shop_type == 2 and shop.general_md5_secret:
        # 京东通用交易平台 - MD5签名验证
        if not verify_general_sign(data, shop.general_md5_secret):
            logger.warning("通用交易订单签名验证失败: shop=%s", shop.shop_code)
            return jsonify(success=False, message='签名验证失败'), 403

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

    # 如果店铺启用了通知，发送订单通知
    try:
        send_order_notification(order, shop)
    except Exception:
        pass  # 通知失败不影响订单创建

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
