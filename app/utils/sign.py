# -*- coding: utf-8 -*-
"""
==============================================
  签名工具模块
  功能：
    1. 京东通用交易 MD5 签名（key=value& 拼接 + PRIVATEKEY，小写hex）
    2. 京东游戏点卡 MD5 签名（key=value& 拼接 + privatekey，小写hex）
    3. 阿奇索开放平台 MD5 签名（keyvalue 拼接，前后加 AppSecret，大写hex）
==============================================
"""

import hashlib


def jd_general_sign(params: dict, private_key: str) -> str:
    """
    京东通用交易平台 — MD5 签名
    步骤：
        1. 排除 sign、signType 参数
        2. 剩余参数按 key 字母升序排序
        3. 拼接为 key1=value1&key2=value2&...&PRIVATEKEY
        4. 对拼接字符串做 MD5，返回 32 位小写 hex
    参数：
        params     — 所有请求参数字典
        private_key — 签名私钥
    返回：
        32 位小写 MD5 签名字符串
    """
    # 排除 sign 和 signType
    filtered = {k: v for k, v in params.items() if k not in ("sign", "signType")}

    # 按 key 字母升序排序
    sorted_keys = sorted(filtered.keys())

    # 拼接为 key=value& 格式
    parts = [f"{k}={filtered[k]}" for k in sorted_keys]
    raw_str = "&".join(parts) + "&" + private_key

    # MD5 计算并返回小写 hex
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest().lower()


def jd_game_sign(params: dict, private_key: str) -> str:
    """
    京东游戏点卡平台 — MD5 签名
    步骤：
        1. 排除 sign 参数及值为空的参数
        2. 剩余参数按 key 字母升序排序
        3. 拼接为 key1=value1&key2=value2&...&privatekey
        4. 对拼接字符串做 MD5，返回 32 位小写 hex
    参数：
        params     — 所有请求参数字典（不含 sign）
        private_key — 签名私钥
    返回：
        32 位小写 MD5 签名字符串
    """
    # 排除 sign 和空值参数
    filtered = {
        k: v for k, v in params.items()
        if k != "sign" and v is not None and str(v) != ""
    }

    # 按 key 字母升序排序
    sorted_keys = sorted(filtered.keys())

    # 拼接为 key=value& 格式，末尾用 & 连接私钥
    parts = [f"{k}={filtered[k]}" for k in sorted_keys]
    parts.append(private_key)
    raw_str = "&".join(parts)

    # MD5 计算并返回小写 hex
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest().lower()


def agiso_sign(params: dict, app_secret: str) -> str:
    """
    阿奇索开放平台 — MD5 签名
    步骤：
        1. 排除 sign 和 byte[] 类型参数
        2. 按参数名 ASCII 升序排列
        3. 将参数名和值直接拼接（无分隔符）：key1value1key2value2...
        4. 在拼接内容前后各加上 AppSecret
        5. 对完整字符串做 MD5，结果转大写
    参数：
        params     — 所有请求参数字典
        app_secret — 应用密钥
    返回：
        32 位大写 MD5 签名字符串
    """
    # 排除 sign 参数
    filtered = {k: v for k, v in params.items() if k != "sign"}

    # 按参数名 ASCII 升序排列
    sorted_keys = sorted(filtered.keys())

    # 参数名和值直接拼接
    joined = "".join(f"{k}{filtered[k]}" for k in sorted_keys)

    # 前后加上 AppSecret
    raw_str = f"{app_secret}{joined}{app_secret}"

    # MD5 计算并返回大写 hex
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest().upper()


def verify_jd_general_sign(params: dict, private_key: str) -> bool:
    """
    验证京东通用交易平台签名
    参数：
        params     — 包含 sign 的请求参数字典
        private_key — 签名私钥
    返回：
        True=签名匹配，False=签名不匹配
    """
    received_sign = params.get("sign", "")
    calculated_sign = jd_general_sign(params, private_key)
    return received_sign.lower() == calculated_sign.lower()


def verify_jd_game_sign(params: dict, private_key: str) -> bool:
    """
    验证京东游戏点卡平台签名
    参数：
        params     — 包含 sign 的请求参数字典
        private_key — 签名私钥
    返回：
        True=签名匹配，False=签名不匹配
    """
    received_sign = params.get("sign", "")
    calculated_sign = jd_game_sign(params, private_key)
    return received_sign.lower() == calculated_sign.lower()
