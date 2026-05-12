#!/bin/bash
#
# 腾讯云 DDNS 一键安装脚本
# 安装目录: /opt/tencent_ddns
#

set -euo pipefail

INSTALL_DIR="/opt/tencent_ddns"
REPO_URL="https://github.com/billkit/tencent_ddns.git"
TEMP_DIR=$(mktemp -d)

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

cleanup() { rm -rf "$TEMP_DIR"; }
trap cleanup EXIT

# ============================
# 前置检查
# ============================
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "请使用 root 权限运行此脚本"
        echo "用法: sudo bash install.sh"
        exit 1
    fi
}

check_python() {
    if ! command -v python3 &>/dev/null; then
        error "未找到 python3，请先安装"
        exit 1
    fi
    info "Python: $(python3 --version)"
}

check_git() {
    if ! command -v git &>/dev/null; then
        warn "未找到 git，正在安装..."
        if command -v apt-get &>/dev/null; then
            apt-get update && apt-get install -y git
        elif command -v yum &>/dev/null; then
            yum install -y git
        elif command -v apk &>/dev/null; then
            apk add git
        else
            error "无法自动安装 git，请手动安装后重试"
            exit 1
        fi
        ok "git 安装完成"
    fi
}

# ============================
# 安装 CLI 版
# ============================
install_cli() {
    info "开始安装 CLI 版本..."

    mkdir -p "$INSTALL_DIR"
    cp "$TEMP_DIR/tencent_ddns/tencent_ddns.py" "$INSTALL_DIR/ddns.py"
    chmod +x "$INSTALL_DIR/ddns.py"

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}  配置腾讯云 DDNS（CLI 版本）${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo ""

    read -rp "请输入 SecretId: " SECRET_ID
    read -rsp "请输入 SecretKey: " SECRET_KEY; echo
    read -rp "请输入临时 Token (可选，直接回车跳过): " TOKEN
    read -rp "请输入主域名 (如 example.com): " DOMAIN
    read -rp "请输入子域名 (如 home，留空为 @): " SUBDOMAIN
    [ -z "$SUBDOMAIN" ] && SUBDOMAIN="@"
    read -rp "请输入记录类型 [A/AAAA] (默认 A): " RECORD_TYPE
    [ -z "$RECORD_TYPE" ] && RECORD_TYPE="A"
    read -rp "请输入解析线路 [默认/电信/联通/移动] (默认 默认): " RECORD_LINE
    [ -z "$RECORD_LINE" ] && RECORD_LINE="默认"

    # 写入配置文件
    cat > "$INSTALL_DIR/config.json" <<EOF
{
    "SECRET_ID": "$SECRET_ID",
    "SECRET_KEY": "$SECRET_KEY",
    "TOKEN": "$TOKEN",
    "DOMAIN": "$DOMAIN",
    "SUBDOMAIN": "$SUBDOMAIN",
    "RECORD_TYPE": "$RECORD_TYPE",
    "RECORD_LINE": "$RECORD_LINE",
    "LOG_FILE": "/var/log/tencent_ddns.log",
    "REGION": "ap-guangzhou"
}
EOF

    chmod 600 "$INSTALL_DIR/config.json"
    ok "配置文件已写入: $INSTALL_DIR/config.json"

    # 安装 Python 依赖
    info "安装 Python 依赖..."
    pip3 install requests tencentcloud-sdk-python -q 2>/dev/null || \
        pip3 install requests tencentcloud-sdk-python --break-system-packages -q 2>/dev/null
    ok "依赖安装完成"

    # 测试运行
    echo ""
    info "正在测试 DDNS 更新..."
    if python3 "$INSTALL_DIR/ddns.py"; then
        ok "测试成功！"
    else
        warn "测试失败，请检查配置和网络"
    fi

    # 定时任务设置
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}  设置定时任务${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo ""
    echo "请选择执行间隔："
    echo "  1) 每 5 分钟 (推荐)"
    echo "  2) 每 10 分钟"
    echo "  3) 每 30 分钟"
    echo "  4) 每小时"
    echo "  5) 不设置 (手动执行)"
    read -rp "请输入选项 [1-5] (默认 1): " CRON_CHOICE

    case "$CRON_CHOICE" in
        2) INTERVAL="*/10" ;;
        3) INTERVAL="*/30" ;;
        4) INTERVAL="0" ;;
        5) INTERVAL="" ;;
        *) INTERVAL="*/5" ;;
    esac

    if [ -n "$INTERVAL" ]; then
        # 写入 crontab
        CRON_CMD="$INTERVAL * * * * /usr/bin/python3 $INSTALL_DIR/ddns.py >> /var/log/tencent_ddns.log 2>&1"

        # 先清理旧的 DDNS crontab
        (crontab -l 2>/dev/null | grep -v "tencent_ddns\|ddns.py" || true) | crontab -
        # 添加新的
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

        ok "定时任务已设置: $CRON_CMD"
        echo ""
        info "可用命令:"
        echo "  查看日志: tail -f /var/log/tencent_ddns.log"
        echo "  手动执行: python3 $INSTALL_DIR/ddns.py"
        echo "  查看定时: crontab -l"
    else
        info "未设置定时任务，可手动执行: python3 $INSTALL_DIR/ddns.py"
    fi

    echo ""
    ok "CLI 版本安装完成！"
}

