import sys
sys.path.insert(0, '/www/wwwroot/dianshang')

from app import create_app
from app.models.order import Order

def check_orders():
    app = create_app()
    with app.app_context():
        jd_order_nos = ['JD2960835998', 'JD5581545799', 'JD7915637412', 'JD6904335081']
        
        status_map = {
            0: '待处理',
            1: '处理中',
            2: '已完成',
            3: '已取消',
            4: '已退款',
            5: '异常'
        }
        
        print("=" * 80)
        print("📦 京东订单状态查询")
        print("=" * 80)
        
        for jd_no in jd_order_nos:
            order = Order.query.filter_by(jd_order_no=jd_no).first()
            if order:
                status_text = status_map.get(order.order_status, f'未知({order.order_status})')
                print(f"\n京东订单号: {jd_no}")
                print(f"  系统订单号: {order.order_no}")
                print(f"  订单状态: {status_text} [{order.order_status}]")
                print(f"  订单类型: {'直充' if order.order_type == 1 else '卡密'}")
                print(f"  商品信息: {order.product_info}")
                print(f"  订单金额: ¥{order.amount}")
                print(f"  创建时间: {order.create_time}")
                print(f"  店铺ID: {order.shop_id}")
            else:
                print(f"\n京东订单号: {jd_no}")
                print(f"  ❌ 未找到该订单")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    check_orders()
