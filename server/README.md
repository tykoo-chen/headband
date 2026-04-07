# AI 自律发带 - 云端 API

基于 Flask + Claude Vision (`claude-opus-4-5`) 的单文件后端，给硬件端（地瓜 RDK 发带）和 PWA 前端共用。

## 快速开始

```bash
cd server
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-xxxx
python app.py
```

默认监听 `0.0.0.0:5000`。可通过 `PORT` 环境变量改端口。

数据保存在同目录下的 `rules.json` / `events.json` / `deduct_log.json`，无需数据库。

## 端点一览

| 方法 | 路径        | 说明 |
|------|-------------|------|
| GET  | `/health`   | 健康检查 |
| GET  | `/rules`    | 获取规则列表 |
| POST | `/rules`    | 覆盖式更新规则列表（请求体为 JSON 数组） |
| GET  | `/events?limit=50` | 最近触发事件（最新在前） |
| POST | `/frame`    | 发带上传图片，返回硬件动作 |
| POST | `/test`     | 文本场景测试，走相同判断逻辑 |

## 从 RDK 发带端调用示例

multipart 上传：

```bash
curl -X POST http://<server-ip>:5000/frame \
  -F "image=@/tmp/frame.jpg"
```

base64 JSON 上传：

```bash
curl -X POST http://<server-ip>:5000/frame \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\": \"$(base64 -w0 /tmp/frame.jpg)\", \"media_type\": \"image/jpeg\"}"
```

返回示例：

```json
{
  "ok": true,
  "matched_rules": ["no_phone"],
  "fired_rules": ["no_phone"],
  "reason": "画面中出现了正在使用的手机",
  "actions": [
    {"type": "vibrate", "duration_ms": 1500, "intensity": 1.0},
    {"type": "buzzer",  "duration_ms": 600,  "freq_hz": 2200},
    {"type": "led",     "color": "red", "blink": 3}
  ]
}
```

发带端拿到 `actions` 后，依次驱动震动马达 / 蜂鸣器 / LED。

## 文本测试

```bash
curl -X POST http://localhost:5000/test \
  -H "Content-Type: application/json" \
  -d '{"scene": "用户正在低头玩手机，屏幕亮着抖音"}'
```

## 设计要点

- **冷却**：同一规则 30 秒内只触发一次，避免发带被连环惩罚。
- **通道**：`vibrate / buzzer / led` 是硬件指令，由发带端执行；`bark / wecom_bot / email / deduct` 是软通道，服务端直接执行。
- **安全**：建议在反向代理层加鉴权，本服务本身未做。
