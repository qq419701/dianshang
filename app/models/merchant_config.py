# -*- coding: utf-8 -*-
"""
==============================================
  商户京东配置模型
  功能：存储商户的京东通用交易/游戏点卡/阿奇索平台配置
  对应数据库表：merchant_jd_config
==============================================
"""

from app import db
from datetime import datetime


class MerchantJdConfig(db.Model):
    """
    商户京东配置表
    每个商户可以分别配置通用交易(biz_type=1)和游戏点卡(biz_type=2)
    """
    __tablename__ = "merchant_jd_config"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    merchant_id = db.Column(db.BigInteger, nullable=False, comment="商户ID")
    biz_type = db.Column(db.SmallInteger, nullable=False, comment="业务类型：1=通用交易, 2=游戏点卡")

    # 京东通用交易字段
    vendor_id = db.Column(db.BigInteger, comment="京东vendorId（通用交易）")

    # 京东游戏点卡字段
    customer_id = db.Column(db.BigInteger, comment="京东customerId（游戏点卡）")

    # 公共字段 — 密钥使用系统AES加密存储
    md5_secret = db.Column(db.String(255), comment="MD5签名密钥（AES加密存储）")
    aes_secret = db.Column(db.String(255), comment="AES加密密钥（AES加密存储）")
    our_api_url = db.Column(db.String(500), comment="我方接口基础地址")
    jd_callback_url = db.Column(db.String(500), comment="京东回调地址")

    # 游戏点卡特有字段
    jd_direct_callback_url = db.Column(db.String(500), comment="京东直充回调地址")
    jd_card_callback_url = db.Column(db.String(500), comment="京东卡密回调地址")

    is_enabled = db.Column(db.SmallInteger, default=1, comment="启用开关：0=禁用, 1=启用")
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    update_time = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 唯一约束：同一商户同一业务类型只能有一条配置
    __table_args__ = (
        db.UniqueConstraint("merchant_id", "biz_type", name="uk_merchant_biz"),
        {"comment": "商户京东配置表"},
    )

    def __repr__(self):
        return f"<MerchantJdConfig 商户={self.merchant_id} 业务类型={self.biz_type}>"


class AgisoConfig(db.Model):
    """
    阿奇索开放平台配置表
    可选模块 — 按商户独立配置
    """
    __tablename__ = "agiso_config"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    merchant_id = db.Column(db.BigInteger, nullable=False, unique=True, comment="商户ID")

    host = db.Column(db.String(255), comment="阿奇索API网关地址")
    port = db.Column(db.Integer, comment="端口")
    app_id = db.Column(db.String(128), comment="应用ID")
    app_secret = db.Column(db.String(255), comment="应用密钥（AES加密存储）")
    access_token = db.Column(db.String(500), comment="授权令牌（AES加密存储）")
    general_trade_route = db.Column(db.String(255), comment="通用交易路由")
    game_card_route = db.Column(db.String(255), comment="点卡路由")
    is_enabled = db.Column(db.SmallInteger, default=0, comment="启用开关：0=禁用, 1=启用")

    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    update_time = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    __table_args__ = ({"comment": "阿奇索开放平台配置表"},)

    def __repr__(self):
        return f"<AgisoConfig 商户={self.merchant_id}>"
