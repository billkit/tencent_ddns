# Web 管理界面

腾讯云 DDNS 的图形化管理界面，支持配置管理、实时查询、手动执行、日志查看和定时任务提示。

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动（默认 0.0.0.0:8877）
bash start.sh

# 或直接
python3 app.py
```

然后访问 **http://0.0.0.0:8877**

## 功能

- **配置管理** — 可视化填写 SecretId、SecretKey、域名、子域名、解析线路等
- **实时查询** — 查看当前公网 IP 和 DNSPod 解析记录状态
- **手动执行** — 一键触发 DDNS 更新
- **日志查看** — 实时显示运行日志（自动刷新）
- **定时任务** — 提供 crontab / systemd 定时器配置模板

## 目录结构

```
.
├── app.py              # Flask Web 应用
├── templates/
│   └── index.html      # 前端页面
├── start.sh            # 一键启动脚本
├── requirements.txt    # Python 依赖
└── .gitignore
```

## 配置说明

首次使用请在界面「配置」页面填写：

| 配置项 | 说明 |
|--------|------|
| SecretId | 腾讯云 API 密钥 ID（必填） |
| SecretKey | 腾讯云 API 密钥 Key（必填） |
| 主域名 | 如 `example.com`（必填） |
| 子域名 | 如 `home`（必填） |
| 解析线路 | 默认 / 电信 / 联通 / 移动 / 教育网 |
| 日志路径 | 默认为 `/var/log/tencent_ddns.log` |

> 获取 SecretId/SecretKey：[腾讯云控制台 → 访问密钥 → API 密钥](https://console.cloud.tencent.com/cam/capi)

## 定时任务

```bash
# 每 5 分钟检查一次
*/5 * * * * /usr/bin/python3 /path/to/app.py --port 8877 >> /var/log/tencent_ddns.log 2>&1
```

详见「定时任务」页面。

## 安全注意

- **不要** 将 8877 端口直接暴露在公网
- 建议通过 Nginx 反向代理 + HTTPS 访问
- `config.json` 包含敏感信息，勿提交到代码仓库（已加入 .gitignore）