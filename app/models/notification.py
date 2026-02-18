# -*- coding: utf-8 -*-
"""
==============================================
  通知模型
  功能：站内消息、通知配置、通知日志
  对应数据库表：notifications, notification_configs, notification_logs
==============================================
"""

from app import db
from datetime import datetime


class Notification(db.Model):
    """
    站内消息表
    存储用户的站内通知消息
    """
    __tablename__ = "notifications"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), comment="用户ID")
    title = db.Column(db.String(255), nullable=False, comment="消息标题")
    content = db.Column(db.Text, comment="消息内容")
    type = db.Column(db.SmallInteger, comment="消息类型：1=系统, 2=订单, 3=配置, 4=警告")
    related_type = db.Column(db.String(32), comment="关联类型")
    related_id = db.Column(db.BigInteger, comment="关联ID")
    is_read = db.Column(db.SmallInteger, default=0, comment="已读状态：0=未读, 1=已读")
    read_time = db.Column(db.DateTime, comment="阅读时间")
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    user = db.relationship("User", back_populates="notifications")

    __table_args__ = (
        {"comment": "站内消息表"},
    )

    def mark_as_read(self):
        """标记为已读"""
        self.is_read = 1
        self.read_time = datetime.utcnow()

    def __repr__(self):
        return f"<Notification {self.title} user_id={self.user_id}>"


class NotificationConfig(db.Model):
    """
    通知配置表
    存储各商户的通知渠道配置
    """
    __tablename__ = "notification_configs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    merchant_id = db.Column(db.BigInteger, db.ForeignKey("merchants.id"), comment="商户ID")
    scene = db.Column(db.String(64), nullable=False, comment="通知场景")
    enable_email = db.Column(db.SmallInteger, default=0, comment="启用邮件：0=禁用, 1=启用")
    email_to = db.Column(db.String(512), comment="邮件接收人（多个用逗号分隔）")
    enable_webhook = db.Column(db.SmallInteger, default=0, comment="启用Webhook：0=禁用, 1=启用")
    webhook_url = db.Column(db.String(512), comment="Webhook地址")
    enable_site_msg = db.Column(db.SmallInteger, default=1, comment="启用站内信：0=禁用, 1=启用")
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    update_time = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关联关系
    merchant = db.relationship("Merchant", back_populates="notification_configs")

    __table_args__ = (
        db.UniqueConstraint("merchant_id", "scene", name="uk_merchant_scene"),
        {"comment": "通知配置表"},
    )

    def __repr__(self):
        return f"<NotificationConfig merchant_id={self.merchant_id} scene={self.scene}>"


class NotificationLog(db.Model):
    """
    通知日志表
    记录所有通知发送日志
    """
    __tablename__ = "notification_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    merchant_id = db.Column(db.BigInteger, comment="商户ID")
    scene = db.Column(db.String(64), comment="通知场景")
    channel = db.Column(db.String(32), comment="发送渠道：email/webhook/site_msg")
    to_address = db.Column(db.String(512), comment="接收地址")
    title = db.Column(db.String(255), comment="标题")
    content = db.Column(db.Text, comment="内容")
    status = db.Column(db.SmallInteger, comment="状态：0=失败, 1=成功")
    error_message = db.Column(db.Text, comment="错误信息")
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = (
        {"comment": "通知日志表"},
    )

    def __repr__(self):
        return f"<NotificationLog channel={self.channel} status={self.status}>"
