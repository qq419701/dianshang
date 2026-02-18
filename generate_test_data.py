"""生成测试数据：100个店铺 + 10万个订单"""
import sys
import random
import secrets
from datetime import datetime, timedelta
sys.path.insert(0, '/www/wwwroot/dianshang')

from app import create_app
from app.extensions import db
from app.models.shop import Shop
from app.models.order import Order

def generate_test_data():
    app = create_app()
    with app.app_context():
        print("🚀 开始生成测试数据...")
        
        # 生成 100 个店铺
        print("\n📦 正在生成 100 个测试店铺...")
        shops = []
        shop_types = [1, 2]
        
        for i in range(1, 101):
            shop_type = random.choice(shop_types)
            shop = Shop(
                shop_name=f'测试店铺{i:03d}号',
                shop_code=f'TEST_SHOP_{i:05d}',
                shop_type=shop_type,
                is_enabled=random.choice([0, 1]),
                game_customer_id=f'GAME_CUSTOMER_{i:05d}' if shop_type == 1 else None,
                game_md5_secret=secrets.token_hex(16) if shop_type == 1 else None,
                game_direct_callback_url='https://jd-game.example.com/callback/direct' if shop_type == 1 else None,
                game_card_callback_url='https://jd-game.example.com/callback/card' if shop_type == 1 else None,
                game_api_url='https://api.jd-game.com/v1' if shop_type == 1 else None,
                general_vendor_id=f'VENDOR_{i:05d}' if shop_type == 2 else None,
                general_md5_secret=secrets.token_hex(16) if shop_type == 2 else None,
                general_callback_url='https://jd-general.example.com/callback' if shop_type == 2 else None,
                general_api_url='https://api.jd-general.com/v1' if shop_type == 2 else None,
                notify_enabled=random.choice([0, 1]),
                expire_time=datetime.utcnow() + timedelta(days=random.randint(30, 365)),
                remark=f'测试店铺{i}号'
            )
            shops.append(shop)
            if i % 10 == 0:
                print(f"  ✅ 已生成 {i}/100 个店铺")
        
        db.session.bulk_save_objects(shops)
        db.session.commit()
        print(f"✅ 成功生成 100 个店铺！")
        
        # 获取店铺ID
        shop_ids = [s.id for s in Shop.query.filter(Shop.shop_code.like('TEST_SHOP_%')).all()]
        
        # 生成 10万个订单
        print("\n📦 正在生成 10万个测试订单...")
        order_statuses = [0, 1, 2, 3, 4, 5]
        order_types = [1, 2]
        products = ['王者荣耀点券', 'QQ会员', '腾讯视频VIP', '爱奇艺会员', '优酷会员',
                   'Steam充值卡', '网易云音乐VIP', 'B站大会员', '微信读书VIP', '喜马拉雅VIP']
        
        batch_size = 1000
        total_orders = 100000
        
        for batch in range(0, total_orders, batch_size):
            orders = []
            for i in range(batch, min(batch + batch_size, total_orders)):
                shop_id = random.choice(shop_ids)
                shop = Shop.query.get(shop_id)
                create_time = datetime.utcnow() - timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                order_status = random.choice(order_statuses)
                order_type = random.choice(order_types)
                product = random.choice(products)
                amount = random.choice([10, 30, 50, 88, 98, 128, 198, 298])
                quantity = random.randint(1, 10)
                
                order = Order(
                    order_no=f'ORD{create_time.strftime("%Y%m%d%H%M%S")}{i:06d}',
                    jd_order_no=f'JD{random.randint(1000000000, 9999999999)}',
                    shop_id=shop_id,
                    shop_type=shop.shop_type,
                    order_type=order_type,
                    order_status=order_status,
                    sku_id=f'SKU{random.randint(100000, 999999)}',
                    product_info=f'{product} x {quantity}',
                    amount=amount * quantity,
                    quantity=quantity,
                    produce_account=f'user{random.randint(10000, 99999)}@example.com',
                    create_time=create_time
                )
                orders.append(order)
            
            db.session.bulk_save_objects(orders)
            db.session.commit()
            completed = min(batch + batch_size, total_orders)
            progress = (completed / total_orders) * 100
            print(f"  ✅ 已生成 {completed:,}/{total_orders:,} 个订单 ({progress:.1f}%)")
        
        print(f"\n✅ 成功生成 10万个订单！")
        print("\n" + "="*50)
        print("📊 测试数据统计")
        print("="*50)
        print(f"店铺总数: {Shop.query.filter(Shop.shop_code.like('TEST_SHOP_%')).count()}")
        print(f"订单总数: {Order.query.count():,}")
        for status in order_statuses:
            count = Order.query.filter_by(order_status=status).count()
            status_name = ['待处理', '处理中', '已完成', '已取消', '已退款', '异常'][status]
            print(f"  - {status_name}: {count:,}")

if __name__ == '__main__':
    generate_test_data()
