"""
AI 自律发带 - 板子端 Flask 服务
================================
接口：
  GET  /            - PWA 静态资源
  GET  /frame       - 返回最新一帧 JPEG（1Hz 直播流，给 PWA <img src=.../frame?t=>）
  GET  /scene       - 返回 {text, image(base64)}，Kimi 描述最近一帧
  POST /speak       - Kimi 生成羞辱语，返回 {line}，由 PWA 端 Web Speech API 播报
  POST /email       - 邮件通报占位

依赖：
  pip3 install flask openai opencv-python
  export MOONSHOT_API_KEY=...
"""

import os
import time
import base64
import threading

import cv2
import requests
from flask import Flask, request, jsonify, send_from_directory, Response

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.environ.get('PWA_DIR', APP_DIR)
MOONSHOT_API_KEY = os.environ.get('MOONSHOT_API_KEY', '')
XAI_API_KEY = os.environ.get('XAI_API_KEY', '')

app = Flask(__name__, static_folder=None)

client = None
if OpenAI and MOONSHOT_API_KEY:
    client = OpenAI(api_key=MOONSHOT_API_KEY, base_url='https://api.moonshot.cn/v1')


# ----- 摄像头后台抓帧 -----
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
latest = {'jpg': None}

def _grab_loop():
    while True:
        ok, f = cap.read()
        if ok:
            _, buf = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 85])
            latest['jpg'] = buf.tobytes()
        time.sleep(0.05)

threading.Thread(target=_grab_loop, daemon=True).start()


# ----- CORS + 永远不缓存 HTML/JS（避免 iPhone Safari 死缓存老版本） -----
@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    ct = resp.headers.get('Content-Type', '')
    if any(t in ct for t in ('html', 'javascript', 'json')):
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
    return resp


# ----- 静态 PWA -----
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def static_files(path):
    full = os.path.join(STATIC_DIR, path)
    if os.path.isdir(full):
        path = os.path.join(path, 'index.html')
    return send_from_directory(STATIC_DIR, path)


# ----- /frame 实时画面流 -----
@app.route('/frame')
def frame():
    if not latest['jpg']:
        return '', 503
    return Response(latest['jpg'], mimetype='image/jpeg')


# ----- /scene Kimi 描述 -----
@app.route('/scene', methods=['GET', 'OPTIONS'])
def scene():
    if request.method == 'OPTIONS':
        return ('', 204)
    if not latest['jpg']:
        return jsonify(error='no frame'), 503
    jpg = latest['jpg']
    b64 = base64.b64encode(jpg).decode('ascii')
    text = ''
    if client:
        try:
            r = client.chat.completions.create(
                model='moonshot-v1-8k-vision-preview',
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
                        {'type': 'text', 'text': (
                            '用一句中文（最多 60 字）客观描述这张第一人称画面：'
                            '画面里用户在做什么动作，手里或眼前有什么物品；'
                            '如果画面里有屏幕或包装，识别出上面所有可见的文字、品牌名、App 名、Logo 关键词并写出来；'
                            '直接输出一句话，不要评价，不要省略可见的文字。'
                        )},
                    ],
                }],
            )
            text = r.choices[0].message.content.strip()
        except Exception as e:
            text = f'(Kimi 描述失败: {e})'
    else:
        text = '(未配置 MOONSHOT_API_KEY)'
    return jsonify(text=text, image=b64)


# ----- /speak -----
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

    # 语音合成放到 PWA 端 iPhone 自带 TTS 做，这里只返回文字
    print(f'[SPEAK] rule={rule} line={line}')
    return jsonify(ok=True, line=line)


# ----- /chat - Kimi 代理 Claude，避免 iPhone 直连 api.anthropic.com 被国内网络掐 -----
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return ('', 204)
    if not client:
        return jsonify(error='MOONSHOT_API_KEY not configured'), 500
    data = request.get_json() or {}
    messages = data.get('messages') or []
    system = data.get('system') or ''
    max_tokens = int(data.get('max_tokens') or 1024)
    model = data.get('model') or 'moonshot-v1-32k'
    # Kimi/Moonshot 是 OpenAI 兼容格式，system 走 messages 里第一条
    msgs = []
    if system:
        msgs.append({'role': 'system', 'content': system})
    for m in messages:
        if not m or not m.get('role') or m.get('content') is None:
            continue
        msgs.append({'role': m['role'], 'content': m['content']})
    try:
        r = client.chat.completions.create(
            model=model,
            messages=msgs,
            max_tokens=max_tokens,
        )
        text = r.choices[0].message.content
        return jsonify(ok=True, text=text, model=model)
    except Exception as e:
        print(f'[CHAT] kimi failed: {e}')
        return jsonify(ok=False, error=str(e)), 500


# ----- /email -----
@app.route('/email', methods=['POST', 'OPTIONS'])
def email():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json() or {}
    to = data.get('to', '')
    if not to:
        return jsonify(error='missing to'), 400
    print(f'[EMAIL] to={to} rule={data.get("rule_name")} reason={data.get("reason")}')
    return jsonify(ok=True, logged=True, note='SMTP not configured yet')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
