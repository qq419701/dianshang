"""清理测试数据"""
import sys
sys.path.insert(0, '/www/wwwroot/dianshang')

from app import create_app
from app.extensions import db
from app.models.shop import Shop
from app.models.order import Order

def clean_test_data():
    app = create_app()
    with app.app_context():
        print("🧹 开始清理测试数据...")
        test_shop_ids = [s.id for s in Shop.query.filter(Shop.shop_code.like('TEST_SHOP_%')).all()]
        
        if test_shop_ids:
            deleted_orders = Order.query.filter(Order.shop_id.in_(test_shop_ids)).delete(synchronize_session=False)
            db.session.commit()
            print(f"✅ 已删除 {deleted_orders:,} 个测试订单")
        
        deleted_shops = Shop.query.filter(Shop.shop_code.like('TEST_SHOP_%')).delete(synchronize_session=False)
        db.session.commit()
        print(f"✅ 已删除 {deleted_shops} 个测试店铺")
        print(f"\n剩��店铺数: {Shop.query.count()}")
        print(f"剩余订单数: {Order.query.count():,}")

if __name__ == '__main__':
    clean_test_data()
