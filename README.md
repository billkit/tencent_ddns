# 腾讯云 DDNS

腾讯云 DNSPod 动态域名解析（DDNS）脚本，支持自动更新子域名解析记录。

## 版本说明

| 版本 | 路径 | 说明 |
|------|------|------|
| 简易版 | `tencent_ddns.py` | 命令行脚本，轻量级，需手动编辑配置 |
| **Web 版** | `DDNS_web/` | 图形化管理界面，支持配置管理、实时查询、日志查看 |

## 快速开始

### 命令行版（简易版）

```bash
python3 tencent_ddns.py
```

首次使用请编辑 `tencent_ddns.py` 中的配置项，或在 `DDNS_web` 界面上填写。

### Web 版

```bash
cd DDNS_web
bash start.sh
```

访问 **http://0.0.0.0:8877**

详细说明见 [DDNS_web/README.md](DDNS_web/README.md)

## 功能对比

| 功能 | 简易版 | Web 版 |
|------|--------|--------|
| 配置管理 | 手动编辑代码 | 可视化界面 |
| 实时查询 | ❌ | ✅ |
| 日志查看 | ❌ | ✅ |
| 一键执行 DDNS | ✅ | ✅ |
| 定时任务提示 | ❌ | ✅ |

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

获取腾讯云密钥：[腾讯云控制台 → 访问密钥](https://console.cloud.tencent.com/cam/capi)

## 定时任务

```bash
# 每 5 分钟检查一次
*/5 * * * * /usr/bin/python3 /path/to/tencent_ddns.py >> /var/log/tencent_ddns.log 2>&1
```

## 其他资源

- 腾讯云 DNSPod API 文档：https://cloud.tencent.com/document/api/1427
- DNSPod API 文档：https://dnsapi.cn/#interface