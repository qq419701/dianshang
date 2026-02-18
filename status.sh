#!/bin/bash
echo "📊 应用运行状态："
ps aux | grep "gunicorn.*run:app" | grep -v grep
echo ""
echo "📡 端口监听状态："
lsof -i :5000 2>/dev/null || echo "端口 5000 未被监听"
