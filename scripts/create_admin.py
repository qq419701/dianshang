#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================
  创建管理员账号脚本
  功能：创建初始超级管理员账号
  使用方式：python3 scripts/create_admin.py [password]
  如果不提供密码参数，将使用默认密码：admin123
==============================================
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User, Role
from app.models.merchant import Merchant


def create_admin(password=None):
    """创建管理员账号
    
    参数：
        password: 管理员密码，如果为None则使用默认密码admin123
    """
    app = create_app()
    
    with app.app_context():
        # 检查是否已存在admin用户
        existing_user = User.query.filter_by(username='admin').first()
        if existing_user:
            print("❌ 管理员账号已存在，无需重复创建")
            return
        
        # 检查超级管理员角色是否存在
        super_admin_role = Role.query.filter_by(code='super_admin').first()
        if not super_admin_role:
            print("❌ 错误：超级管理员角色不存在，请先执行数据库迁移脚本")
            return
        
        # 检查默认商户是否存在
        default_merchant = Merchant.query.get(1)
        if not default_merchant:
            print("❌ 错误：默认商户不存在，请先执行数据库迁移脚本")
            return
        
        # 使用提供的密码或默认密码
        if password is None:
            password = 'admin123'
            print("⚠️  未提供密码，使用默认密码：admin123")
        
        # 创建管理员账号
        admin = User(
            username='admin',
            real_name='系统管理员',
            email='admin@example.com',
            role_id=super_admin_role.id,
            merchant_id=default_merchant.id,
            status=1
        )
        
        # 设置密码
        admin.set_password(password)
        
        try:
            db.session.add(admin)
            db.session.commit()
            
            print("✅ 管理员账号创建成功！")
            print("=" * 50)
            print(f"用户名：admin")
            print(f"密码：{'admin123' if password == 'admin123' else '***（已设置）'}")
            print(f"角色：{super_admin_role.name}")
            print("=" * 50)
            if password == 'admin123':
                print("⚠️  重要提示：使用的是默认密码，首次登录后请立即修改！")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建管理员账号失败：{str(e)}")


if __name__ == '__main__':
    # 从命令行参数获取密码
    password = sys.argv[1] if len(sys.argv) > 1 else None
    create_admin(password)
