# -*- coding: utf-8 -*-
"""
==============================================
  回调日志模型
  功能：记录京东回调请求和我方主动回调的日志
  对应数据库表：jd_callbacks、agiso_logs
==============================================
"""

from app import db
from datetime import datetime


class JdCallback(db.Model):
    """
    京东回调记录表
    记录所有与京东之间的回调交互（含入站和出站）
    """
    __tablename__ = "jd_callbacks"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    order_id = db.Column(db.BigInteger, nullable=False, comment="订单ID")
    callback_type = db.Column(
        db.SmallInteger, nullable=False,
        comment="回调类型：1=通用交易回调, 2=直充回调, 3=卡密回调"
    )
    callback_direction = db.Column(
        db.SmallInteger,
        comment="回调方向：1=京东调我方, 2=我方调京东"
    )
    request_params = db.Column(db.Text, comment="请求参数（脱敏后存储）")
    response_data = db.Column(db.Text, comment="响应数据（脱敏后存储）")
    result_code = db.Column(db.String(32), comment="结果码")
    result_message = db.Column(db.String(500), comment="结果信息")
    retry_count = db.Column(db.Integer, default=0, comment="重试次数")
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = ({"comment": "京东回调记录表"},)

    def __repr__(self):
        return f"<JdCallback 订单ID={self.order_id} 类型={self.callback_type}>"


class AgisoLog(db.Model):
    """
    阿奇索调用日志表
    记录与阿奇索平台之间所有API调用的日志（独立隔离）
    """
    __tablename__ = "agiso_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    merchant_id = db.Column(db.BigInteger, nullable=False, comment="商户ID")
    api_name = db.Column(db.String(128), comment="接口名称")
    request_data = db.Column(db.Text, comment="请求数据（脱敏后存储）")
    response_data = db.Column(db.Text, comment="响应数据（脱敏后存储）")
    result_code = db.Column(db.String(32), comment="结果码")
    result_message = db.Column(db.String(500), comment="结果信息")
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")

    __table_args__ = ({"comment": "阿奇索调用日志表"},)

    def __repr__(self):
        return f"<AgisoLog 商户={self.merchant_id} 接口={self.api_name}>"
