# 腾讯云 DDNS (tencent_ddns)

腾讯云 DNSPod 动态域名解析（DDNS）脚本，支持自动更新子域名解析记录。

## 功能特性

- ✅ 支持 SecretId + SecretKey 认证
- ✅ 支持临时 Token 认证
- ✅ 自动获取公网 IP 地址
- ✅ 只在 IP 变化时更新解析记录，节省 API 调用
- ✅ 自动填写解析线路（RecordLine）
- ✅ 完整的日志记录功能

## 环境要求

- Python 3.6+
- 腾讯云 SDK for Python (`tencentcloud-sdk-python`)

## 安装依赖

```bash
python3 -m pip install --upgrade pip
python3 -m pip install requests tencentcloud-sdk-python
```

## 配置说明

编辑 `tencent_ddns.py` 文件，修改以下配置项：

```python
SECRET_ID = ""        # 腾讯云 SecretId（必填）
SECRET_KEY = ""       # 腾讯云 SecretKey（必填）
TOKEN = ""            # 临时密钥 Token（可选）
DOMAIN = "example.com"  # 主域名（必填）
SUBDOMAIN = "home"      # 子域名（必填）
RECORD_TYPE = "A"       # 解析记录类型（默认 A 记录）
RECORD_LINE = "默认"    # 解析线路（默认"默认"）
LOG_FILE = "/var/log/tencent_ddns.log"  # 日志文件路径
REGION = "ap-guangzhou"  # DNSPod 服务区域（固定）
```

### 获取腾讯云密钥

1. 访问 [腾讯云控制台](https://console.cloud.tencent.com/cam/capi)
2. 创建 API 密钥（SecretId 和 SecretKey）
3. 确保密钥有 DNSPod 相关权限

## 使用方法

### 手动运行

```bash
python3 tencent_ddns.py
```

### 定时任务（crontab）

添加到 crontab 实现自动更新（例如每 5 分钟检查一次）：

```bash
*/5 * * * * /usr/bin/python3 /path/to/tencent_ddns.py >> /var/log/tencent_ddns.log 2>&1
```

## 日志输出

脚本会将运行日志写入配置的 `LOG_FILE` 路径，格式如下：

```
2026-05-10 22:30:15 [INFO] IP 未变化: 123.123.123.123
2026-05-10 22:35:22 [INFO] DDNS 更新成功: 123.123.123.123 -> 123.123.123.124
2026-05-10 22:40:33 [ERROR] 无法获取公网 IP
```

## 注意事项

1. 首次运行前，请确保在腾讯云 DNSPod 控制台已创建对应的子域名解析记录
2. `RECORD_LINE` 参数必须与 DNSPod 控制台的线路名称一致（如"默认"、"电信"、"联通"等）
3. 建议使用定时任务定期运行，避免 IP 变化后无法及时更新
4. 日志文件路径需要有写入权限

## 其他资源

- 腾讯云 DNSPod API 文档：https://cloud.tencent.com/document/api/1427
- DNSPod API 文档：https://dnsapi.cn/#interface
