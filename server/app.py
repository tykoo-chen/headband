"""
AI 自律发带 - 云端 API 后端
============================
单文件 Flask 服务：
  - 接收发带上传的图片，调用 Claude Vision 判断是否命中规则
  - 命中后返回硬件需要执行的动作（震动 / 蜂鸣 / LED）
  - 同时执行软通道惩罚（推送 / 邮件 / 记账）
  - 提供规则增删改查、事件日志、健康检查
数据存储在本地 JSON 文件，无数据库依赖。
"""

import base64
import json
import os
import time
import uuid
from datetime import datetime
from threading import Lock

from flask import Flask, request, jsonify
from flask_cors import CORS

import anthropic

import punishments


# ---------------------------------------------------------------------------
# 基础配置
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE_DIR, "rules.json")
EVENTS_PATH = os.path.join(BASE_DIR, "events.json")

CLAUDE_MODEL = "claude-opus-4-5"
COOLDOWN_SECONDS = 30
MAX_EVENTS = 500  # events.json 最大条数，超过会截断

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

app = Flask(__name__)
CORS(app)  # 允许 PWA 跨域调用

_file_lock = Lock()
_cooldown = {}  # rule_id -> last_triggered_at (epoch seconds)
_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


# ---------------------------------------------------------------------------
# JSON 文件读写工具
# ---------------------------------------------------------------------------

def _read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path, data):
    with _file_lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def load_rules():
    return _read_json(RULES_PATH, [])


def save_rules(rules):
    _write_json(RULES_PATH, rules)


def load_events():
    return _read_json(EVENTS_PATH, [])


def append_event(event):
    events = load_events()
    events.append(event)
    if len(events) > MAX_EVENTS:
        events = events[-MAX_EVENTS:]
    _write_json(EVENTS_PATH, events)


# ---------------------------------------------------------------------------
# 初始化默认规则（首次启动时）
# ---------------------------------------------------------------------------
if not os.path.exists(RULES_PATH):
    save_rules([
        {
            "id": "no_phone",
            "name": "学习时禁止玩手机",
            "enabled": True,
            "condition": "画面中出现手机屏幕、用户正在低头看手机或手里握着手机",
            "punishments": [
                {"channel": "vibrate", "params": {"duration_ms": 1500, "intensity": 1.0}},
                {"channel": "buzzer",  "params": {"duration_ms": 600, "freq_hz": 2200}},
                {"channel": "led",     "params": {"color": "red", "blink": 3}},
            ],
        },
        {
            "id": "no_snack",
            "name": "深夜禁止吃零食",
            "enabled": False,
            "condition": "画面中出现零食包装、薯片、饼干、巧克力等高热量零食",
            "punishments": [
                {"channel": "vibrate", "params": {"duration_ms": 800}},
                {"channel": "deduct",  "params": {"amount": 5, "reason": "夜宵零食"}},
            ],
        },
    ])


# ---------------------------------------------------------------------------
# Claude Vision 判断
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """你是 AI 自律发带的视觉裁判。用户会给你一张第一人称视角的照片以及一组"违规规则"。
请严格判断图中是否命中任意规则。

输出要求：
1. 只输出严格 JSON，不要任何解释性文字、不要 markdown 代码块。
2. 格式: {"matched": ["rule_id1", "rule_id2"], "reason": "简短中文说明"}
3. 如果没有命中任何规则，matched 为空数组。
4. 只返回明确命中的规则 id；模糊不清的不要算命中。"""


def _build_rule_text(rules):
    lines = []
    for r in rules:
        if r.get("enabled"):
            lines.append(f"- id={r['id']}: {r.get('name','')} -> 条件：{r.get('condition','')}")
    return "\n".join(lines) if lines else "（当前无启用规则）"


def _parse_claude_json(text):
    """容错解析 Claude 返回的 JSON。"""
    text = (text or "").strip()
    if text.startswith("```"):
        # 去掉 ```json ... ``` 包裹
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        # 尝试在文本中找第一个 { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                return {"matched": [], "reason": f"解析失败: {text[:120]}"}
        return {"matched": [], "reason": f"解析失败: {text[:120]}"}


def judge_with_vision(image_b64: str, media_type: str, rules: list) -> dict:
    """调用 Claude Vision 判断图片是否命中规则。"""
    if _client is None:
        return {"matched": [], "reason": "未配置 ANTHROPIC_API_KEY"}
    rule_text = _build_rule_text(rules)
    user_text = f"以下是当前启用的违规规则列表：\n{rule_text}\n\n请判断这张图片是否命中其中任何规则，按要求输出 JSON。"
    try:
        resp = _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": media_type, "data": image_b64,
                    }},
                    {"type": "text", "text": user_text},
                ],
            }],
        )
        text = resp.content[0].text if resp.content else ""
        return _parse_claude_json(text)
    except Exception as e:
        return {"matched": [], "reason": f"Claude 调用失败: {e}"}


