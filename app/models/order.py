# -*- coding: utf-8 -*-
"""
==============================================
  订单模型
  功能：存储京东通用交易和游戏点卡的订单数据
  对应数据库表：orders
==============================================
"""

from app import db
from datetime import datetime


class Order(db.Model):
    """
    订单主表
    存储所有来自京东平台的订单信息（通用交易 + 游戏点卡）
    """
    __tablename__ = "orders"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    merchant_id = db.Column(db.BigInteger, nullable=False, comment="商户ID")
    shop_id = db.Column(db.BigInteger, db.ForeignKey("shops.id"), comment="店铺ID")
    biz_type = db.Column(db.SmallInteger, nullable=False, comment="业务类型：1=通用交易, 2=游戏点卡")
    order_no = db.Column(db.String(64), nullable=False, comment="我方订单号")
    jd_order_no = db.Column(db.String(64), nullable=False, comment="京东订单号")

    order_status = db.Column(db.SmallInteger, nullable=False, comment="订单状态")
    operation_mode = db.Column(db.SmallInteger, default=0, comment="操作方式：0=自动, 1=手动")

    amount = db.Column(db.BigInteger, comment="订单金额（单位：分）")
    quantity = db.Column(db.Integer, comment="数量")
    sku_id = db.Column(db.String(64), comment="商品SKU")
    ware_no = db.Column(db.String(64), comment="商品编码")
    produce_account = db.Column(db.String(255), comment="充值账号")
    product_info = db.Column(db.Text, comment="卡密信息（AES加密存储）")
    notify_url = db.Column(db.String(500), comment="回调地址")
    pay_time = db.Column(db.DateTime, comment="支付时间")

    # 通知记录
    notified = db.Column(db.SmallInteger, default=0, comment="是否已发送通知：0=否 1=是")
    notify_send_time = db.Column(db.DateTime, comment="通知发送时间")

    remark = db.Column(db.String(500), comment="备注")

    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")
    update_time = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关联关系
    shop = db.relationship("Shop", backref=db.backref("orders", lazy="dynamic"))

    # 唯一约束：京东订单号 + 业务类型
    __table_args__ = (
        db.UniqueConstraint("jd_order_no", "biz_type", name="uk_jd_order_biz"),
        db.Index("idx_shop_id", "shop_id"),
        {"comment": "订单主表"},
    )

    def __repr__(self):
        return f"<Order 订单号={self.order_no} 京东订单={self.jd_order_no} 状态={self.order_status}>"
