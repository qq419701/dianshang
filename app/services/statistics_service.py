# -*- coding: utf-8 -*-
"""
==============================================
  统计服务
  功能：商户和店铺维度的统计分析
==============================================
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app import db
from app.models.order import Order
from app.models.shop import Shop
from app.models.merchant import Merchant

logger = logging.getLogger(__name__)


def get_merchant_statistics(merchant_id, start_date=None, end_date=None):
    """
    获取商户维度统计
    
    参数：
        merchant_id: 商户ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    返回：
        dict 包含统计数据
    """
    try:
        # 构建查询条件
        conditions = [Order.merchant_id == merchant_id]
        if start_date:
            conditions.append(Order.create_time >= start_date)
        if end_date:
            conditions.append(Order.create_time <= end_date)

        # 统计数据
        stats = db.session.query(
            func.count(Order.id).label('total_orders'),
            func.sum(db.case((Order.order_status == 0, 1), else_=0)).label('success_orders'),
            func.sum(db.case((Order.order_status == 2, 1), else_=0)).label('failed_orders'),
            func.sum(db.case((Order.order_status == 1, 1), else_=0)).label('pending_orders'),
            func.sum(Order.amount).label('total_amount'),
            func.sum(db.case((Order.order_status == 0, Order.amount), else_=0)).label('success_amount')
        ).filter(and_(*conditions)).first()

        total = stats.total_orders or 0
        success = stats.success_orders or 0
        
        return {
            'total_orders': total,
            'success_orders': success,
            'failed_orders': stats.failed_orders or 0,
            'pending_orders': stats.pending_orders or 0,
            'total_amount': stats.total_amount or 0,
            'success_amount': stats.success_amount or 0,
            'success_rate': round(success * 100 / total, 2) if total > 0 else 0
        }

    except Exception as e:
        logger.exception("获取商户统计失败")
        return None


def get_shop_statistics(shop_id, start_date=None, end_date=None):
    """
    获取店铺维度统计
    
    参数：
        shop_id: 店铺ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    返回：
        dict 包含统计数据
    """
    try:
        conditions = [Order.shop_id == shop_id]
        if start_date:
            conditions.append(Order.create_time >= start_date)
        if end_date:
            conditions.append(Order.create_time <= end_date)

        stats = db.session.query(
            func.count(Order.id).label('total_orders'),
            func.sum(db.case((Order.order_status == 0, 1), else_=0)).label('success_orders'),
            func.sum(db.case((Order.order_status == 2, 1), else_=0)).label('failed_orders'),
            func.sum(Order.amount).label('total_amount'),
            func.sum(db.case((Order.order_status == 0, Order.amount), else_=0)).label('success_amount')
        ).filter(and_(*conditions)).first()

        total = stats.total_orders or 0
        success = stats.success_orders or 0

        return {
            'total_orders': total,
            'success_orders': success,
            'failed_orders': stats.failed_orders or 0,
            'total_amount': stats.total_amount or 0,
            'success_amount': stats.success_amount or 0,
            'success_rate': round(success * 100 / total, 2) if total > 0 else 0
        }

    except Exception as e:
        logger.exception("获取店铺统计失败")
        return None


def get_merchant_shops_statistics(merchant_id, start_date=None, end_date=None):
    """
    获取商户下所有店铺的统计对比数据
    
    参数：
        merchant_id: 商户ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    返回：
        list 包含每个店铺的统计数据
    """
    try:
        shops = Shop.query.filter_by(merchant_id=merchant_id).all()
        
        result = []
        for shop in shops:
            stats = get_shop_statistics(shop.id, start_date, end_date)
            if stats:
                result.append({
                    'shop_id': shop.id,
                    'shop_name': shop.shop_name,
                    'shop_code': shop.shop_code,
                    'biz_type': shop.biz_type,
                    'biz_type_name': shop.get_biz_type_name(),
                    **stats
                })
        
        return result

    except Exception as e:
        logger.exception("获取商户店铺统计失败")
        return []


def get_biz_type_statistics(merchant_id, start_date=None, end_date=None):
    """
    获取业务类型统计（通用交易 vs 游戏点卡）
    
    参数：
        merchant_id: 商户ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    返回：
        dict 包含各业务类型的统计
    """
    try:
        conditions = [Order.merchant_id == merchant_id]
        if start_date:
            conditions.append(Order.create_time >= start_date)
        if end_date:
            conditions.append(Order.create_time <= end_date)

        stats = db.session.query(
            Order.biz_type,
            func.count(Order.id).label('total_orders'),
            func.sum(db.case((Order.order_status == 0, 1), else_=0)).label('success_orders'),
            func.sum(Order.amount).label('total_amount')
        ).filter(and_(*conditions)).group_by(Order.biz_type).all()

        result = {}
        for stat in stats:
            biz_name = "通用交易" if stat.biz_type == 1 else "游戏点卡"
            result[biz_name] = {
                'total_orders': stat.total_orders or 0,
                'success_orders': stat.success_orders or 0,
                'total_amount': stat.total_amount or 0
            }

        return result

    except Exception as e:
        logger.exception("获取业务类型统计失败")
        return {}


def get_daily_statistics(merchant_id, days=7):
    """
    获取每日统计趋势（用于图表）
    
    参数：
        merchant_id: 商户ID
        days: 统计天数
    
    返回：
        list 包含每天的统计数据
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 按日期分组统计
        stats = db.session.query(
            func.date(Order.create_time).label('date'),
            func.count(Order.id).label('total_orders'),
            func.sum(db.case((Order.order_status == 0, 1), else_=0)).label('success_orders'),
            func.sum(Order.amount).label('total_amount')
        ).filter(
            and_(
                Order.merchant_id == merchant_id,
                Order.create_time >= start_date,
                Order.create_time <= end_date
            )
        ).group_by(func.date(Order.create_time)).order_by('date').all()

        result = []
        for stat in stats:
            result.append({
                'date': stat.date.strftime('%Y-%m-%d'),
                'total_orders': stat.total_orders or 0,
                'success_orders': stat.success_orders or 0,
                'total_amount': stat.total_amount or 0
            })

        return result

    except Exception as e:
        logger.exception("获取每日统计失败")
        return []


def generate_chart_data(merchant_id, start_date=None, end_date=None):
    """
    生成图表数据（用于ECharts）
    
    参数：
        merchant_id: 商户ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    返回：
        dict 包含图表所需的数据格式
    """
    try:
        shops_stats = get_merchant_shops_statistics(merchant_id, start_date, end_date)
        
        # 店铺流水对比
        shop_names = [stat['shop_name'] for stat in shops_stats]
        shop_orders = [stat['total_orders'] for stat in shops_stats]
        shop_amounts = [stat['total_amount'] / 100 for stat in shops_stats]  # 转换为元

        return {
            'shop_names': shop_names,
            'shop_orders': shop_orders,
            'shop_amounts': shop_amounts
        }

    except Exception as e:
        logger.exception("生成图表数据失败")
        return {
            'shop_names': [],
            'shop_orders': [],
            'shop_amounts': []
        }
