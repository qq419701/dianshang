"""检查并修复 order.py 的导入"""
with open('app/routes/order.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否有必要的导入
imports_needed = {
    'from flask import': ['request', 'jsonify'],
    'from app.extensions import': ['db'],
    'from app.models.order import': ['Order'],
    'import logging': []
}

# 检查 logger
if 'logger = logging.getLogger(__name__)' not in content:
    print("❌ 缺少 logger 定义")
    # 在文件开头的导入后添加
    lines = content.split('\n')
    # 找到最后一个 import 或 from 语句
    import_end = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_end = i
    
    # 在导入后添加 logger
    if 'import logging' not in content:
        lines.insert(import_end + 1, 'import logging')
        import_end += 1
    
    lines.insert(import_end + 2, '\nlogger = logging.getLogger(__name__)\n')
    content = '\n'.join(lines)
    
    with open('app/routes/order.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已添加 logger 定义")
else:
    print("✅ logger 已存在")

# 检查 jsonify 导入
if 'jsonify' not in content:
    print("⚠️  可能缺少 jsonify 导入")
else:
    print("✅ jsonify 已导入")
