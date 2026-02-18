# -*- coding: utf-8 -*-
"""
==============================================
  店铺模型
  功能：店铺信息管理和配置
  对应数据库表：shops
==============================================
"""

from app import db
from datetime import datetime, timezone


class Shop(db.Model):
    """
    店铺表
    存储商户下的多个店铺及其配置
    """
    __tablename__ = "shops"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="店铺ID")
    merchant_id = db.Column(db.BigInteger, db.ForeignKey("merchants.id"), nullable=False, comment="所属商户ID")
    shop_name = db.Column(db.String(128), nullable=False, comment="店铺名称")
    shop_code = db.Column(db.String(64), comment="店铺编码（自定义标识）")
    biz_type = db.Column(db.SmallInteger, nullable=False, comment="业务类型：1=京东通用交易, 2=京东游戏点卡")

    # 京东通用交易字段
    vendor_id = db.Column(db.BigInteger, comment="京东vendorId")

    # 京东游戏点卡字段
    customer_id = db.Column(db.BigInteger, comment="京东customerId")

    # 公共配置字段 — 密钥使用系统AES加密存储
    md5_secret = db.Column(db.String(255), comment="MD5签名密钥（AES加密）")
    aes_secret = db.Column(db.String(255), comment="AES加密密钥（AES加密）")
    our_api_url = db.Column(db.String(500), comment="我方接口基础地址")
    jd_callback_url = db.Column(db.String(500), comment="京东回调地址")
    jd_direct_callback_url = db.Column(db.String(500), comment="京东直充回调地址")
    jd_card_callback_url = db.Column(db.String(500), comment="京东卡密回调地址")

    is_enabled = db.Column(db.SmallInteger, default=1, comment="启用状态：0=禁用, 1=启用")
    remark = db.Column(db.Text, comment="备注")
    create_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    update_time = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间"
    )

    # 关联关系
    merchant = db.relationship("Merchant", backref=db.backref("shops", lazy="dynamic"))

    # 唯一约束：同一商户的店铺编码不能重复
    __table_args__ = (
        db.UniqueConstraint("merchant_id", "shop_code", name="uk_merchant_shop_code"),
        db.Index("idx_merchant_id", "merchant_id"),
        db.Index("idx_biz_type", "biz_type"),
        {"comment": "店铺配置表"},
    )

    def is_active(self):
        """检查店铺是否启用"""
        return self.is_enabled == 1

    def get_biz_type_name(self):
        """获取业务类型名称"""
        return "京东通用交易" if self.biz_type == 1 else "京东游戏点卡"

    def get_order_count(self):
        """获取订单数量"""
        from app.models.order import Order
        return Order.query.filter_by(shop_id=self.id).count()

    def get_order_statistics(self):
        """获取订单统计信息"""
        from app.models.order import Order
        from sqlalchemy import func
        
        stats = db.session.query(
            func.count(Order.id).label('total'),
            func.sum(db.case((Order.order_status == 0, 1), else_=0)).label('success'),
            func.sum(db.case((Order.order_status == 2, 1), else_=0)).label('failed'),
            func.sum(Order.amount).label('total_amount')
        ).filter(Order.shop_id == self.id).first()
        
        return {
            'total': stats.total or 0,
            'success': stats.success or 0,
            'failed': stats.failed or 0,
            'total_amount': stats.total_amount or 0,
            'success_rate': round(stats.success * 100 / stats.total, 2) if stats.total > 0 else 0
        }

    def check_config_complete(self):
        """检查配置是否完整"""
        if self.biz_type == 1:
            # 通用交易必填项
            return all([
                self.vendor_id,
                self.md5_secret,
                self.aes_secret,
                self.our_api_url,
                self.jd_callback_url
            ])
        elif self.biz_type == 2:
            # 游戏点卡必填项
            return all([
                self.customer_id,
                self.md5_secret,
                self.our_api_url,
                self.jd_direct_callback_url,
                self.jd_card_callback_url
            ])
        return False

    def __repr__(self):
        return f"<Shop {self.shop_name} (商户={self.merchant_id}, 类型={self.biz_type})>"
