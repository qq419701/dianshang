# -*- coding: utf-8 -*-
"""
==============================================
  应用入口文件
  功能：创建并启动 Flask 应用
  使用方式：python run.py
==============================================
"""

import os
from app import create_app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
