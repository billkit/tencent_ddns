#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云 DDNS Web 管理界面
功能：配置管理、实时查询、手动执行、日志查看、定时任务
"""

import os
import sys
import json
import logging
from datetime import datetime

sys.path.insert(0, '/root/.local/lib/python3.9/site-packages')

import requests
from flask import Flask, request, render_template, jsonify, redirect

from tencentcloud.common import credential
from tencentcloud.dnspod.v20210323 import dnspod_client, models

# =========================
# 配置
# =========================
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
LOG_FILE = '/var/log/tencent_ddns.log'
APP_PORT = 8877

# =========================
# 工具函数
# =========================
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'SECRET_ID': '', 'SECRET_KEY': '', 'TOKEN': '',
        'DOMAIN': '', 'SUBDOMAIN': '', 'RECORD_TYPE': 'A',
        'RECORD_LINE': '默认', 'LOG_FILE': LOG_FILE, 'REGION': 'ap-guangzhou'
    }

def write_log(cfg, message):
    """写日志到文件"""
    log_path = cfg.get('LOG_FILE', LOG_FILE)
    try:
        dir_path = os.path.dirname(log_path) or '/tmp'
        os.makedirs(dir_path, exist_ok=True)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'{ts} {message}\n')
            f.flush()
    except Exception as e:
        sys.stderr.write(f'write_log error: {e}\n')

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def get_public_ip():
    for url in ['https://api.ipify.org', 'https://ipinfo.io/ip', 'https://icanhazip.com']:
        try:
            ip = requests.get(url, timeout=5).text.strip()
            if ip and ip[0].isdigit():
                return ip
        except Exception:
            continue
    return ''

def get_dnspod_client(cfg):
    cred = credential.Credential(cfg['SECRET_ID'], cfg['SECRET_KEY'], cfg.get('TOKEN', ''))
    return dnspod_client.DnspodClient(cred, cfg['REGION'])

def run_ddns(cfg):
    current_ip = get_public_ip()
    if not current_ip:
        msg = '[ERROR] 无法获取公网 IP'
        write_log(cfg, msg)
        return {'success': False, 'message': msg, 'old_ip': '', 'new_ip': ''}

    client = get_dnspod_client(cfg)

    req = models.DescribeRecordListRequest()
    req.Domain = cfg['DOMAIN']
    req.Subdomain = cfg['SUBDOMAIN']
    req.RecordType = cfg['RECORD_TYPE']
    req.Limit = 1

    try:
        resp = client.DescribeRecordList(req)
    except Exception as e:
        msg = f'[ERROR] 查询解析记录失败: {e}'
        write_log(cfg, msg)
        return {'success': False, 'message': msg, 'old_ip': '', 'new_ip': current_ip}

    if not resp.RecordList or len(resp.RecordList) == 0:
        msg = f'[ERROR] 未找到 {cfg["SUBDOMAIN"]}.{cfg["DOMAIN"]} 的解析记录'
        write_log(cfg, msg)
        return {'success': False, 'message': msg, 'old_ip': '', 'new_ip': current_ip}

    record = resp.RecordList[0]
    record_id = record.RecordId
    old_ip = record.Value

    if current_ip == old_ip:
        msg = f'[INFO] IP 未变化: {current_ip}'
        write_log(cfg, msg)
        return {'success': True, 'message': f'IP 未变化，当前解析IP: {current_ip}', 'old_ip': old_ip, 'new_ip': current_ip}

    update_req = models.ModifyRecordRequest()
    update_req.Domain = cfg['DOMAIN']
    update_req.RecordId = record_id
    update_req.SubDomain = cfg['SUBDOMAIN']
    update_req.RecordType = cfg['RECORD_TYPE']
    update_req.Value = current_ip
    update_req.RecordLine = cfg['RECORD_LINE']

    try:
        client.ModifyRecord(update_req)
        msg = f'[INFO] DDNS 更新成功: {old_ip} -> {current_ip}'
        write_log(cfg, msg)
        return {'success': True, 'message': msg, 'old_ip': old_ip, 'new_ip': current_ip}
    except Exception as e:
        msg = f'[ERROR] DDNS 更新失败: {e}'
        write_log(cfg, msg)
        return {'success': False, 'message': msg, 'old_ip': old_ip, 'new_ip': current_ip}

def query_record(cfg):
    current_ip = get_public_ip()
    if not current_ip:
        return {'success': False, 'message': '无法获取公网 IP', 'current_wan_ip': '', 'records': []}

    client = get_dnspod_client(cfg)

    req = models.DescribeRecordListRequest()
    req.Domain = cfg['DOMAIN']
    req.Subdomain = cfg['SUBDOMAIN']
    req.RecordType = cfg['RECORD_TYPE']
    req.Limit = 20

    try:
        resp = client.DescribeRecordList(req)
    except Exception as e:
        return {'success': False, 'message': f'查询失败: {e}', 'current_wan_ip': current_ip, 'records': []}

    records = []
    if resp.RecordList:
        for r in resp.RecordList:
            records.append({
                'RecordId': r.RecordId, 'Value': r.Value,
                'RecordType': r.Type, 'RecordLine': r.Line,
                'TTL': getattr(r, 'TTL', None),
                'Status': getattr(r, 'Status', 'Enable'),
                'Updated': getattr(r, 'UpdatedOn', '')
            })

    return {'success': True, 'message': '查询成功', 'current_wan_ip': current_ip, 'records': records}

def read_log_file(log_path, lines=100):
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        return [l.strip() for l in all_lines[-lines:] if l.strip()]
    except Exception:
        return []

# =========================
# Flask 应用
# =========================
app = Flask(__name__, static_folder='static')
app.config['JSON_AS_ASCII'] = False

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# =========================
# 路由
# =========================
@app.route('/')
def index():
    return render_template('index.html', page='home')

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    cfg = load_config()
    if request.method == 'POST':
        cfg['SECRET_ID'] = request.form.get('SECRET_ID', '').strip()
        cfg['SECRET_KEY'] = request.form.get('SECRET_KEY', '').strip()
        cfg['TOKEN'] = request.form.get('TOKEN', '').strip()
        cfg['DOMAIN'] = request.form.get('DOMAIN', '').strip()
        cfg['SUBDOMAIN'] = request.form.get('SUBDOMAIN', '').strip()
        cfg['RECORD_TYPE'] = request.form.get('RECORD_TYPE', 'A').strip()
        cfg['RECORD_LINE'] = request.form.get('RECORD_LINE', '默认').strip()
        cfg['LOG_FILE'] = request.form.get('LOG_FILE', LOG_FILE).strip()
        cfg['REGION'] = request.form.get('REGION', 'ap-guangzhou').strip()
        save_config(cfg)
        return jsonify({'success': True, 'message': '配置已保存'})
    return render_template('index.html', page='config', saved=False, cfg=cfg)

@app.route('/api/run', methods=['POST'])
def api_run():
    cfg = load_config()
    if not cfg['SECRET_ID'] or not cfg['DOMAIN']:
        return jsonify({'success': False, 'message': '请先完成配置'})
    return jsonify(run_ddns(cfg))

@app.route('/api/query')
def api_query():
    cfg = load_config()
    if not cfg['SECRET_ID'] or not cfg['DOMAIN']:
        return jsonify({'success': False, 'message': '请先完成配置'})
    return jsonify(query_record(cfg))

@app.route('/api/ip')
def api_ip():
    ip = get_public_ip()
    return jsonify({'success': True, 'ip': ip if ip else '获取失败'})

@app.route('/api/logs')
def api_logs():
    cfg = load_config()
    log_path = request.args.get('path', cfg.get('LOG_FILE', LOG_FILE))
    count = int(request.args.get('count', 100))
    lines = read_log_file(log_path, count)
    return jsonify({'success': True, 'logs': lines, 'path': log_path})

@app.route('/api/status')
def api_status():
    cfg = load_config()
    ip = get_public_ip()
    result = query_record(cfg) if cfg['SECRET_ID'] and cfg['DOMAIN'] else {'success': False}
    return jsonify({
        'configured': bool(cfg['SECRET_ID'] and cfg['DOMAIN']),
        'current_wan_ip': ip if ip else '获取失败',
        'record_ip': result.get('records', [{}])[0].get('Value', '未查询') if result.get('success') else '查询失败',
        'record_info': result
    })

@app.route('/cron')
def cron_page():
    cfg = load_config()
    return render_template('index.html', page='cron', cfg=cfg)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', type=int, default=APP_PORT)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()
    print(f'\n  腾讯云 DDNS Web 管理界面\n  访问地址: http://0.0.0.0:{args.port}\n')
    app.run(host=args.host, port=args.port, debug=False, threaded=True)