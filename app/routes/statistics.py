# -*- coding: utf-8 -*-
"""
==============================================
  统计报表路由
  功能：商户和店铺维度的统计分析
==============================================
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template
from app.services import statistics_service
from app.models.merchant import Merchant
from app.models.shop import Shop
from app.utils.auth_decorator import login_required, permission_required
from app.services.auth_service import get_current_user

# 创建蓝图
statistics_bp = Blueprint("statistics", __name__)

# 日志记录器
logger = logging.getLogger(__name__)


@statistics_bp.route("/")
@login_required
@permission_required("statistics:view")
def index():
    """
    统计报表首页
    """
    user = get_current_user()
    
    # 获取商户列表（操作员只能看到自己的商户）
    if user.merchant_id:
        merchants = Merchant.query.filter_by(id=user.merchant_id).all()
    else:
        merchants = Merchant.query.filter_by(status=1).all()
    
    return render_template("statistics/index.html", merchants=merchants)


@statistics_bp.route("/merchant/<int:merchant_id>")
@login_required
@permission_required("statistics:view")
def merchant_statistics(merchant_id):
    """
    获取商户统计数据
    """
    try:
        user = get_current_user()
        
        # 权限检查：操作员只能查看自己商户的数据
        if user.merchant_id and user.merchant_id != merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取日期范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # 获取统计数据
        stats = statistics_service.get_merchant_statistics(
            merchant_id=merchant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if stats:
            # 金额已经是分为单位，转换为元
            stats['total_amount'] = stats['total_amount'] / 100
            stats['success_amount'] = stats['success_amount'] / 100
            return jsonify({'success': True, 'data': stats})
        else:
            return jsonify({'success': False, 'message': '获取统计数据失败'})
        
    except Exception as e:
        logger.exception("获取商户统计失败")
        return jsonify({'success': False, 'message': '获取失败'})


@statistics_bp.route("/shops/<int:merchant_id>")
@login_required
@permission_required("statistics:view")
def shops_statistics(merchant_id):
    """
    获取商户下所有店铺的统计数据
    """
    try:
        user = get_current_user()
        
        # 权限检查
        if user.merchant_id and user.merchant_id != merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取日期范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # 获取店铺统计数据
        shops_stats = statistics_service.get_merchant_shops_statistics(
            merchant_id=merchant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 金额已经是分为单位，转换为元
        for stat in shops_stats:
            stat['total_amount'] = stat['total_amount'] / 100
            stat['success_amount'] = stat['success_amount'] / 100
        
        return jsonify({'success': True, 'data': shops_stats})
        
    except Exception as e:
        logger.exception("获取店铺统计失败")
        return jsonify({'success': False, 'message': '获取失败'})


@statistics_bp.route("/biz_type/<int:merchant_id>")
@login_required
@permission_required("statistics:view")
def biz_type_statistics(merchant_id):
    """
    获取业务类型统计数据
    """
    try:
        user = get_current_user()
        
        # 权限检查
        if user.merchant_id and user.merchant_id != merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取日期范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # 获取业务类型统计
        stats = statistics_service.get_biz_type_statistics(
            merchant_id=merchant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 金额已经是分为单位，转换为元
        for biz_name in stats:
            stats[biz_name]['total_amount'] = stats[biz_name]['total_amount'] / 100
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        logger.exception("获取业务类型统计失败")
        return jsonify({'success': False, 'message': '获取失败'})


@statistics_bp.route("/daily/<int:merchant_id>")
@login_required
@permission_required("statistics:view")
def daily_statistics(merchant_id):
    """
    获取每日统计趋势数据
    """
    try:
        user = get_current_user()
        
        # 权限检查
        if user.merchant_id and user.merchant_id != merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取统计天数
        days = request.args.get('days', 7, type=int)
        
        # 获取每日统计
        stats = statistics_service.get_daily_statistics(
            merchant_id=merchant_id,
            days=days
        )
        
        # 转换金额单位
        for stat in stats:
            stat['total_amount'] = stat['total_amount'] / 100
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        logger.exception("获取每日统计失败")
        return jsonify({'success': False, 'message': '获取失败'})


@statistics_bp.route("/chart/<int:merchant_id>")
@login_required
@permission_required("statistics:view")
def chart_data(merchant_id):
    """
    获取图表数据（用于ECharts）
    """
    try:
        user = get_current_user()
        
        # 权限检查
        if user.merchant_id and user.merchant_id != merchant_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取日期范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # 生成图表数据
        chart_data = statistics_service.generate_chart_data(
            merchant_id=merchant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({'success': True, 'data': chart_data})
        
    except Exception as e:
        logger.exception("生成图表数据失败")
        return jsonify({'success': False, 'message': '获取失败'})
