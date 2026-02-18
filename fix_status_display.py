import sys
sys.path.insert(0, '/www/wwwroot/dianshang')

# 检查订单列表模板中的状态显示逻辑
with open('app/templates/order/list.html', 'r', encoding='utf-8') as f:
    content = f.read()
    
print("检查模板中的状态显示...")
if "order_status" in content:
    print("✅ 找到 order_status 字段")
    
    # 检查是否有状态映射
    status_keywords = ['待处理', '处理中', '已完成', '已取消', '已退款', '异常']
    found = [kw for kw in status_keywords if kw in content]
    
    if found:
        print(f"✅ 找到状态文本: {', '.join(found)}")
    else:
        print("⚠️  未找到状态文本映射，可能直接显示数字")
else:
    print("❌ 未找到 order_status 字段")

print("\n当前状态码说明：")
print("0 = 待处理")
print("1 = 处理中")
print("2 = 已完成")
print("3 = 已取消")
print("4 = 已退款")
print("5 = 异常")
