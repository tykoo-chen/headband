"""摄像头模块：抽帧并压缩为 JPEG 字节流。

优先使用 OpenCV，失败则回退到 picamera2，再回退到 libcamera-jpeg 命令。
"""

import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)


class Camera:
    def __init__(self, width: int = 640, height: int = 480, jpeg_quality: int = 70):
        self.width = width
        self.height = height
        self.jpeg_quality = jpeg_quality
        self._backend = None  # "cv2" / "picamera2" / "libcamera"
        self._cap = None
        self._picam = None
        self._init_backend()

    def _init_backend(self):
        # 1) 尝试 OpenCV
        try:
            import cv2  # noqa
            cap = cv2.VideoCapture(0)
            if cap is not None and cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self._cap = cap
                self._backend = "cv2"
                logger.info("摄像头后端: OpenCV (cv2.VideoCapture)")
                return
            else:
                if cap is not None:
                    cap.release()
        except Exception as e:
            logger.warning("OpenCV 初始化失败: %s", e)

        # 2) 尝试 picamera2
        try:
            from picamera2 import Picamera2  # type: ignore
            picam = Picamera2()
            cfg = picam.create_still_configuration(main={"size": (self.width, self.height)})
            picam.configure(cfg)
            picam.start()
            self._picam = picam
            self._backend = "picamera2"
            logger.info("摄像头后端: picamera2")
            return
        except Exception as e:
            logger.warning("picamera2 初始化失败: %s", e)

        # 3) fallback libcamera-jpeg 命令
        self._backend = "libcamera"
        logger.info("摄像头后端: libcamera-jpeg (命令行)")

    def capture(self) -> bytes:
        """抽取一帧并返回 JPEG 字节流。失败抛出异常。"""
        if self._backend == "cv2":
            import cv2
            ok, frame = self._cap.read()
            if not ok or frame is None:
                raise RuntimeError("cv2 抽帧失败")
            frame = cv2.resize(frame, (self.width, self.height))
            ok, buf = cv2.imencode(
                ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            )
            if not ok:
                raise RuntimeError("cv2 JPEG 编码失败")
            return buf.tobytes()

        if self._backend == "picamera2":
            import io
            from PIL import Image  # picamera2 通常会带 PIL
            arr = self._picam.capture_array()
            img = Image.fromarray(arr)
            if img.mode != "RGB":
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=self.jpeg_quality)
            return buf.getvalue()

        if self._backend == "libcamera":
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                tmp_path = f.name
            try:
                cmd = [
                    "libcamera-jpeg", "-o", tmp_path,
                    "--width", str(self.width),
                    "--height", str(self.height),
                    "-q", str(self.jpeg_quality),
                    "-n", "-t", "200",
                ]
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
                with open(tmp_path, "rb") as fp:
                    return fp.read()
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        raise RuntimeError("未知摄像头后端")

    def close(self):
        try:
            if self._cap is not None:
                self._cap.release()
            if self._picam is not None:
                self._picam.stop()
        except Exception as e:
            logger.warning("关闭摄像头出错: %s", e)

    def __del__(self):
        self.close()
