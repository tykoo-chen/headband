# AI 自律发带 🧠⚡

> 一条会"提醒"你别走神的发带：摄像头看你在干嘛，AI 判断你是不是在摸鱼，摸鱼就震你一下 + 扣你钱。

🌐 在线体验（PWA）：<https://self-discipline-nine.vercel.app>
📦 GitHub：<https://github.com/tykoo-chen/headband>

![效果图占位](docs/images/hero.png)
> （效果图待补：B 拍组装照，A 拍佩戴照，放到 `docs/images/` 下）

---

## ✨ 一句话介绍

**AI 自律发带** = 一个戴在头上的小摄像头 + 云端 AI + 手机 PWA App，实时检测你是否在专注做该做的事，否则发带震动 + 扣你提前押的钱。

---

## 🏗 整体架构

```
   ┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
   │   发带硬件          │  HTTP   │   云端服务          │  HTTP   │   PWA 手机网页      │
   │  (headband/)       │ ──────▶ │  (server/, Flask)  │ ◀────── │  (demo/, 部署 Vercel)│
   │  地瓜 RDK + 摄像头   │         │  规则 / 事件 / 扣款  │         │  设规则 / 看记录    │
   │  + 震动马达         │ ◀────── │                    │ ──────▶ │  + 惩罚通道         │
   └────────────────────┘  指令    └────────────────────┘  推送   └────────────────────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │ 惩罚通道     │
                                   │ (扣钱 / 通知)│
                                   └─────────────┘
```

数据流（一句话版）：**摄像头拍照 → 发带本地预处理 → POST 到云端 → AI 判定 → 不专注则下发震动指令 + 扣款 + PWA 显示记录**。

---

## 📂 目录结构

| 目录 / 文件 | 干什么的 | 谁负责 |
|---|---|---|
| `demo/` | PWA 前端（HTML/JS），用户在手机上看到的界面 | E（少量改动） |
| `server/` | Python Flask 云端服务，规则 / 事件 / 扣款 API | E |
| `headband/` | 发带本地代码（地瓜 RDK 上跑的 Python） | D |
| `产品原型文档.md` | 产品需求 + 角色分工 + 硬件清单 | A |
| `docs/` | 团队协作文档 | 全员 |
| `README.md` | 本文件 | A |

---

## 👥 团队角色（5 人）

| 代号 | 角色 | 一句话职责 | 改哪里 |
|---|---|---|---|
| **A** | 队长 / 产品 | 采购、规则设计、用户测试，不写代码 | `产品原型文档.md`、`docs/` |
| **B** | 硬件手 | 焊接、组装发带本体 | 不改代码，拍照上传 `docs/images/` |
| **C** | 结构 / 3D 打印 | 外壳建模、打印 | `hardware/3d/`（如有） |
| **D** | 软件 - 发带端 | 摄像头采集 + 上传 + 接收震动指令 | `headband/` |
| **E** | 软件 - 服务端 | Flask API + 惩罚通道 + 前端联调 | `server/`、`demo/` |

详见 [`docs/role-playbook.md`](docs/role-playbook.md)。

---

## 🚀 快速开始

### 我只想试试 PWA
打开手机浏览器，访问 👉 <https://self-discipline-nine.vercel.app>
（建议 Safari / Chrome，加到主屏幕即可像 App 一样用）

### 我是队员，第一次拿到代码
1. 注册 GitHub 账号：<https://github.com/join>
2. 把账号发给队长 A，让他把你加成 collaborator
3. 装 GitHub Desktop：<https://desktop.github.com/>
4. 打开 GitHub Desktop → File → Clone Repository → 输入 `tykoo-chen/headband`
5. 看 [`CONTRIBUTING.md`](CONTRIBUTING.md) 里的"第一次设置"

### 我是开发者，想跑后端
```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 我是发带端开发者
```bash
cd headband
python3 main.py --mock   # 没有硬件时用 mock 模式
```

---

## 📚 详细文档

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — **团队协作规范（必读）**
- [`docs/quickstart-for-beginners.md`](docs/quickstart-for-beginners.md) — 零基础 Git 速成
- [`docs/role-playbook.md`](docs/role-playbook.md) — 5 个角色每天干什么
- [`产品原型文档.md`](产品原型文档.md) — 产品原型 + 硬件清单

---

## 📅 时间线

- Day 1：硬件焊接 + 后端 API 跑通 + PWA 上线
- Day 2：联调 + 用户测试 + Demo 拍摄

---

## 📝 License

仅作为黑客松 Demo 使用。
