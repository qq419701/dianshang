from datetime import datetime, timedelta
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.order import Order
from app.models.shop import Shop

statistics_bp = Blueprint('statistics', __name__)


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            from flask import redirect, url_for, flash
            flash('无权限访问', 'danger')
            return redirect(url_for('order.order_list'))
        return f(*args, **kwargs)
    return decorated


@statistics_bp.route('/')
@login_required
@admin_required
def index():
    # Overall stats
    total_orders = Order.query.count()
    total_amount = db.session.query(func.sum(Order.amount)).scalar() or 0
    completed_orders = Order.query.filter_by(order_status=2).count()
    pending_orders = Order.query.filter(Order.order_status.in_([0, 1])).count()

    # Per-shop stats
    shop_stats = db.session.query(
        Shop.id,
        Shop.shop_name,
        func.count(Order.id).label('order_count'),
        func.coalesce(func.sum(Order.amount), 0).label('total_amount'),
    ).outerjoin(Order, Shop.id == Order.shop_id).group_by(Shop.id).all()

    # Recent 7 days stats
    today = datetime.utcnow().date()
    daily_stats = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = Order.query.filter(Order.create_time.between(day_start, day_end)).count()
        amount = db.session.query(func.sum(Order.amount)).filter(
            Order.create_time.between(day_start, day_end)
        ).scalar() or 0
        daily_stats.append({
            'date': day.strftime('%m-%d'),
            'count': count,
            'amount': amount / 100,
        })

    return render_template('statistics/index.html',
                           total_orders=total_orders,
                           total_amount=total_amount / 100,
                           completed_orders=completed_orders,
                           pending_orders=pending_orders,
                           shop_stats=shop_stats,
                           daily_stats=daily_stats)
