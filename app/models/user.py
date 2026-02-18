# -*- coding: utf-8 -*-
"""
==============================================
  用户和角色模型
  功能：用户认证、角色权限管理
  对应数据库表：users, roles
==============================================
"""

from app import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json


class Role(db.Model):
    """
    角色表
    存储系统角色及其权限信息
    """
    __tablename__ = "roles"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    name = db.Column(db.String(64), nullable=False, unique=True, comment="角色名称")
    code = db.Column(db.String(64), nullable=False, unique=True, comment="角色代码")
    description = db.Column(db.String(255), comment="角色描述")
    permissions = db.Column(db.Text, comment="权限列表（JSON格式）")
    status = db.Column(db.SmallInteger, default=1, comment="状态：0=禁用, 1=启用")
    create_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")

    # 关联的用户
    users = db.relationship("User", back_populates="role", lazy="dynamic")

    __table_args__ = (
        {"comment": "角色表"},
    )

    def get_permissions(self):
        """获取权限列表"""
        if not self.permissions:
            return []
        try:
            return json.loads(self.permissions)
        except:
            return []

    def has_permission(self, permission):
        """
        检查是否拥有指定权限
        支持通配符：*:* 表示所有权限
        """
        perms = self.get_permissions()
        if "*:*" in perms:
            return True
        if permission in perms:
            return True
        # 检查模块级通配符，如 "user:*"
        module = permission.split(":")[0]
        if f"{module}:*" in perms:
            return True
        return False

    def __repr__(self):
        return f"<Role {self.name} ({self.code})>"


class User(db.Model):
    """
    用户表
    存储系统用户信息
    """
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    username = db.Column(db.String(64), nullable=False, unique=True, comment="用户名")
    password_hash = db.Column(db.String(255), nullable=False, comment="密码哈希")
    real_name = db.Column(db.String(128), comment="真实姓名")
    email = db.Column(db.String(128), comment="邮箱")
    mobile = db.Column(db.String(32), comment="手机号")
    role_id = db.Column(db.BigInteger, db.ForeignKey("roles.id"), comment="角色ID")
    merchant_id = db.Column(db.BigInteger, db.ForeignKey("merchants.id"), comment="商户ID")
    status = db.Column(db.SmallInteger, default=1, comment="状态：0=禁用, 1=启用")
    last_login_time = db.Column(db.DateTime, comment="最后登录时间")
    last_login_ip = db.Column(db.String(64), comment="最后登录IP")
    create_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    update_time = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间"
    )

    # 关联关系
    role = db.relationship("Role", back_populates="users")
    merchant = db.relationship("Merchant", back_populates="users")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")
    operation_logs = db.relationship("OperationLog", back_populates="user", lazy="dynamic")

    __table_args__ = (
        {"comment": "用户表"},
    )

    def set_password(self, password):
        """设置密码（加密存储）"""
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission):
        """检查用户是否拥有指定权限"""
        if not self.role:
            return False
        return self.role.has_permission(permission)

    def is_active(self):
        """检查用户是否激活"""
        return self.status == 1

    def __repr__(self):
        return f"<User {self.username} ({self.real_name})>"
