# -*- coding: utf-8 -*-
"""
==============================================
  店铺服务
  功能：店铺管理CRUD操作
==============================================
"""

import logging
from app import db
from app.models.shop import Shop
from app.models.merchant import Merchant
from app.models.order import Order
from app.utils.crypto import system_aes_encrypt, system_aes_decrypt

logger = logging.getLogger(__name__)


def get_shop_by_id(shop_id):
    """
    根据ID获取店铺
    
    参数：
        shop_id: 店铺ID
    
    返回：
        Shop对象或None
    """
    return Shop.query.get(shop_id)


def get_shops_by_merchant(merchant_id, biz_type=None):
    """
    获取商户下的所有店铺
    
    参数：
        merchant_id: 商户ID
        biz_type: 业务类型筛选（可选）
    
    返回：
        Shop对象列表
    """
    query = Shop.query.filter_by(merchant_id=merchant_id)
    if biz_type:
        query = query.filter_by(biz_type=biz_type)
    return query.order_by(Shop.create_time.desc()).all()


def create_shop(merchant_id, shop_name, shop_code, biz_type, **config):
    """
    创建店铺
    
    参数：
        merchant_id: 商户ID
        shop_name: 店铺名称
        shop_code: 店铺编码
        biz_type: 业务类型（1=通用交易, 2=游戏点卡）
        **config: 其他配置参数
    
    返回：
        (success: bool, message: str, shop: Shop)
    """
    try:
        # 验证商户是否存在
        merchant = Merchant.query.get(merchant_id)
        if not merchant:
            return False, "商户不存在", None

        # 检查店铺编码是否重复
        if shop_code:
            existing = Shop.query.filter_by(
                merchant_id=merchant_id, 
                shop_code=shop_code
            ).first()
            if existing:
                return False, "店铺编码已存在", None

        # 创建店铺
        shop = Shop(
            merchant_id=merchant_id,
            shop_name=shop_name,
            shop_code=shop_code,
            biz_type=biz_type,
            is_enabled=config.get('is_enabled', 1),
            remark=config.get('remark', '')
        )

        # 设置业务类型相关字段
        if biz_type == 1:
            # 通用交易
            shop.vendor_id = config.get('vendor_id')
            shop.jd_callback_url = config.get('jd_callback_url', '')
        elif biz_type == 2:
            # 游戏点卡
            shop.customer_id = config.get('customer_id')
            shop.jd_direct_callback_url = config.get('jd_direct_callback_url', '')
            shop.jd_card_callback_url = config.get('jd_card_callback_url', '')

        # 设置公共字段
        shop.our_api_url = config.get('our_api_url', '')
        
        # 加密存储密钥
        if config.get('md5_secret'):
            shop.md5_secret = system_aes_encrypt(config['md5_secret'])
        if config.get('aes_secret'):
            shop.aes_secret = system_aes_encrypt(config['aes_secret'])

        db.session.add(shop)
        db.session.commit()

        logger.info(f"创建店铺成功：{shop_name} (ID={shop.id})")
        return True, "创建成功", shop

    except Exception as e:
        db.session.rollback()
        logger.exception("创建店铺失败")
        return False, f"创建失败：{str(e)}", None


