#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""传天羽高管经营驾驶舱 V4：零第三方依赖的本地服务。

运行: python app.py  ->  http://127.0.0.1:8003
"""

import json
import mimetypes
import os
import threading
import urllib.error
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE = Path(__file__).resolve().parent
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:8b"


def load_data():
    return json.loads((BASE / "data.json").read_text(encoding="utf-8"))


def build_context(d):
    """把看板数据压缩成给 AI 的上下文文本。"""
    apr = d["apr"]
    lines = []
    lines.append(f"数据日期：{d['today']}（今日为吉客云实时部分数据）")
    lines.append(f"全公司：今日销售额{d['today_total']['amount_wan']}万元/{d['today_total']['orders']}单，环比昨日{d['chg_vs_yest']}%，较上周同日{d['chg_vs_lastwk']}%")
    lines.append("渠道结构（今日）：" + "、".join(
        f"{c['name']} {c['amount_wan']}万(占{c['pct']}%, 较昨日{c['yest_chg']}%)" for c in d["channels"]
    ))
    lines.append(
        f"APR门店8月（截至8/10）：月销{apr['sales']}万/目标{apr['task']}万/完成率{apr['rate']}%，"
        f"毛利{apr['profit']}万/毛利率{apr['pm']}%，客流{apr['traffic']}人/订单{apr['orders']}单/"
        f"转化率{apr['conv']}%，时间进度{apr['time_progress']}%（差{apr['gap']}pp）"
    )
    lines.append(f"达成预测：按当前日均节奏预测月末{apr['forecast_month_end']}万，达成率{apr['forecast_rate']}%")
    stores = "；".join(
        f"{s['name']}销{s['sales']}万/完成{s['rate']}%/毛利{s['profit']}万/毛利率{s['pm']}%/转化{s['conv']}%"
        for s in apr["stores"]
    )
    lines.append(f"门店明细：{stores}")
    sps = "、".join(f"{s['name']}({s['store']}){s['sales']}万/完成{s['rate']}%" for s in apr["salespersons"][:8])
    lines.append(f"销售员TOP：{sps}")
    lines.append(f"库存：SKU {d['inventory']['total_skus']}，总件数{d['inventory']['total_qty']}，其中'其他'类{d['inventory']['other_qty']}件占{d['inventory']['other_pct']}%（需核实）")
    lines.append(f"Apple电商今日{d['ecomm']['apple']['amount_wan']}万/{d['ecomm']['apple']['orders']}单；Shure电商今日{d['ecomm']['shure']['amount_wan']}万/{d['ecomm']['shure']['orders']}单")
    ib = d.get("inventory_biz", {})
    if ib:
        lines.append(f"库存（商务分析表，金额口径，已剔除虚拟品）：总库存{ib['total']['amount']}万/{ib['total']['qty']}件；分类：" + "、".join(
            f"{c['name']}{c['amount']}万({c['pct']}%)" for c in ib.get("category", [])
        ))
        lines.append("库存仓位：" + "、".join(f"{w['name']}{w['amount']}万({w['pct']}%)" for w in ib.get("warehouse", [])))
        lines.append("库龄分布(万)：" + "、".join(f"{k}{v}" for k, v in ib.get("aging", {}).items()))
        lines.append(f"高库龄预警：90天+ {ib.get('aging_risk_amount', 0)}万（占{ib.get('aging_risk_pct', 0)}%），360天+ {ib.get('severe_amount', 0)}万/{ib.get('severe_count', 0)}项，需商务专项处理")
    st = d.get("apr_struct", {})
    h = st.get("host") or {}
    a = st.get("acc") or {}
    if h:
        lines.append(
            f"APR产品结构（8月线下真实）：主机{h.get('host_amount', 0)}万，"
            f"iPhone {h.get('iphone', {}).get('amount', 0)}万({h.get('iphone', {}).get('pct', 0)}%)/"
            f"iPad {h.get('ipad', {}).get('amount', 0)}万({h.get('ipad', {}).get('pct', 0)}%)/"
            f"Watch {h.get('watch', {}).get('amount', 0)}万({h.get('watch', {}).get('pct', 0)}%)/"
            f"Mac {h.get('mac', {}).get('amount', 0)}万({h.get('mac', {}).get('pct', 0)}%)"
        )
    if a:
        lines.append(f"第三方配件（8月线下）：{a.get('acc_amount', 0)}万，手机配件占{a.get('phone', {}).get('pct', 0)}%")
    return "\n".join(lines)


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


class DashboardHandler(SimpleHTTPRequestHandler):
    server_version = "ChuangelDashboard/4.0"

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_bytes(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.send_file(BASE / "templates" / "index.html", "text/html; charset=utf-8")
            return
        if path == "/api/data":
            self.send_bytes(200, json_bytes(load_data()), "application/json; charset=utf-8")
            return
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            target = (BASE / "static" / rel).resolve()
            static_root = (BASE / "static").resolve()
            if target != static_root and static_root in target.parents and target.is_file():
                self.send_file(target)
                return
        self.send_error(404, "Not Found")

    def send_file(self, path, content_type=None):
        try:
            body = path.read_bytes()
        except OSError:
            self.send_error(404, "Not Found")
            return
        mime = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if mime.startswith("text/") and "charset" not in mime:
            mime += "; charset=utf-8"
        self.send_bytes(200, body, mime)

    def do_POST(self):
        if urlparse(self.path).path != "/api/ai":
            self.send_error(404, "Not Found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            req_json = json.loads(self.rfile.read(length) or b"{}")
            q = str(req_json.get("q", "")).strip()
        except (ValueError, json.JSONDecodeError):
            self.send_bytes(400, json_bytes({"error": "请求格式错误"}), "application/json; charset=utf-8")
            return
        if not q:
            self.send_bytes(400, json_bytes({"error": "问题不能为空"}), "application/json; charset=utf-8")
            return

        d = load_data()
        system = (
            "你是传天羽科技（Apple授权经销商）经营简报看板的AI分析助手，服务对象是公司老板。"
            "你具备资深零售操盘手的分析能力。回答要求：\n"
            "1. 全程用中文，简洁、专业、有结论有数据有建议\n"
            "2. 先给结论，再给关键数据支撑，最后给1-3条可执行建议\n"
            "3. 数据中未提供的内容要明说'该数据暂未接入'，不要编造\n"
            "4. 涉及门店分析时，结合完成率、毛利、转化、客流等指标综合判断\n"
        )
        prompt = f"{system}\n\n===== 今日看板核心数据 =====\n{build_context(d)}\n\n===== 老板提问 =====\n{q}\n\n请回答："
        payload = json_bytes({
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.3},
        })
        try:
            req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
            answer = (resp.get("response") or "").strip() or "（模型未返回内容，请稍后重试）"
            self.send_bytes(200, json_bytes({"answer": answer}), "application/json; charset=utf-8")
        except Exception as exc:
            self.send_bytes(500, json_bytes({"error": f"AI服务暂时不可用：{exc}"}), "application/json; charset=utf-8")


def main():
    url = "http://127.0.0.1:8003"
    server = ThreadingHTTPServer(("127.0.0.1", 8003), DashboardHandler)
    print(f"传天羽高管经营驾驶舱 V4 已启动：{url}")
    print("使用期间请保持本窗口打开。按 Ctrl+C 可停止。")
    if os.environ.get("AUTO_OPEN_BROWSER", "1") == "1":
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
