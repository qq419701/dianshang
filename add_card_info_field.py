import sys
sys.path.insert(0, '/www/wwwroot/dianshang')
from app import create_app
from app.extensions import db

def add_field():
    app = create_app()
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('orders')]
        
        if 'card_info' not in columns:
            db.session.execute(db.text(
                'ALTER TABLE orders ADD COLUMN card_info TEXT COMMENT "卡密信息JSON"'
            ))
            db.session.commit()
            print("✅ card_info 字段添加成功")
        else:
            print("✅ card_info 字段已存在")

if __name__ == '__main__':
    add_field()
