#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
==============================================
  数据迁移脚本
  功能：从 merchant_jd_config 迁移数据到 shops 表
  使用方式：python scripts/migrate_to_shops.py
==============================================
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.merchant_config import MerchantJdConfig
from app.models.shop import Shop
from app.models.order import Order
from sqlalchemy.exc import IntegrityError

def migrate_configs_to_shops():
    """
    将 merchant_jd_config 表的配置迁移到 shops 表
    """
    print("开始迁移配置数据...")
    
    # 获取所有配置
    configs = MerchantJdConfig.query.filter_by(is_enabled=1).all()
    
    migrated_count = 0
    skipped_count = 0
    
    for config in configs:
        try:
            # 检查是否已经迁移过
            existing_shop = Shop.query.filter_by(
                merchant_id=config.merchant_id,
                biz_type=config.biz_type
            ).first()
            
            if existing_shop:
                print(f"跳过：商户 {config.merchant_id} 的业务类型 {config.biz_type} 已存在店铺")
                skipped_count += 1
                continue
            
            # 生成店铺名称
            biz_type_name = "通用交易" if config.biz_type == 1 else "游戏点卡"
            shop_name = f"京东{biz_type_name}店铺"
            shop_code = f"jd_{config.biz_type}_{config.merchant_id}"
            
            # 创建店铺
            shop = Shop(
                merchant_id=config.merchant_id,
                shop_name=shop_name,
                shop_code=shop_code,
                biz_type=config.biz_type,
                vendor_id=config.vendor_id,
                customer_id=config.customer_id,
                md5_secret=config.md5_secret,
                aes_secret=config.aes_secret,
                our_api_url=config.our_api_url,
                jd_callback_url=config.jd_callback_url,
                jd_direct_callback_url=config.jd_direct_callback_url,
                jd_card_callback_url=config.jd_card_callback_url,
                is_enabled=config.is_enabled,
                remark=f"从配置ID {config.id} 自动迁移"
            )
            
            db.session.add(shop)
            db.session.flush()  # 获取shop.id
            
            # 更新关联订单
            Order.query.filter_by(
                merchant_id=config.merchant_id,
                biz_type=config.biz_type
            ).update({Order.shop_id: shop.id})
            
            db.session.commit()
            
            print(f"成功迁移：商户 {config.merchant_id} 的 {biz_type_name} 配置 -> 店铺 {shop.id}")
            migrated_count += 1
            
        except IntegrityError as e:
            db.session.rollback()
            print(f"错误：迁移商户 {config.merchant_id} 的配置失败 - {str(e)}")
            skipped_count += 1
        except Exception as e:
            db.session.rollback()
            print(f"错误：迁移商户 {config.merchant_id} 的配置失败 - {str(e)}")
            skipped_count += 1
    
    print(f"\n迁移完成：")
    print(f"  - 成功迁移：{migrated_count} 个配置")
    print(f"  - 跳过/失败：{skipped_count} 个配置")


def update_orphan_orders():
    """
    处理没有关联店铺的订单
    尝试根据 merchant_id 和 biz_type 匹配到店铺
    """
    print("\n处理未关联店铺的订单...")
    
    # 查找没有shop_id的订单
    orphan_orders = Order.query.filter(
        db.or_(Order.shop_id.is_(None), Order.shop_id == 0)
    ).all()
    
    updated_count = 0
    failed_count = 0
    
    for order in orphan_orders:
        # 尝试找到匹配的店铺
        shop = Shop.query.filter_by(
            merchant_id=order.merchant_id,
            biz_type=order.biz_type
        ).first()
        
        if shop:
            order.shop_id = shop.id
            updated_count += 1
        else:
            print(f"警告：订单 {order.id} 找不到匹配的店铺（商户={order.merchant_id}, 类型={order.biz_type}）")
            failed_count += 1
    
    if updated_count > 0:
        db.session.commit()
    
    print(f"订单关联更新完成：")
    print(f"  - 成功关联：{updated_count} 个订单")
    print(f"  - 无法关联：{failed_count} 个订单")


def verify_migration():
    """
    验证迁移结果
    """
    print("\n验证迁移结果...")
    
    # 统计店铺数量
    shop_count = Shop.query.count()
    print(f"店铺总数：{shop_count}")
    
    # 统计各商户的店铺数
    from sqlalchemy import func
    merchant_shop_counts = db.session.query(
        Shop.merchant_id,
        func.count(Shop.id)
    ).group_by(Shop.merchant_id).all()
    
    print("\n各商户店铺数：")
    for merchant_id, count in merchant_shop_counts:
        print(f"  - 商户 {merchant_id}: {count} 个店铺")
    
    # 统计订单关联情况
    total_orders = Order.query.count()
    linked_orders = Order.query.filter(Order.shop_id != None, Order.shop_id != 0).count()
    unlinked_orders = total_orders - linked_orders
    
    print(f"\n订单关联情况：")
    print(f"  - 总订单数：{total_orders}")
    print(f"  - 已关联店铺：{linked_orders} ({linked_orders*100/total_orders:.1f}%)" if total_orders > 0 else "  - 已关联店铺：0 (0%)")
    print(f"  - 未关联店铺：{unlinked_orders}")


def main():
    """
    主函数
    """
    print("=" * 50)
    print("数据迁移工具 - merchant_jd_config -> shops")
    print("=" * 50)
    
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        try:
            # 执行迁移
            migrate_configs_to_shops()
            
            # 更新订单关联
            update_orphan_orders()
            
            # 验证结果
            verify_migration()
            
            print("\n" + "=" * 50)
            print("迁移完成！")
            print("=" * 50)
            
        except Exception as e:
            print(f"\n迁移失败：{str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
