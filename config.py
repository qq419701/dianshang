# -*- coding: utf-8 -*-
"""
==============================================
  应用配置模块
  功能：加载环境变量，初始化数据库及Flask应用配置
==============================================
"""

import os
from dotenv import load_dotenv

# 加载 .env 环境变量文件
load_dotenv()


class Config:
    """Flask 应用配置类"""

    # Flask 密钥
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")

    # 数据库配置
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "dianshang")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    # SQLAlchemy 数据库连接字符串
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 系统 AES 密钥（用于加密存储敏感数据，必须32字节）
    SYSTEM_AES_KEY = os.getenv("SYSTEM_AES_KEY", "01234567890123456789012345678901")
    
    # 邮件配置（用于通知系统）
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")
