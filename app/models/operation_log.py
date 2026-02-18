# -*- coding: utf-8 -*-
"""
==============================================
  操作日志模型
  功能：记录用户操作审计日志
  对应数据库表：operation_logs
==============================================
"""

from app import db
from datetime import datetime, timezone


class OperationLog(db.Model):
    """
    操作日志表
    记录用户的所有操作行为
    """
    __tablename__ = "operation_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), comment="用户ID")
    username = db.Column(db.String(64), comment="用户名")
    operation = db.Column(db.String(128), comment="操作名称")
    module = db.Column(db.String(64), comment="操作模块")
    method = db.Column(db.String(16), comment="请求方法")
    path = db.Column(db.String(255), comment="请求路径")
    ip_address = db.Column(db.String(64), comment="IP地址")
    user_agent = db.Column(db.String(512), comment="User-Agent")
    request_data = db.Column(db.Text, comment="请求数据")
    response_data = db.Column(db.Text, comment="响应数据")
    status = db.Column(db.SmallInteger, comment="状态：0=失败, 1=成功")
    error_message = db.Column(db.Text, comment="错误信息")
    create_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")

    # 关联关系
    user = db.relationship("User", back_populates="operation_logs")

    __table_args__ = (
        {"comment": "操作日志表"},
    )

    def __repr__(self):
        return f"<OperationLog {self.operation} user={self.username}>"