def update_shop(shop_id, **updates):
    """
    更新店铺信息
    
    参数：
        shop_id: 店铺ID
        **updates: 要更新的字段
    
    返回：
        (success: bool, message: str)
    """
    try:
        shop = Shop.query.get(shop_id)
        if not shop:
            return False, "店铺不存在"

        # 更新基本信息
        if 'shop_name' in updates:
            shop.shop_name = updates['shop_name']
        if 'shop_code' in updates:
            # 检查新编码是否重复
            if updates['shop_code'] != shop.shop_code:
                existing = Shop.query.filter_by(
                    merchant_id=shop.merchant_id,
                    shop_code=updates['shop_code']
                ).first()
                if existing:
                    return False, "店铺编码已存在"
                shop.shop_code = updates['shop_code']
        if 'is_enabled' in updates:
            shop.is_enabled = updates['is_enabled']
        if 'remark' in updates:
            shop.remark = updates['remark']

        # 业务类型相关配置
        if shop.biz_type == 1:
            if 'vendor_id' in updates:
                vendor_id_val = updates['vendor_id']
                shop.vendor_id = int(vendor_id_val) if vendor_id_val and vendor_id_val != '' else None
            if 'jd_callback_url' in updates:
                shop.jd_callback_url = updates['jd_callback_url']
        elif shop.biz_type == 2:
            if 'customer_id' in updates:
                customer_id_val = updates['customer_id']
                shop.customer_id = int(customer_id_val) if customer_id_val and customer_id_val != '' else None
            if 'jd_direct_callback_url' in updates:
                shop.jd_direct_callback_url = updates['jd_direct_callback_url']
            if 'jd_card_callback_url' in updates:
                shop.jd_card_callback_url = updates['jd_card_callback_url']

        if 'our_api_url' in updates:
            shop.our_api_url = updates['our_api_url']

        # 更新密钥（仅当提供新值且不是掩码时）
        if updates.get('md5_secret') and updates['md5_secret'] != '******':
            shop.md5_secret = system_aes_encrypt(updates['md5_secret'])
        if updates.get('aes_secret') and updates['aes_secret'] != '******':
            shop.aes_secret = system_aes_encrypt(updates['aes_secret'])

        db.session.commit()
        logger.info(f"更新店铺成功：{shop.shop_name} (ID={shop_id})")
        return True, "更新成功"

    except Exception as e:
        db.session.rollback()
        logger.exception("更新店铺失败")
        return False, f"更新失败：{str(e)}"


def delete_shop(shop_id, force=False):
    """
    删除店铺（软删除）
    
    参数：
        shop_id: 店铺ID
        force: 是否强制删除（即使有关联订单）
    
    返回：
        (success: bool, message: str)
    """
    try:
        shop = Shop.query.get(shop_id)
        if not shop:
            return False, "店铺不存在"

        # 检查是否有关联订单
        order_count = Order.query.filter_by(shop_id=shop_id).count()
        if order_count > 0 and not force:
            return False, f"该店铺有 {order_count} 个关联订单，无法删除"

        # 软删除：设置为禁用
        shop.is_enabled = 0
        db.session.commit()

        logger.info(f"删除店铺成功：{shop.shop_name} (ID={shop_id})")
        return True, "删除成功"

    except Exception as e:
        db.session.rollback()
        logger.exception("删除店铺失败")
        return False, f"删除失败：{str(e)}"


def get_shop_config_decrypted(shop_id):
    """
    获取店铺配置（密钥解密）
    
    参数：
        shop_id: 店铺ID
    
    返回：
        dict 包含解密后的配置
    """
    shop = Shop.query.get(shop_id)
    if not shop:
        return None

    config = {
        'id': shop.id,
        'merchant_id': shop.merchant_id,
        'shop_name': shop.shop_name,
        'shop_code': shop.shop_code,
        'biz_type': shop.biz_type,
        'is_enabled': shop.is_enabled,
        'remark': shop.remark,
        'our_api_url': shop.our_api_url,
    }

    # 解密密钥
    try:
        if shop.md5_secret:
            config['md5_secret'] = system_aes_decrypt(shop.md5_secret)
        if shop.aes_secret:
            config['aes_secret'] = system_aes_decrypt(shop.aes_secret)
    except Exception as e:
        logger.error(f"解密密钥失败: {e}")
        config['md5_secret'] = None
        config['aes_secret'] = None

    # 业务类型特定字段
    if shop.biz_type == 1:
        config['vendor_id'] = shop.vendor_id
        config['jd_callback_url'] = shop.jd_callback_url
    elif shop.biz_type == 2:
        config['customer_id'] = shop.customer_id
        config['jd_direct_callback_url'] = shop.jd_direct_callback_url
        config['jd_card_callback_url'] = shop.jd_card_callback_url

    return config
