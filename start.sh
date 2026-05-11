#!/bin/bash
# 腾讯云 DDNS Web 界面启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="/var/log/tencent_ddns.log"

echo "☁️  腾讯云 DDNS 管理界面"
echo "========================"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

# 检查依赖（缺少则安装）
python3 -c "import flask, requests, tencentcloud" 2>/dev/null || {
    echo "📦 正在安装依赖..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
}

# 启动
echo "🌐 启动中... 访问 http://0.0.0.0:8877"
python3 "$SCRIPT_DIR/app.py" "$@"