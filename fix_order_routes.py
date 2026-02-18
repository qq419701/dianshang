"""删除重复的路由定义，保留新版本"""
with open('app/routes/order.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 标记要删除的行范围
# 删除第一个 notify_success (104行开始) 到第一个 notify_refund 之前
# 删除第一个 notify_refund (140行开始) 到下一个函数之前

new_lines = []
skip_until = -1

for i, line in enumerate(lines):
    line_num = i + 1
    
    # 跳过第一个 notify_success (104-139行)
    if line_num == 104 and 'def notify_success' in line:
        skip_until = 140
        print(f"跳过第一个 notify_success (行 104-139)")
        continue
    
    # 跳过第一个 notify_refund (140-298行，到 save_cards 之前)
    if line_num == 140 and 'def notify_refund' in line:
        skip_until = 299
        print(f"跳过第一个 notify_refund (行 140-298)")
        continue
    
    # 如果在跳过范围内，继续跳过
    if skip_until > 0 and line_num < skip_until:
        continue
    
    # 重置跳过标记
    if line_num == skip_until:
        skip_until = -1
    
    new_lines.append(line)

# 写回文件
with open('app/routes/order.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"✅ 原始行数: {len(lines)}")
print(f"✅ 处理后行数: {len(new_lines)}")
print(f"✅ 删除了 {len(lines) - len(new_lines)} 行")
print("✅ 重复路由已删除")
