# -*- coding: utf-8 -*-
"""
==============================================
  加密工具模块
  功能：
    1. AES-256 ECB 模式加密/解密（京东通用交易卡密加密）
    2. Base64 编解码（京东游戏点卡业务数据编码）
    3. GBK 编码 Base64（京东游戏点卡回调专用）
    4. 系统级 AES 加密/解密（数据库敏感字段加密存储）
==============================================
"""

import base64
import json
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding


# ==============================
#  AES-256 ECB 加密/解密
# ==============================

def aes_encrypt(plaintext: str, key: str) -> str:
    """
    AES-256 ECB 模式加密
    用于京东通用交易平台的卡密信息加密
    参数：
        plaintext — 明文字符串
        key       — 32 字节密钥字符串
    返回：
        Base64 编码的密文字符串
    """
    # 密钥必须为 32 字节
    key_bytes = key.encode("utf-8")[:32].ljust(32, b"\0")

    # PKCS7 填充（等同于 Java 的 PKCS5Padding）
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    # AES-256 ECB 加密
    cipher = Cipher(algorithms.AES(key_bytes), modes.ECB())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()

    # 返回 Base64 编码
    return base64.b64encode(encrypted).decode("utf-8")


def aes_decrypt(ciphertext: str, key: str) -> str:
    """
    AES-256 ECB 模式解密
    用于解密京东通用交易平台的卡密信息
    参数：
        ciphertext — Base64 编码的密文字符串
        key        — 32 字节密钥字符串
    返回：
        解密后的明文字符串
    """
    # 密钥必须为 32 字节
    key_bytes = key.encode("utf-8")[:32].ljust(32, b"\0")

    # Base64 解码
    encrypted = base64.b64decode(ciphertext)

    # AES-256 ECB 解密
    cipher = Cipher(algorithms.AES(key_bytes), modes.ECB())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()

    # 去除 PKCS7 填充
    unpadder = sym_padding.PKCS7(128).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

    return decrypted.decode("utf-8")


# ==============================
#  Base64 编解码（UTF-8）
# ==============================

def base64_encode_utf8(data: str) -> str:
    """
    UTF-8 编码后进行 Base64 编码
    用于京东游戏点卡平台的业务数据编码
    参数：
        data — 原始字符串（通常为 JSON）
    返回：
        Base64 编码后的字符串
    """
    return base64.b64encode(data.encode("utf-8")).decode("utf-8")


def base64_decode_utf8(encoded: str) -> str:
    """
    Base64 解码并以 UTF-8 解读
    用于解码京东游戏点卡平台的业务数据
    参数：
        encoded — Base64 编码的字符串
    返回：
        解码后的原始字符串
    """
    return base64.b64decode(encoded).decode("utf-8")


# ==============================
#  Base64 编解码（GBK — 游戏点卡回调专用）
# ==============================

def base64_encode_gbk(data: str) -> str:
    """
    GBK 编码后进行 Base64 编码
    ⚠️ 仅用于京东游戏点卡回调接口（gameApi.action / cardApi.action）的 data 字段
    参数：
        data — 原始字符串（通常为 JSON）
    返回：
        Base64 编码后的字符串（底层为 GBK 编码）
    """
    return base64.b64encode(data.encode("gbk")).decode("utf-8")


def base64_decode_gbk(encoded: str) -> str:
    """
    Base64 解码并以 GBK 解读
    用于解码京东游戏点卡回调返回的 data 字段
    参数：
        encoded — Base64 编码的字符串
    返回：
        解码后的原始字符串
    """
    return base64.b64decode(encoded).decode("gbk")


# ==============================
#  系统级 AES 加密（数据库敏感字段）
# ==============================

def system_aes_encrypt(plaintext: str) -> str:
    """
    使用系统 AES 密钥加密敏感数据
    用于加密存储密钥、卡密等敏感字段到数据库
    参数：
        plaintext — 需要加密的明文
    返回：
        Base64 编码的密文
    """
    system_key = os.getenv("SYSTEM_AES_KEY", "01234567890123456789012345678901")
    return aes_encrypt(plaintext, system_key)


def system_aes_decrypt(ciphertext: str) -> str:
    """
    使用系统 AES 密钥解密敏感数据
    用于从数据库读取并解密密钥、卡密等敏感字段
    参数：
        ciphertext — Base64 编码的密文
    返回：
        解密后的明文
    """
    system_key = os.getenv("SYSTEM_AES_KEY", "01234567890123456789012345678901")
    return aes_decrypt(ciphertext, system_key)
