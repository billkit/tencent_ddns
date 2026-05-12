#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
腾讯云 DDNS 生产版脚本
功能：
- 支持 Token 或 SecretId+SecretKey
- 自动获取公网 IP
- 只在 IP 变化时更新解析
- 自动填写 RecordLine (默认)
- 日志记录
"""

import requests
import json
import os
import sys
from tencentcloud.common import credential
from tencentcloud.dnspod.v20210323 import dnspod_client, models
from datetime import datetime

# =========================
# 配置
# =========================
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# 默认配置
DEFAULTS = {
    "SECRET_ID": "",
    "SECRET_KEY": "",
    "TOKEN": "",
    "DOMAIN": "example.com",
    "SUBDOMAIN": "home",
    "RECORD_TYPE": "A",
    "RECORD_LINE": "默认",
    "LOG_FILE": "/var/log/tencent_ddns.log",
    "REGION": "ap-guangzhou"
}

def load_config() -> dict:
    """从 config.json 读取配置，缺失项用默认值"""
    config = DEFAULTS.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                json_config = json.load(f)
                config.update(json_config)
        except Exception as e:
            print(f"[WARN] 读取 config.json 失败: {e}，使用默认配置", file=sys.stderr)
    return config

cfg = load_config()
SECRET_ID = cfg["SECRET_ID"]
SECRET_KEY = cfg["SECRET_KEY"]
TOKEN = cfg["TOKEN"]
DOMAIN = cfg["DOMAIN"]
SUBDOMAIN = cfg["SUBDOMAIN"]
RECORD_TYPE = cfg["RECORD_TYPE"]
RECORD_LINE = cfg["RECORD_LINE"]
LOG_FILE = cfg["LOG_FILE"]
REGION = cfg["REGION"]

# =========================
# 工具函数
# =========================
def log(message: str):
    """写日志"""
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{time_str} {message}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def get_public_ip() -> str:
    """获取公网 IP"""
    for url in ["https://api.ipify.org", "https://ipinfo.io/ip"]:
        try:
            ip = requests.get(url, timeout=5).text.strip()
            if ip:
                return ip
        except Exception:
            continue
    return ""

# =========================
# 主程序
# =========================
def main():
    current_ip = get_public_ip()
    if not current_ip:
        log("[ERROR] 无法获取公网 IP")
        sys.exit(1)

    # 创建腾讯云客户端
    cred = credential.Credential(SECRET_ID, SECRET_KEY, TOKEN)
    client = dnspod_client.DnspodClient(cred, REGION)

    # 查询解析记录
    req = models.DescribeRecordListRequest()
    req.Domain = DOMAIN
    req.Subdomain = SUBDOMAIN
    req.RecordType = RECORD_TYPE
    req.Limit = 1

    try:
        resp = client.DescribeRecordList(req)
    except Exception as e:
        log(f"[ERROR] 查询解析记录失败: {e}")
        sys.exit(1)

    if not resp.RecordList or len(resp.RecordList) == 0:
        log(f"[ERROR] 未找到 {SUBDOMAIN}.{DOMAIN} 的解析记录")
        sys.exit(1)

    record = resp.RecordList[0]
    record_id = record.RecordId
    old_ip = record.Value

    if current_ip == old_ip:
        log(f"[INFO] IP 未变化: {current_ip}")
        return

    # 更新解析记录
    update_req = models.ModifyRecordRequest()
    update_req.Domain = DOMAIN
    update_req.RecordId = record_id
    update_req.SubDomain = SUBDOMAIN
    update_req.RecordType = RECORD_TYPE
    update_req.Value = current_ip
    update_req.RecordLine = RECORD_LINE  # 必填

    try:
        update_resp = client.ModifyRecord(update_req)
        log(f"[INFO] DDNS 更新成功: {old_ip} -> {current_ip}")
    except Exception as e:
        log(f"[ERROR] DDNS 更新失败: {e}")

if __name__ == "__main__":
    main()
