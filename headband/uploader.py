"""上传模块：把抽取的帧 POST 给云端服务。"""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def upload_frame(server_url: str, image_bytes: bytes, device_id: str) -> Optional[dict]:
    """上传一帧图像到 /frame 端点。

    成功返回服务端 JSON dict；失败返回 None。
    """
    url = server_url.rstrip("/") + "/frame"
    files = {
        "image": ("frame.jpg", image_bytes, "image/jpeg"),
    }
    data = {"device_id": device_id}
    try:
        resp = requests.post(url, files=files, data=data, timeout=10)
        if resp.status_code != 200:
            logger.warning("上传失败 status=%s body=%s", resp.status_code, resp.text[:200])
            return None
        return resp.json()
    except requests.RequestException as e:
        logger.warning("上传异常: %s", e)
        return None
    except ValueError as e:
        logger.warning("响应不是合法 JSON: %s", e)
        return None
