# -*- coding: utf-8 -*-
"""
==============================================
  商户模型
  功能：商户信息管理
  对应数据库表：merchants
==============================================
"""

from app import db
from datetime import datetime


class Merchant(db.Model):
    """
    商户表
    存储商户基本信息
    """
    __tablename__ = "merchants"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    name = db.Column(db.String(128), nullable=False, comment="商户名称")
    code = db.Column(db.String(64), unique=True, comment="商户代码")
    contact_name = db.Column(db.String(128), comment="联系人姓名")
    contact_mobile = db.Column(db.String(32), comment="联系人手机")
    contact_email = db.Column(db.String(128), comment="联系人邮箱")
    status = db.Column(db.SmallInteger, default=1, comment="状态：0=禁用, 1=启用")
    remark = db.Column(db.Text, comment="备注")
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    update_time = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关联关系
    users = db.relationship("User", back_populates="merchant", lazy="dynamic")
    jd_configs = db.relationship("MerchantJdConfig", back_populates="merchant", lazy="dynamic")
    notification_configs = db.relationship("NotificationConfig", back_populates="merchant", lazy="dynamic")

    __table_args__ = (
        {"comment": "商户表"},
    )

    def is_active(self):
        """检查商户是否激活"""
        return self.status == 1

    def __repr__(self):
        return f"<Merchant {self.name} ({self.code})>"
