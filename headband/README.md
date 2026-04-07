# AI 自律发带 - 客户端

运行在地瓜 RDK X3 开发板上的 Python 客户端。负责定时抽帧、上传云端、根据云端返回的动作驱动震动马达 / 蜂鸣器 / LED。

## 硬件接线

| 元件 | GPIO (BCM) | 接线说明 |
| --- | --- | --- |
| 震动马达 | GPIO 5 | GPIO -> 1k 电阻 -> NPN 三极管/MOS 管基极；马达接 VCC 与三极管集电极之间，发射极接 GND；马达两端并联续流二极管 |
| 蜂鸣器 | GPIO 6 | 有源蜂鸣器同上用三极管驱动；或直接 GPIO -> 220Ω 电阻 -> 蜂鸣器 -> GND（电流不要超过引脚上限） |
| LED | GPIO 13 | GPIO -> 220Ω 电阻 -> LED 正极 -> LED 负极 -> GND |

> 注意：地瓜 RDK X3 的 GPIO 输出电流有限，**不要直接驱动马达**，必须用 MOS/三极管。共地（板子 GND 与外部电源 GND 相连）。

## 文件结构

```
headband/
├── main.py              # 主程序入口（主循环）
├── camera.py            # 摄像头抽帧（cv2 / picamera2 / libcamera）
├── uploader.py          # HTTP 上传
├── actuator.py          # GPIO 动作执行（Hobot.GPIO，自动 mock 兜底）
├── config.json          # 配置文件
├── install.sh           # 一键安装依赖
├── headband.service     # systemd 单元
└── README.md
```

## 安装

```bash
cd headband
bash install.sh
nano config.json   # 把 server_url 改成你的云端地址
```

## 手动运行

```bash
python3 main.py
```

正常输出示例：

```
2026-04-07 10:00:00 [INFO] headband: 启动 AI 自律发带客户端 ...
2026-04-07 10:00:03 [INFO] headband: 抽帧完成 size=23456 bytes
2026-04-07 10:00:04 [INFO] headband: 命中规则: 抽烟
2026-04-07 10:00:04 [INFO] headband: 执行 2 个动作: ['vibrate', 'buzz']
```

按 `Ctrl+C` 优雅退出。

## 开机自启

```bash
sudo cp headband.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now headband
```

> 如果 headband 目录不在 `/root/headband`，先编辑 `headband.service` 里的 `WorkingDirectory` 和 `ExecStart` 路径。

## 查看日志

```bash
journalctl -u headband -f
```

## 配置说明 (`config.json`)

| 字段 | 含义 |
| --- | --- |
| `server_url` | 云端服务地址，例如 `http://192.168.1.10:5000` 或 `https://xxx.vercel.app` |
| `device_id` | 设备唯一 ID，云端用来区分多台发带 |
| `frame_interval_seconds` | 抽帧间隔（秒） |
| `jpeg_quality` | JPEG 压缩质量 1-100 |
| `gpio.motor` / `gpio.buzzer` / `gpio.led` | BCM 编号引脚 |

## 与云端的协议

- **请求**：`POST {server_url}/frame`，`multipart/form-data`
  - `image`: JPEG 文件
  - `device_id`: 字符串
- **响应**：JSON
  ```json
  {
    "matched_rules": [{"id": "smoke", "name": "抽烟"}],
    "actions": [
      {"type": "vibrate", "duration_ms": 1500},
      {"type": "buzz",    "duration_ms": 800},
      {"type": "led_flash", "duration_ms": 300, "times": 3}
    ]
  }
  ```
- 客户端按顺序执行 actions，每个动作之间间隔 100ms。

## 故障排查

### 1. 摄像头打不开
- 检查 `ls /dev/video*`，确认设备存在；
- `sudo usermod -aG video $USER` 然后重新登录；
- 试试 `python3 -c "import cv2; print(cv2.VideoCapture(0).read()[0])"`；
- 实在不行用 `libcamera-jpeg -o test.jpg` 验证硬件本身是否正常。

### 2. GPIO 权限不足
- systemd 已用 `User=root`；手动跑请用 `sudo python3 main.py`；
- 或把用户加入 gpio 组：`sudo usermod -aG gpio $USER`。

### 3. 网络连不上
- `ping` 一下 server_url 的域名/IP；
- 在板子上 `curl -v http://your-server/frame` 看是否 405/404（说明能通，只是方法不对）；
- 检查 `config.json` 里没有打错端口；
- 客户端遇到网络异常**不会崩溃**，会继续下一轮循环并打印 WARN。

### 4. 没有 GPIO 库（在笔记本上调试）
- `actuator.py` 会自动降级到 mock 模式，所有动作只打印日志，不会报错。
