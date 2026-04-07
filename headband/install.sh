#!/usr/bin/env bash
# AI 自律发带 - 一键安装脚本
set -e

echo "==> 升级 pip"
python3 -m pip install --upgrade pip

echo "==> 安装 Python 依赖"
python3 -m pip install requests opencv-python

echo "==> 安装 Hobot.GPIO（地瓜 RDK 专用，普通电脑可能装不上，可忽略错误）"
python3 -m pip install Hobot.GPIO || echo "[WARN] Hobot.GPIO 安装失败，将使用 mock GPIO"

echo ""
echo "==> 安装完成"
echo "请编辑 config.json，把 server_url 改成你的云端服务地址："
echo "    nano $(dirname "$0")/config.json"
echo ""
echo "手动运行：python3 main.py"
echo "开机自启：sudo cp headband.service /etc/systemd/system/ && sudo systemctl enable --now headband"
