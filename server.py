"""
AI 自律发带 - 板子端 Flask 服务（部署到 /root/server.py）
========================================================
提供接口：
  GET  /            - PWA 静态资源（index.html 等）
  GET  /scene       - 抓一帧摄像头图 + Kimi 生成文字描述，给 PWA 实时轮询
  POST /speak       - 收到规则命中后，让 Kimi 生成羞辱语并以 JSON 返回，由 PWA 端 Web Speech API 播报
  POST /email       - 收到规则命中后发送邮件通报（当前只打日志，SMTP 待接）

依赖安装（板子端）：
  pip3 install edge-tts flask openai
  sudo apt install mpg123 alsa-utils
  # Ensure MOONSHOT_API_KEY env var is set
"""

import os
import base64
import subprocess
import tempfile
from flask import Flask, request, jsonify, send_from_directory

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.environ.get('PWA_DIR', APP_DIR)
MOONSHOT_API_KEY = os.environ.get('MOONSHOT_API_KEY', '')

app = Flask(__name__, static_folder=None)

client = None
if OpenAI and MOONSHOT_API_KEY:
    client = OpenAI(api_key=MOONSHOT_API_KEY, base_url='https://api.moonshot.cn/v1')


# ---------------------------------------------------------------------------
# CORS — 允许 PWA 从任何来源调用（含 OPTIONS 预检）
# ---------------------------------------------------------------------------
@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp


# ---------------------------------------------------------------------------
# 静态：PWA 前端
# ---------------------------------------------------------------------------
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def static_files(path):
    full = os.path.join(STATIC_DIR, path)
    if os.path.isdir(full):
        path = os.path.join(path, 'index.html')
    return send_from_directory(STATIC_DIR, path)


# ---------------------------------------------------------------------------
# /scene — 摄像头抓一帧 + Kimi 描述
# ---------------------------------------------------------------------------
def _grab_frame():
    """用 fswebcam 抓一帧到临时 jpg，返回 base64。"""
    jpg = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
    try:
        subprocess.run(
            ['fswebcam', '-q', '-r', '640x480', '--no-banner', jpg],
            check=True, timeout=10
        )
        with open(jpg, 'rb') as f:
            return base64.b64encode(f.read()).decode('ascii')
    finally:
        try: os.unlink(jpg)
        except Exception: pass


@app.route('/scene', methods=['GET', 'OPTIONS'])
def scene():
    if request.method == 'OPTIONS':
        return ('', 204)
    try:
        img_b64 = _grab_frame()
    except Exception as e:
        return jsonify(error=f'camera failed: {e}'), 500

    text = ''
    if client:
        try:
            r = client.chat.completions.create(
                model='moonshot-v1-8k-vision-preview',
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}},
                        {'type': 'text', 'text': '请用一句中文（30 字以内）客观描述画面里用户正在做什么、手里有什么。'},
                    ],
                }],
            )
            text = r.choices[0].message.content.strip()
        except Exception as e:
            text = f'(Kimi 描述失败: {e})'
    else:
        text = '(未配置 MOONSHOT_API_KEY)'

    return jsonify(text=text, image=img_b64)


# ---------------------------------------------------------------------------
# /speak — 语音羞辱惩罚
# ---------------------------------------------------------------------------
@app.route('/speak', methods=['POST', 'OPTIONS'])
def speak():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json() or {}
    rule = data.get('rule_name', '')
    condition = data.get('condition', '')
    reason = data.get('reason', '')

    if not client:
        return jsonify(error='MOONSHOT_API_KEY not configured'), 500

    prompt = (
        f'用户违反了规则"{rule}"（条件：{condition}）。'
        f'请生成一句 20 字以内、接地气、带点脏话但不过分的中文批评语，'
        f'要有冲击力，直接输出这一句，不要引号。'
    )
    try:
        r = client.chat.completions.create(
            model='moonshot-v1-8k',
            messages=[{'role': 'user', 'content': prompt}],
        )
        line = r.choices[0].message.content.strip().strip('"""')
    except Exception as e:
        return jsonify(error=f'kimi failed: {e}'), 500

    print(f'[SPEAK PUNISHMENT] rule={rule} reason={reason} line={line}')
    return jsonify(ok=True, line=line)


# ---------------------------------------------------------------------------
# /email — 邮件通报惩罚（当前仅记录，SMTP 待接）
# ---------------------------------------------------------------------------
@app.route('/email', methods=['POST', 'OPTIONS'])
def email():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json() or {}
    to = data.get('to', '')
    if not to:
        return jsonify(error='missing to'), 400
    # TODO: actual SMTP send — for now just log to stdout and return success
    print(f'[EMAIL PUNISHMENT] to={to} rule={data.get("rule_name")} reason={data.get("reason")}')
    return jsonify(ok=True, logged=True, note='SMTP not configured yet')


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