# ============================
# 安装 Web 版
# ============================
install_web() {
    info "开始安装 Web 版本..."

    mkdir -p "$INSTALL_DIR"
    cp -r "$TEMP_DIR/tencent_ddns/DDNS_web"/* "$INSTALL_DIR/"

    chmod +x "$INSTALL_DIR/app.py"

    ok "文件已复制到: $INSTALL_DIR"

    # 安装依赖
    info "安装 Python 依赖..."
    pip3 install -r "$INSTALL_DIR/requirements.txt" -q 2>/dev/null || \
        pip3 install -r "$INSTALL_DIR/requirements.txt" --break-system-packages -q 2>/dev/null
    ok "依赖安装完成"

    # 创建 systemd 服务
    info "创建 systemd 服务..."

    cat > /etc/systemd/system/tencent-ddns-web.service <<'EOF'
[Unit]
Description=Tencent Cloud DDNS Web Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tencent_ddns
ExecStart=/usr/bin/python3 /opt/tencent_ddns/app.py --port 8877
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable tencent-ddns-web.service
    systemctl start tencent-ddns-web.service

    ok "systemd 服务已启用并启动"

    # 检查服务状态
    sleep 2
    if systemctl is-active --quiet tencent-ddns-web.service; then
        ok "Web 服务运行正常"
    else
        warn "服务未正常运行，请检查: systemctl status tencent-ddns-web.service"
    fi

    echo ""
    ok "Web 版本安装完成！"
    echo ""
    info "访问地址: http://<你的IP>:8877"
    info "请在浏览器中打开上述地址，完成 API 密钥和域名配置"
    echo ""
    info "管理命令:"
    echo "  查看状态: systemctl status tencent-ddns-web.service"
    echo "  重启服务: systemctl restart tencent-ddns-web.service"
    echo "  查看日志: journalctl -u tencent-ddns-web.service -f"
    echo "  停止服务: systemctl stop tencent-ddns-web.service"
}

# ============================
# 主流程
# ============================
main() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   腾讯云 DDNS 一键安装脚本 v1.0          ║${NC}"
    echo -e "${CYAN}║   安装目录: $INSTALL_DIR                 ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
    echo ""

    check_root
    check_python
    check_git

    # 克隆仓库到临时目录
    info "正在克隆仓库..."
    git clone --depth 1 "$REPO_URL" "$TEMP_DIR/tencent_ddns" 2>/dev/null
    ok "仓库克隆完成"

    echo ""
    echo "请选择安装类型："
    echo "  1) CLI 版本 (命令行脚本 + crontab 定时)"
    echo "  2) Web 版本 (Web 管理界面 + systemd 服务)"
    echo "  3) 卸载"
    echo ""
    read -rp "请输入选项 [1-3] (默认 1): " CHOICE

    case "$CHOICE" in
        2) install_web ;;
        3)
            if [ -d "$INSTALL_DIR" ]; then
                systemctl stop tencent-ddns-web.service 2>/dev/null || true
                systemctl disable tencent-ddns-web.service 2>/dev/null || true
                rm -f /etc/systemd/system/tencent-ddns-web.service
                systemctl daemon-reload
                # 清理 crontab
                (crontab -l 2>/dev/null | grep -v "tencent_ddns\|ddns.py" || true) | crontab -
                rm -rf "$INSTALL_DIR"
                ok "已卸载 $INSTALL_DIR"
            else
                warn "未找到安装目录"
            fi
            ;;
        *) install_cli ;;
    esac

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}  安装完成！${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo ""
}

main "$@"
