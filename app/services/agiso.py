"""阿奇索开放平台接口服务。

实现阿奇索开放平台的API调用，用于京东订单自动发货。
参考阿奇索开放平台接口文档：https://open.agiso.com/document/#/aldsJd/guide

接入流程：
1. 在阿奇索开放平台创建应用，获取AppID和AppSecret
2. 商家授权后获取AccessToken
3. 调用自动发货接口

认证方式：
- HTTP Header: Authorization: Bearer {access_token}
- HTTP Header: ApiVersion: 1
- 请求签名：所有参数按ASCII排序拼接，前后加AppSecret，MD5摘要
"""
import hashlib
import json
import logging
import requests

logger = logging.getLogger(__name__)


def generate_agiso_sign(params, app_secret):
    """生成阿奇索开放平台API签名。

    签名规则：
    1. 将所有请求参数按参数名ASCII升序排列
    2. 拼接为 key1value1key2value2... 格式
    3. 在拼接字符串前后各加上AppSecret
    4. 对整个字符串做MD5摘要（小写32位）

    Args:
        params: 请求参数字典
        app_secret: 应用密钥

    Returns:
        str: MD5签名（小写）
    """
    sorted_keys = sorted(params.keys())
    param_str = ''.join(f'{k}{params[k]}' for k in sorted_keys if params[k] is not None)
    sign_str = f'{app_secret}{param_str}{app_secret}'
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()


def _build_agiso_url(shop):
    """构建阿奇索API基础URL。

    Args:
        shop: 店铺对象

    Returns:
        str: API基础URL
    """
    host = shop.agiso_host or 'open.agiso.com'
    port = shop.agiso_port
    if port and port not in (80, 443):
        return f'https://{host}:{port}'
    return f'https://{host}'


def _build_headers(shop):
    """构建阿奇索API请求头。

    Args:
        shop: 店铺对象

    Returns:
        dict: HTTP请求头
    """
    headers = {
        'Content-Type': 'application/json',
        'ApiVersion': '1',
    }
    if shop.agiso_access_token:
        headers['Authorization'] = f'Bearer {shop.agiso_access_token}'
    return headers


def agiso_auto_deliver(shop, order):
    """调用阿奇索开放平台自动发货接口。

    根据订单类型（直充/卡密）调用对应的发货接口。

    Args:
        shop: 店铺对象（需包含阿奇索配置信息）
        order: 订单对象

    Returns:
        (bool, str, dict|None): (是否成功, 消息, 返回数据)
    """
    if not shop.agiso_enabled:
        return False, '未启用阿奇索自动发货', None

    if not shop.agiso_app_id or not shop.agiso_app_secret:
        return False, '阿奇索应用配置不完整', None

    if not shop.agiso_access_token:
        return False, '未配置阿奇索访问令牌', None

    base_url = _build_agiso_url(shop)
    headers = _build_headers(shop)

    # 构建发货请求参数
    params = {
        'appId': shop.agiso_app_id,
        'jdOrderId': order.jd_order_no,
        'orderId': order.order_no,
        'skuId': order.sku_id or '',
        'quantity': str(order.quantity),
    }

    # 直充订单需要充值账号
    if order.order_type == 1 and order.produce_account:
        params['chargeAccount'] = order.produce_account

    # 生成签名
    params['sign'] = generate_agiso_sign(params, shop.agiso_app_secret)

    api_url = f'{base_url}/api/jd/order/deliver'

    try:
        resp = requests.post(api_url, json=params, headers=headers, timeout=30)
        result = resp.json()

        if result.get('code') == 0 or result.get('success'):
            data = result.get('data', {})
            return True, '阿奇索发货成功', data
        else:
            error_msg = result.get('message') or result.get('msg') or '发货失败'
            return False, f'阿奇索发货失败：{error_msg}', result

    except requests.exceptions.Timeout:
        logger.exception("阿奇索接口调用超时")
        return False, '阿奇索接口调用超时', None
    except requests.exceptions.ConnectionError:
        logger.exception("阿奇索接口连接失败")
        return False, '阿奇索接口连接失败，请检查主机地址和端口配置', None
    except Exception as e:
        logger.exception("阿奇索接口调用异常")
        return False, f'阿奇索接口调用异常：{str(e)}', None


def agiso_query_order(shop, jd_order_no):
    """查询阿奇索平台订单状态。

    Args:
        shop: 店铺对象
        jd_order_no: 京东订单号

    Returns:
        (bool, str, dict|None): (是否成功, 消息, 返回数据)
    """
    if not shop.agiso_enabled:
        return False, '未启用阿奇索', None

    if not shop.agiso_app_id or not shop.agiso_app_secret:
        return False, '阿奇索应用配置不完整', None

    base_url = _build_agiso_url(shop)
    headers = _build_headers(shop)

    params = {
        'appId': shop.agiso_app_id,
        'jdOrderId': jd_order_no,
    }

    params['sign'] = generate_agiso_sign(params, shop.agiso_app_secret)

    api_url = f'{base_url}/api/jd/order/query'

    try:
        resp = requests.post(api_url, json=params, headers=headers, timeout=10)
        result = resp.json()

        if result.get('code') == 0 or result.get('success'):
            return True, '查询成功', result.get('data', {})
        else:
            error_msg = result.get('message') or result.get('msg') or '查询失败'
            return False, error_msg, None
    except Exception as e:
        logger.exception("阿奇索订单查询异常")
        return False, str(e), None
