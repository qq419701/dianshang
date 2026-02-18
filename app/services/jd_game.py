"""京东游戏点卡平台接口服务。

实现京东游戏点卡平台的签名验证、订单接收和回调通知功能。
参考京东游戏点卡平台接口文档。
"""
import hashlib
import json
import logging
import requests

logger = logging.getLogger(__name__)


def verify_game_sign(params, md5_secret):
    """验证京东游戏点卡平台请求的MD5签名。

    签名规则：将所有请求参数（除sign外）按参数名ASCII升序排列，
    拼接为 key1=value1&key2=value2&...&key=md5_secret 格式，
    然后对该字符串做MD5摘要（小写）。

    Args:
        params: 请求参数字典
        md5_secret: MD5密钥

    Returns:
        bool: 签名是否有效
    """
    if not md5_secret:
        return True  # 未配置密钥时跳过验签

    received_sign = params.get('sign', '')
    if not received_sign:
        return False

    # 过滤掉sign参数，其余按key升序排列
    filtered = {k: v for k, v in params.items() if k != 'sign' and v is not None and v != ''}
    sorted_keys = sorted(filtered.keys())
    sign_str = '&'.join(f'{k}={filtered[k]}' for k in sorted_keys)
    sign_str += f'&key={md5_secret}'

    computed_sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
    return computed_sign == received_sign.lower()


def generate_game_sign(params, md5_secret):
    """生成京东游戏点卡平台的MD5签名。

    Args:
        params: 请求参数字典（不含sign字段）
        md5_secret: MD5密钥

    Returns:
        str: MD5签名（小写）
    """
    filtered = {k: v for k, v in params.items() if v is not None and v != ''}
    sorted_keys = sorted(filtered.keys())
    sign_str = '&'.join(f'{k}={filtered[k]}' for k in sorted_keys)
    sign_str += f'&key={md5_secret}'
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()


def callback_game_direct_success(shop, order):
    """向京东游戏点卡平台回调直充成功通知。

    Args:
        shop: 店铺对象
        order: 订单对象

    Returns:
        (bool, str): (是否成功, 消息)
    """
    callback_url = shop.game_direct_callback_url
    if not callback_url:
        return False, '未配置游戏直充回调地址'

    params = {
        'jdOrderId': order.jd_order_no,
        'orderId': order.order_no,
        'status': 'SUCCESS',
        'message': '充值成功',
    }

    if shop.game_md5_secret:
        params['sign'] = generate_game_sign(params, shop.game_md5_secret)

    try:
        resp = requests.post(callback_url, json=params, timeout=10)
        result = resp.json()
        if result.get('success') or result.get('code') == 0:
            return True, '回调成功'
        return False, result.get('message', '回调失败')
    except Exception as e:
        logger.exception("游戏点卡直充回调失败")
        return False, str(e)


def callback_game_card_deliver(shop, order, cards):
    """向京东游戏点卡平台回调卡密发货信息。

    Args:
        shop: 店铺对象
        order: 订单对象
        cards: 卡密列表 [{"cardNo": "xxx", "cardPwd": "xxx"}, ...]

    Returns:
        (bool, str): (是否成功, 消息)
    """
    callback_url = shop.game_card_callback_url
    if not callback_url:
        return False, '未配置游戏卡密回调地址'

    params = {
        'jdOrderId': order.jd_order_no,
        'orderId': order.order_no,
        'cards': json.dumps(cards, ensure_ascii=False),
    }

    if shop.game_md5_secret:
        sign_params = {
            'jdOrderId': order.jd_order_no,
            'orderId': order.order_no,
        }
        params['sign'] = generate_game_sign(sign_params, shop.game_md5_secret)

    try:
        resp = requests.post(callback_url, json=params, timeout=10)
        result = resp.json()
        if result.get('success') or result.get('code') == 0:
            return True, '卡密回调成功'
        return False, result.get('message', '卡密回调失败')
    except Exception as e:
        logger.exception("游戏点卡卡密回调失败")
        return False, str(e)


def callback_game_refund(shop, order):
    """向京东游戏点卡平台回调退款通知。

    Args:
        shop: 店铺对象
        order: 订单对象

    Returns:
        (bool, str): (是否成功, 消息)
    """
    callback_url = shop.game_direct_callback_url
    if not callback_url:
        return False, '未配置回调地址'

    params = {
        'jdOrderId': order.jd_order_no,
        'orderId': order.order_no,
        'status': 'REFUND',
        'message': '退款',
    }

    if shop.game_md5_secret:
        params['sign'] = generate_game_sign(params, shop.game_md5_secret)

    try:
        resp = requests.post(callback_url, json=params, timeout=10)
        result = resp.json()
        if result.get('success') or result.get('code') == 0:
            return True, '退款回调成功'
        return False, result.get('message', '退款回调失败')
    except Exception as e:
        logger.exception("游戏点卡退款回调失败")
        return False, str(e)
