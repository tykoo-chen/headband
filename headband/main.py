"""AI 自律发带 - 主程序入口。

主循环：定时抽帧 -> 上传云端 -> 解析 actions -> 执行硬件动作。
"""

import json
import logging
import os
import signal
import sys
import time

from camera import Camera
from uploader import upload_frame
from actuator import Actuator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("headband")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

_running = True


def _handle_sigint(signum, frame):
    global _running
    logger.info("收到信号 %s, 准备退出...", signum)
    _running = False


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_actions(actuator: Actuator, actions: list):
    """按顺序执行 action 列表，每个动作之间间隔 100ms。"""
    for i, act in enumerate(actions):
        atype = act.get("type")
        dur = int(act.get("duration_ms", 500))
        try:
            if atype == "vibrate":
                actuator.vibrate(dur)
            elif atype == "buzz":
                actuator.buzz(dur)
            elif atype in ("led", "led_flash"):
                times = int(act.get("times", 3))
                actuator.led_flash(dur, times=times)
            else:
                logger.warning("未知动作类型: %s", atype)
        except Exception as e:
            logger.exception("执行动作出错 %s: %s", act, e)
        if i < len(actions) - 1:
            time.sleep(0.1)


def main():
    signal.signal(signal.SIGINT, _handle_sigint)
    signal.signal(signal.SIGTERM, _handle_sigint)

    cfg = load_config(CONFIG_PATH)
    server_url = cfg["server_url"]
    device_id = cfg.get("device_id", "headband-01")
    interval = float(cfg.get("frame_interval_seconds", 3))
    jpeg_quality = int(cfg.get("jpeg_quality", 70))
    gpio_cfg = cfg.get("gpio", {})

    logger.info("启动 AI 自律发带客户端 device_id=%s server=%s interval=%ss",
                device_id, server_url, interval)

    camera = Camera(jpeg_quality=jpeg_quality)
    actuator = Actuator(gpio_cfg)

    try:
        while _running:
            t0 = time.time()
            try:
                frame = camera.capture()
                logger.info("抽帧完成 size=%d bytes", len(frame))
            except Exception as e:
                logger.warning("抽帧失败: %s", e)
                _sleep_until(t0 + interval)
                continue

            resp = upload_frame(server_url, frame, device_id)
            if resp is None:
                logger.info("上传失败或无响应，跳过本轮")
                _sleep_until(t0 + interval)
                continue

            matched = resp.get("matched_rules", []) or []
            actions = resp.get("actions", []) or []
            if matched:
                names = ", ".join(r.get("name", r.get("id", "?")) for r in matched)
                logger.info("命中规则: %s", names)
            else:
                logger.info("未命中规则")

            if actions:
                logger.info("执行 %d 个动作: %s", len(actions),
                            [a.get("type") for a in actions])
                execute_actions(actuator, actions)
            else:
                logger.info("无动作")

            _sleep_until(t0 + interval)
    finally:
        logger.info("清理资源...")
        try:
            actuator.cleanup()
        except Exception:
            pass
        try:
            camera.close()
        except Exception:
            pass
        logger.info("已退出")


def _sleep_until(deadline: float):
    """间隔睡眠，期间响应退出信号。"""
    while _running:
        remain = deadline - time.time()
        if remain <= 0:
            return
        time.sleep(min(remain, 0.2))


if __name__ == "__main__":
    main()
