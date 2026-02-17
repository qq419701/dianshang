# -*- coding: utf-8 -*-
"""
==============================================
  单元测试 — 签名工具和加密工具
  测试范围：
    1. 京东通用交易 MD5 签名
    2. 京东游戏点卡 MD5 签名
    3. 阿奇索 MD5 签名
    4. AES 加密/解密
    5. Base64 编解码（UTF-8 和 GBK）
==============================================
"""

import unittest
from app.utils.sign import (
    jd_general_sign,
    jd_game_sign,
    agiso_sign,
    verify_jd_general_sign,
    verify_jd_game_sign,
)
from app.utils.crypto import (
    aes_encrypt,
    aes_decrypt,
    base64_encode_utf8,
    base64_decode_utf8,
    base64_encode_gbk,
    base64_decode_gbk,
)


class TestJdGeneralSign(unittest.TestCase):
    """京东通用交易平台签名测试"""

    def test_sign_basic(self):
        """测试基本签名计算"""
        params = {
            "jdOrderNo": "10001",
            "timestamp": "20210207170426",
        }
        private_key = "abc123"
        sign = jd_general_sign(params, private_key)

        # 验证返回值为32位小写hex
        self.assertEqual(len(sign), 32)
        self.assertEqual(sign, sign.lower())

    def test_sign_excludes_sign_and_signtype(self):
        """测试签名排除 sign 和 signType 参数"""
        params1 = {"jdOrderNo": "10001", "timestamp": "20210207170426"}
        params2 = {
            "jdOrderNo": "10001",
            "timestamp": "20210207170426",
            "sign": "oldsign",
            "signType": "MD5",
        }
        private_key = "abc123"

        # 排除 sign/signType 后签名应该一致
        self.assertEqual(
            jd_general_sign(params1, private_key),
            jd_general_sign(params2, private_key),
        )

    def test_sign_key_order(self):
        """测试参数按key字母升序排列"""
        params1 = {"b": "2", "a": "1"}
        params2 = {"a": "1", "b": "2"}
        private_key = "key"

        # 无论传入顺序如何，签名应该一致
        self.assertEqual(
            jd_general_sign(params1, private_key),
            jd_general_sign(params2, private_key),
        )

    def test_verify_sign(self):
        """测试签名验证"""
        params = {"jdOrderNo": "10001", "timestamp": "20210207170426"}
        private_key = "abc123"

        # 计算签名
        sign = jd_general_sign(params, private_key)
        params["sign"] = sign
        params["signType"] = "MD5"

        # 验证应通过
        self.assertTrue(verify_jd_general_sign(params, private_key))

        # 篡改签名应失败
        params["sign"] = "invalidsign"
        self.assertFalse(verify_jd_general_sign(params, private_key))


class TestJdGameSign(unittest.TestCase):
    """京东游戏点卡平台签名测试"""

    def test_sign_basic(self):
        """测试基本签名计算"""
        params = {
            "customerId": "10817",
            "data": "eyJ0ZXN0IjogMX0=",
            "timestamp": "20120424165458",
        }
        private_key = "testkey"
        sign = jd_game_sign(params, private_key)

        # 验证返回值为32位小写hex
        self.assertEqual(len(sign), 32)
        self.assertEqual(sign, sign.lower())

    def test_sign_excludes_empty_values(self):
        """测试排除空值参数"""
        params1 = {"customerId": "10817", "timestamp": "20120424165458"}
        params2 = {
            "customerId": "10817",
            "timestamp": "20120424165458",
            "version": "",
        }
        private_key = "testkey"

        # 排除空值后签名应该一致
        self.assertEqual(
            jd_game_sign(params1, private_key),
            jd_game_sign(params2, private_key),
        )

    def test_verify_sign(self):
        """测试签名验证"""
        params = {
            "customerId": "10817",
            "data": "eyJ0ZXN0IjogMX0=",
            "timestamp": "20120424165458",
        }
        private_key = "testkey"

        sign = jd_game_sign(params, private_key)
        params["sign"] = sign

        self.assertTrue(verify_jd_game_sign(params, private_key))


class TestAgisoSign(unittest.TestCase):
    """阿奇索开放平台签名测试"""

    def test_sign_basic(self):
        """测试基本签名计算"""
        params = {
            "appId": "123456",
            "method": "order.pull",
            "timestamp": "20210207170426",
        }
        app_secret = "mysecret"
        sign = agiso_sign(params, app_secret)

        # 验证返回值为32位大写hex
        self.assertEqual(len(sign), 32)
        self.assertEqual(sign, sign.upper())

    def test_sign_format(self):
        """测试签名拼接格式（AppSecret + keyvalue + AppSecret）"""
        params = {"b": "2", "a": "1"}
        app_secret = "secret"
        sign = agiso_sign(params, app_secret)

        # 验证是大写hex
        self.assertTrue(all(c in "0123456789ABCDEF" for c in sign))

    def test_sign_excludes_sign(self):
        """测试排除 sign 参数"""
        params1 = {"appId": "123", "timestamp": "20210101"}
        params2 = {"appId": "123", "timestamp": "20210101", "sign": "oldsign"}
        app_secret = "secret"

        self.assertEqual(
            agiso_sign(params1, app_secret),
            agiso_sign(params2, app_secret),
        )


class TestAesCrypto(unittest.TestCase):
    """AES 加密/解密测试"""

    def test_encrypt_decrypt(self):
        """测试AES加密后解密应还原明文"""
        key = "12345678901234567890123456789012"  # 32字节密钥
        plaintext = '[{"cardNumber":"123456","password":"654321"}]'

        encrypted = aes_encrypt(plaintext, key)
        decrypted = aes_decrypt(encrypted, key)

        self.assertEqual(decrypted, plaintext)

    def test_encrypt_not_plaintext(self):
        """测试加密后的密文不等于明文"""
        key = "12345678901234567890123456789012"
        plaintext = "hello world"

        encrypted = aes_encrypt(plaintext, key)
        self.assertNotEqual(encrypted, plaintext)

    def test_chinese_encrypt_decrypt(self):
        """测试中文内容加密解密"""
        key = "12345678901234567890123456789012"
        plaintext = '{"卡号":"123456","密码":"654321"}'

        encrypted = aes_encrypt(plaintext, key)
        decrypted = aes_decrypt(encrypted, key)

        self.assertEqual(decrypted, plaintext)


class TestBase64Codec(unittest.TestCase):
    """Base64 编解码测试"""

    def test_utf8_encode_decode(self):
        """测试UTF-8 Base64编解码"""
        original = '{"orderId": "1000005565"}'
        encoded = base64_encode_utf8(original)
        decoded = base64_decode_utf8(encoded)

        self.assertEqual(decoded, original)

    def test_gbk_encode_decode(self):
        """测试GBK Base64编解码（游戏点卡回调专用）"""
        original = '{"orderId": 123, "orderStatus": 0}'
        encoded = base64_encode_gbk(original)
        decoded = base64_decode_gbk(encoded)

        self.assertEqual(decoded, original)

    def test_gbk_chinese_encode_decode(self):
        """测试GBK编码的中文内容"""
        original = '{"failedReason": "充值失败"}'
        encoded = base64_encode_gbk(original)
        decoded = base64_decode_gbk(encoded)

        self.assertEqual(decoded, original)


if __name__ == "__main__":
    unittest.main()
