"""
惩罚通道模块
================
负责把"违规"事件转化为各种惩罚动作：
  - 软通道：Bark 推送、企业微信机器人、邮件、本地记账
  - 硬通道：震动 / 蜂鸣 / LED （由发带端硬件执行，这里只构造指令）

设计原则：每个函数独立 try/except，单通道失败不影响其它通道；
统一返回 dict: {"ok": bool, "channel": str, "detail": str}
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

import requests


DEDUCT_LOG_PATH = os.path.join(os.path.dirname(__file__), "deduct_log.json")


def _ok(channel, detail=""):
    return {"ok": True, "channel": channel, "detail": detail}


def _fail(channel, detail=""):
    return {"ok": False, "channel": channel, "detail": str(detail)}


# ---------------------------------------------------------------------------
# 软通道：远程推送 / 通知
# ---------------------------------------------------------------------------

def bark_push(title: str, body: str, device_key: str) -> dict:
    """通过 Bark 向 iOS 设备推送一条通知。
    device_key 是用户在 Bark App 内拿到的 key。"""
    try:
        url = f"https://api.day.app/{device_key}/{requests.utils.quote(title)}/{requests.utils.quote(body)}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return _ok("bark", r.text[:200])
        return _fail("bark", f"http {r.status_code}: {r.text[:200]}")
    except Exception as e:
        return _fail("bark", e)


def wecom_bot(webhook_url: str, text: str) -> dict:
    """企业微信群机器人 webhook 推送一条文本消息。"""
    try:
        payload = {"msgtype": "text", "text": {"content": text}}
        r = requests.post(webhook_url, json=payload, timeout=5)
        if r.status_code == 200 and r.json().get("errcode", -1) == 0:
            return _ok("wecom_bot", "sent")
        return _fail("wecom_bot", f"http {r.status_code}: {r.text[:200]}")
    except Exception as e:
        return _fail("wecom_bot", e)


def send_email(to: str, subject: str, body: str, smtp_config: dict) -> dict:
    """通过 SMTP 发送一封纯文本邮件。
    smtp_config 字段：host, port, user, password, from(可选), use_ssl(默认 True)。"""
    try:
        host = smtp_config["host"]
        port = int(smtp_config.get("port", 465))
        user = smtp_config["user"]
        password = smtp_config["password"]
        sender = smtp_config.get("from", user)
        use_ssl = smtp_config.get("use_ssl", True)

        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = Header(subject, "utf-8")

        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        server.login(user, password)
        server.sendmail(sender, [to], msg.as_string())
        server.quit()
        return _ok("email", f"to {to}")
    except Exception as e:
        return _fail("email", e)


# ---------------------------------------------------------------------------
# 硬通道：返回硬件指令，让发带端实际执行
# ---------------------------------------------------------------------------

def vibrate(payload: dict) -> dict:
    """构造一条震动指令。payload 例: {"duration_ms": 1500, "intensity": 0.8}"""
    try:
        return _ok("vibrate", {
            "type": "vibrate",
            "duration_ms": int(payload.get("duration_ms", 1000)),
            "intensity": float(payload.get("intensity", 1.0)),
        })
    except Exception as e:
        return _fail("vibrate", e)


def buzzer(payload: dict) -> dict:
    """构造一条蜂鸣指令。payload 例: {"duration_ms": 800, "freq_hz": 2000}"""
    try:
        return _ok("buzzer", {
            "type": "buzzer",
            "duration_ms": int(payload.get("duration_ms", 500)),
            "freq_hz": int(payload.get("freq_hz", 2000)),
        })
    except Exception as e:
        return _fail("buzzer", e)


def led(payload: dict) -> dict:
    """构造一条 LED 闪烁指令。payload 例: {"color": "red", "blink": 3}"""
    try:
        return _ok("led", {
            "type": "led",
            "color": payload.get("color", "red"),
            "blink": int(payload.get("blink", 1)),
        })
    except Exception as e:
        return _fail("led", e)


# ---------------------------------------------------------------------------
# 本地记账
# ---------------------------------------------------------------------------

def log_deduct(amount: float, reason: str) -> dict:
    """把一次扣款（虚拟币 / 零花钱）追加到本地账本。"""
    try:
        records = []
        if os.path.exists(DEDUCT_LOG_PATH):
            with open(DEDUCT_LOG_PATH, "r", encoding="utf-8") as f:
                try:
                    records = json.load(f)
                except Exception:
                    records = []
        records.append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "amount": float(amount),
            "reason": reason,
        })
        with open(DEDUCT_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return _ok("log_deduct", f"-{amount}")
    except Exception as e:
        return _fail("log_deduct", e)


# ---------------------------------------------------------------------------
# 统一调度入口
# ---------------------------------------------------------------------------

def execute(punishment: dict) -> dict:
    """根据 punishment 配置分发到对应通道。
    punishment 形如:
        {"channel": "vibrate", "params": {"duration_ms": 1500}}
        {"channel": "bark",    "params": {"title": "...", "body": "...", "device_key": "..."}}
    """
    try:
        ch = punishment.get("channel")
        params = punishment.get("params", {}) or {}
        if ch == "vibrate":
            return vibrate(params)
        if ch == "buzzer":
            return buzzer(params)
        if ch == "led":
            return led(params)
        if ch == "bark":
            return bark_push(params.get("title", "AI 自律发带"),
                             params.get("body", "检测到违规"),
                             params.get("device_key", ""))
        if ch == "wecom_bot":
            return wecom_bot(params.get("webhook_url", ""),
                             params.get("text", "AI 自律发带：检测到违规"))
        if ch == "email":
            return send_email(params.get("to", ""),
                              params.get("subject", "AI 自律发带告警"),
                              params.get("body", "检测到违规"),
                              params.get("smtp", {}))
        if ch == "deduct":
            return log_deduct(params.get("amount", 1), params.get("reason", "违规"))
        return _fail(ch or "unknown", "未知通道")
    except Exception as e:
        return _fail(punishment.get("channel", "unknown"), e)
