# 腾讯云 DDNS

腾讯云 DNSPod 动态域名解析（DDNS）脚本，支持自动更新子域名解析记录，内置后台调度器，无需 crontab。

## 一键安装

支持 **CLI 版**（命令行）和 **Web 版**（图形界面）两种安装方式：

```bash
# 安装（交互式引导，选 CLI 或 Web）
sudo bash <(curl -s https://raw.githubusercontent.com/billkit/tencent_ddns/main/install.sh)

# 卸载
sudo bash <(curl -s https://raw.githubusercontent.com/billkit/tencent_ddns/main/install.sh) uninstall
```

安装后访问：

- **Web 版** → `http://<服务器IP>:8877`
- **CLI 版** → `python3 /opt/tencent_ddns/tencent_ddns.py`

---

## 版本说明

| 版本 | 说明 |
|------|------|
| **CLI 版** | 命令行脚本，轻量级，交互式引导配置，crontab 定时 |
| **Web 版** | 图形化管理界面，支持配置管理、实时查询、日志查看、内置调度器 |

## 功能对比

| 功能 | CLI 版 | Web 版 |
|------|--------|--------|
| 配置管理 | 交互式引导 | 可视化界面 |
| 实时查询 | 手动执行 | ✅ |
| 日志查看 | ❌ | ✅ |
| 内置定时调度 | crontab（需手动配置） | ✅ 每 N 分钟自动对比 IP 并更新 |
| Web 管理界面 | ❌ | ✅ |

---

## 手动安装

### CLI 版

```bash
git clone https://github.com/billkit/tencent_ddns.git
cd tencent_ddns
python3 tencent_ddns.py
```

### Web 版

```bash
git clone https://github.com/billkit/tencent_ddns.git
cd tencent_ddns/DDNS_web
pip install -r requirements.txt
python3 app.py --port 8877
```

访问 **http://0.0.0.0:8877**

---

## 配置说明

编辑 `tencent_ddns.py` 或在 Web 界面中配置：

```python
SECRET_ID = ""        # 腾讯云 SecretId（必填）
SECRET_KEY = ""       # 腾讯云 SecretKey（必填）
TOKEN = ""            # 临时密钥（可选）
DOMAIN = "example.com"  # 主域名（必填）
SUBDOMAIN = "home"      # 子域名（必填）
RECORD_TYPE = "A"       # 解析记录类型
RECORD_LINE = "默认"    # 解析线路
```

> 获取腾讯云密钥：[腾讯云控制台 → 访问密钥](https://console.cloud.tencent.com/cam/capi)

---

## 其他资源

- 腾讯云 DNSPod API 文档：https://cloud.tencent.com/document/api/1427
- DNSPod API 文档：https://dnsapi.cn/#interface