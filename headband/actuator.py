"""硬件动作模块：通过 GPIO 控制马达 / 蜂鸣器 / LED。

优先使用 Hobot.GPIO（地瓜 RDK 的 GPIO 库，API 与 RPi.GPIO 兼容），
导入失败则回退到 mock 模式（仅打日志），方便在普通笔记本上调试。
"""

import logging
import time

logger = logging.getLogger(__name__)

# 尝试加载 GPIO 库
_GPIO = None
try:
    import Hobot.GPIO as _GPIO  # type: ignore
    logger.info("GPIO 后端: Hobot.GPIO")
except Exception:
    try:
        import RPi.GPIO as _GPIO  # type: ignore
        logger.info("GPIO 后端: RPi.GPIO")
    except Exception:
        _GPIO = None
        logger.warning("未检测到 GPIO 库，使用 mock 模式（仅打日志）")


class Actuator:
    def __init__(self, pin_map: dict):
        """pin_map 例如 {"motor": 5, "buzzer": 6, "led": 13}"""
        self.pin_map = pin_map
        self.mock = _GPIO is None
        if not self.mock:
            try:
                _GPIO.setwarnings(False)
                _GPIO.setmode(_GPIO.BCM)
                for name, pin in pin_map.items():
                    _GPIO.setup(pin, _GPIO.OUT, initial=_GPIO.LOW)
                logger.info("GPIO 初始化完成: %s", pin_map)
            except Exception as e:
                logger.error("GPIO 初始化失败，降级 mock: %s", e)
                self.mock = True

    # ---------- 内部工具 ----------
    def _set(self, name: str, high: bool):
        pin = self.pin_map.get(name)
        if pin is None:
            logger.warning("未配置引脚: %s", name)
            return
        if self.mock:
            logger.info("[MOCK] %s pin=%s -> %s", name, pin, "HIGH" if high else "LOW")
            return
        try:
            _GPIO.output(pin, _GPIO.HIGH if high else _GPIO.LOW)
        except Exception as e:
            logger.warning("GPIO 输出失败 %s: %s", name, e)

    def _pulse(self, name: str, duration_ms: int):
        self._set(name, True)
        time.sleep(max(0, duration_ms) / 1000.0)
        self._set(name, False)

    # ---------- 公开方法 ----------
    def vibrate(self, duration_ms: int = 1000):
        logger.info("动作: vibrate %dms", duration_ms)
        self._pulse("motor", duration_ms)

    def buzz(self, duration_ms: int = 500):
        logger.info("动作: buzz %dms", duration_ms)
        self._pulse("buzzer", duration_ms)

    def led_flash(self, duration_ms: int = 300, times: int = 3):
        logger.info("动作: led_flash %dms x%d", duration_ms, times)
        for _ in range(max(1, times)):
            self._set("led", True)
            time.sleep(duration_ms / 1000.0)
            self._set("led", False)
            time.sleep(duration_ms / 1000.0)

    def stop_all(self):
        for name in self.pin_map:
            self._set(name, False)

    def cleanup(self):
        self.stop_all()
        if not self.mock:
            try:
                _GPIO.cleanup()
            except Exception as e:
                logger.warning("GPIO cleanup 出错: %s", e)

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