def judge_with_text(scene_text: str, rules: list) -> dict:
    """文本版判断（用于 /test 端点，不消耗 vision 配额）。"""
    if _client is None:
        return {"matched": [], "reason": "未配置 ANTHROPIC_API_KEY"}
    rule_text = _build_rule_text(rules)
    user_text = (
        f"以下是当前启用的违规规则列表：\n{rule_text}\n\n"
        f"现在没有图片，只有一段文字描述的场景：\n{scene_text}\n\n"
        f"请基于该描述判断是否命中规则，按要求输出 JSON。"
    )
    try:
        resp = _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_text}],
        )
        text = resp.content[0].text if resp.content else ""
        return _parse_claude_json(text)
    except Exception as e:
        return {"matched": [], "reason": f"Claude 调用失败: {e}"}


# ---------------------------------------------------------------------------
# 命中后的动作分发
# ---------------------------------------------------------------------------

def dispatch_punishments(matched_ids, rules, reason):
    """为命中的规则执行 punishments，过滤掉冷却期内的规则。
    返回 (actions, executed, fired_ids)：
      - actions: 给硬件端的动作指令列表（vibrate/buzzer/led）
      - executed: 软通道执行结果
      - fired_ids: 实际触发（未被冷却拦截）的规则 id 列表
    """
    actions = []
    executed = []
    fired_ids = []
    now = time.time()
    rule_map = {r["id"]: r for r in rules}

    for rid in matched_ids:
        rule = rule_map.get(rid)
        if not rule or not rule.get("enabled"):
            continue
        # 冷却检查
        last = _cooldown.get(rid, 0)
        if now - last < COOLDOWN_SECONDS:
            continue
        _cooldown[rid] = now
        fired_ids.append(rid)

        for p in rule.get("punishments", []):
            result = punishments.execute(p)
            executed.append({"rule_id": rid, "channel": p.get("channel"), "result": result})
            # 硬件类通道把指令塞到 actions 里返回给发带端
            if result.get("ok") and p.get("channel") in ("vibrate", "buzzer", "led"):
                actions.append(result.get("detail"))

    if fired_ids:
        append_event({
            "id": uuid.uuid4().hex[:12],
            "ts": datetime.now().isoformat(timespec="seconds"),
            "matched_rules": fired_ids,
            "reason": reason,
            "actions": actions,
            "executed": executed,
        })
    return actions, executed, fired_ids


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "model": CLAUDE_MODEL,
        "has_api_key": bool(ANTHROPIC_API_KEY),
        "rules_count": len(load_rules()),
        "events_count": len(load_events()),
        "time": datetime.now().isoformat(timespec="seconds"),
    })


@app.route("/rules", methods=["GET"])
def get_rules():
    return jsonify(load_rules())


@app.route("/rules", methods=["POST"])
def post_rules():
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        return jsonify({"ok": False, "error": "请求体必须是规则数组"}), 400
    save_rules(data)
    return jsonify({"ok": True, "count": len(data)})


@app.route("/events", methods=["GET"])
def get_events():
    try:
        limit = int(request.args.get("limit", 50))
    except Exception:
        limit = 50
    events = load_events()
    return jsonify(events[-limit:][::-1])  # 最新在前


@app.route("/frame", methods=["POST"])
def post_frame():
    """发带端上传一帧图片：
    支持两种形式：
      1) multipart/form-data，字段名 image
      2) application/json，字段 image_base64 + 可选 media_type
    """
    image_b64 = None
    media_type = "image/jpeg"

    if request.files.get("image"):
        f = request.files["image"]
        image_b64 = base64.b64encode(f.read()).decode("ascii")
        media_type = f.mimetype or "image/jpeg"
    else:
        data = request.get_json(silent=True) or {}
        image_b64 = data.get("image_base64")
        media_type = data.get("media_type", "image/jpeg")
        # 兼容 dataURL
        if image_b64 and image_b64.startswith("data:"):
            header, _, body = image_b64.partition(",")
            image_b64 = body
            if ";" in header and ":" in header:
                media_type = header.split(":", 1)[1].split(";", 1)[0]

    if not image_b64:
        return jsonify({"ok": False, "error": "缺少图片数据"}), 400

    rules = load_rules()
    verdict = judge_with_vision(image_b64, media_type, rules)
    matched = verdict.get("matched", []) or []
    reason = verdict.get("reason", "")
    actions, executed, fired = dispatch_punishments(matched, rules, reason)

    return jsonify({
        "ok": True,
        "matched_rules": matched,
        "fired_rules": fired,
        "reason": reason,
        "actions": actions,
        "executed": executed,
    })


@app.route("/test", methods=["POST"])
def post_test():
    """测试端点：传文本场景描述，复用整套判断+派发流程。"""
    data = request.get_json(silent=True) or {}
    scene = data.get("scene") or data.get("text") or ""
    if not scene:
        return jsonify({"ok": False, "error": "缺少 scene 字段"}), 400

    rules = load_rules()
    verdict = judge_with_text(scene, rules)
    matched = verdict.get("matched", []) or []
    reason = verdict.get("reason", "")
    actions, executed, fired = dispatch_punishments(matched, rules, reason)

    return jsonify({
        "ok": True,
        "matched_rules": matched,
        "fired_rules": fired,
        "reason": reason,
        "actions": actions,
        "executed": executed,
    })


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
