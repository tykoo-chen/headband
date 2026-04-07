# 角色操作手册 📘

> 5 个角色，每人一节，照着 checklist 干就行。

- [A — 队长 / 产品](#a--队长--产品)
- [B — 硬件手](#b--硬件手)
- [C — 结构 / 3D 打印](#c--结构--3d-打印)
- [D — 软件 · 发带端](#d--软件--发带端)
- [E — 软件 · 服务端 + 惩罚](#e--软件--服务端--惩罚)

---

## A — 队长 / 产品

### 🎯 你的任务
- 总指挥，跑通流程，解决一切跨角色卡点
- 采购硬件（地瓜 RDK / 摄像头 / 震动马达 / 发带 / 焊接耗材）
- 设计"什么算摸鱼"的规则
- 招用户做测试 + 拍 demo
- **审核合并所有 PR**

### 📂 你要改的文件
| 文件 | 干啥 |
|---|---|
| `产品原型文档.md` | 更新需求 / 硬件清单 / 测试结论 |
| `README.md` | 更新整体介绍 / 链接 |
| `docs/` | 写流程文档 |
| `docs/images/` | 放产品照 / 测试照 |

### 🛠 常用操作
- **审 PR**：GitHub 网页 → Pull requests 标签 → 看 Files changed → 没问题点 **Merge pull request**
- **下指令**：群里 @ 对应的人，写清楚"今天要做完 XX"
- **发钱**：管账号，记录扣款流水

### 📅 Day 1 Checklist
- [ ] 上午：采购清单确认 + 下单 / 现场买
- [ ] 上午：召集 5 人开 30 分钟 Kickoff，对齐分工
- [ ] 中午：把所有人加成 GitHub collaborator
- [ ] 下午：定 3 条 MVP 规则（如：低头玩手机 / 离开座位 / 闭眼超过 10s）
- [ ] 晚上：跑通"端到端最小链路"（D 拍一张图 → E 收到 → A 看到记录）

### 📅 Day 2 Checklist
- [ ] 上午：组织联调
- [ ] 中午：找 2 个真人用户测试
- [ ] 下午：拍 demo 视频
- [ ] 晚上：路演彩排

---

## B — 硬件手

### 🎯 你的任务
- 焊接电路：摄像头 / 震动马达 / 电池 / 地瓜 RDK
- 把所有元件装到 C 打印的外壳里
- 把发带本体组装好
- **拍组装过程的照片** 上传到 `docs/images/`

### 📂 你要改的文件
> 你**几乎不用碰代码**。只要：
- 在 `docs/images/hardware/` 下放组装照片
- 必要时在 `产品原型文档.md` 备注"实际接线和文档不一样的地方"

### 🛠 常用操作 / 工具清单
| 工具 | 用途 |
|---|---|
| 烙铁 + 焊锡 | 焊线 |
| 热熔胶枪 | 固定元件 |
| 万用表 | 量电压、查通断 |
| 杜邦线 / 排针 | 接线 |
| 双面胶 / 扎带 | 固定走线 |

### 📅 Day 1 Checklist
- [ ] 跟 A 对硬件清单，缺什么立刻报
- [ ] 焊好摄像头到 RDK 的 CSI / USB 线
- [ ] 焊好震动马达到 GPIO（接三极管或 MOSFET 驱动，不要直接接 GPIO）
- [ ] 通电点亮 RDK
- [ ] 配合 D：让 D 在 RDK 上跑一段测试代码，确认摄像头能拍到图、马达能震
- [ ] 拍照上传 `docs/images/hardware/`

### 📅 Day 2 Checklist
- [ ] 把所有元件装进 C 的外壳
- [ ] 缝 / 粘到发带上
- [ ] 真人佩戴测试舒适度
- [ ] 准备一套备用线，路演当场掉线能救场
- [ ] 拍最终成品照

> 📖 详细硬件清单和接线图见 [`产品原型文档.md`](../产品原型文档.md)

---

## C — 结构 / 3D 打印

### 🎯 你的任务
- 量好元件尺寸（摄像头 + RDK + 电池 + 马达）
- 在 Fusion360 / Tinkercad 里建外壳
- 切片 + 打印
- 配合 B 装配，必要时返工

### 📂 你要改的文件
| 文件 | 干啥 |
|---|---|
| `hardware/3d/*.f3d`、`*.step` | 源文件（你自己建） |
| `hardware/3d/*.stl` | 切片用的模型 |
| `docs/images/3d/` | 渲染图 + 实物照 |

> ⚠️ STL 文件如果大于 10MB，**不要 commit**，发到群文件里，本仓库只保留小尺寸预览。

### 🛠 工作流
1. **量尺寸** → 用游标卡尺，至少量 3 次取平均
2. **建模** → 留 0.3mm 公差，螺丝孔留 M2 / M3
3. **切片** → Cura / Bambu Studio
4. **打印** → PLA，0.2mm 层高，20% 填充
5. **试装** → 装不上立刻改 → 重新打

### 📅 Day 1 Checklist
- [ ] 拿到所有元件实物，量尺寸
- [ ] 出第一版外壳建模
- [ ] 打第一版（容忍粗糙）
- [ ] 和 B 试装，标记需要改的地方

### 📅 Day 2 Checklist
- [ ] 上午：出第二版（修公差 + 加散热孔）
- [ ] 中午：再打一版
- [ ] 下午：装配 + 上漆 / 贴 logo（可选）

---

## D — 软件 · 发带端

### 🎯 你的任务
- 在地瓜 RDK 上跑代码：摄像头采图 → POST 给云端 → 收到指令震动
- **没有硬件时，先在自己笔记本上跑 mock 版本**

### 📂 你要改的文件
| 文件 | 干啥 |
|---|---|
| `headband/main.py` | 主循环：采图 + 上传 + 收指令 |
| `headband/camera.py` | 摄像头封装（真机 + mock） |
| `headband/uploader.py` | HTTP 上传逻辑 |
| `headband/vibrator.py` | 震动马达控制 |
| `headband/config.py` | 服务器地址 / 设备 ID 等配置 |

> ❌ 不要碰 `server/` 和 `demo/`！有需要让 E 改。

### 🛠 在自己笔记本上跑 mock 版本

```bash
cd headband
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 main.py --mock
```

`--mock` 模式下：
- 摄像头 = 用电脑自带 webcam（cv2.VideoCapture(0)），如果没有 webcam 就读 `headband/sample.jpg`
- 震动马达 = 在终端打印 `[VIBRATE] 0.5s`
- 服务器地址 = 默认 `https://self-discipline-nine.vercel.app/api`（或本地 `http://localhost:5000`）

### 🛠 常用命令
```bash
# 跑 mock
python3 main.py --mock

# 跑真机（在 RDK 上）
python3 main.py --device

# 单独测摄像头
python3 -m camera --test

# 单独测震动
python3 -m vibrator --test
```

### 📅 Day 1 Checklist
- [ ] 在自己电脑跑通 `main.py --mock`
- [ ] 把图片成功 POST 到 E 的 `/api/events` 接口
- [ ] 拿到 RDK 实机，配 SSH，传代码
- [ ] 真机跑通摄像头
- [ ] 真机跑通震动马达（配合 B）

### 📅 Day 2 Checklist
- [ ] 端到端联调（真摄像头 → 云端 → 真震动）
- [ ] 优化采集频率（建议 1 帧 / 2 秒）
- [ ] 加断网重试逻辑
- [ ] 写一份 `headband/README.md` 教别人怎么跑

---

## E — 软件 · 服务端 + 惩罚

### 🎯 你的任务
- 维护 Flask 后端 `server/`
- 提供 API 给 D 上传事件、给 PWA 拉规则 / 历史
- 接惩罚通道（扣钱 / 微信通知）
- 改 `demo/` 前端少量 bug + 联调

### 📂 你要改的文件
| 文件 | 干啥 |
|---|---|
| `server/app.py` | Flask 主入口 |
| `server/routes/*.py` | API 路由 |
| `server/punish.py` | 扣钱 / 通知逻辑 |
| `server/requirements.txt` | Python 依赖 |
| `demo/*.html`、`demo/*.js` | PWA 前端小修小补 |

> ❌ 不要碰 `headband/`！有需要让 D 改。

### 🛠 本地跑 Flask

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
# 默认 http://localhost:5000
```

测试一个接口：
```bash
curl -X POST http://localhost:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","label":"phone","ts":1700000000}'
```

### 🛠 部署到 Vercel
> 项目已经接好 Vercel，**push 到 main 自动部署**。

1. 你写完代码，commit + push 到 `e/server` 分支
2. 开 PR 让 A 合并到 `main`
3. 合并后 Vercel 自动构建 → 1~2 分钟后线上更新
4. 检查：<https://self-discipline-nine.vercel.app>

> 🔑 **如果用到 API Key**：在 Vercel 网页 → Project → Settings → Environment Variables 添加，**绝对不要写在代码里**。

### 🛠 PWA 前端调试
```bash
cd demo
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

### 📅 Day 1 Checklist
- [ ] 本地跑通 Flask
- [ ] 实现 4 个核心接口：
  - `POST /api/events`（D 上传事件）
  - `GET /api/events`（PWA 拉历史）
  - `GET /api/rules`、`POST /api/rules`（规则增删改）
  - `GET /api/balance`（剩余押金）
- [ ] 部署到 Vercel
- [ ] 给 D 一个联调 URL

### 📅 Day 2 Checklist
- [ ] 接惩罚通道（最简版：扣本地 `deduct_log.json` + 给微信发消息）
- [ ] 修 PWA 小 bug（配合 A 看测试反馈）
- [ ] 加日志，方便路演时讲解
- [ ] 写 `server/README.md`

---

## 🤝 跨角色协作小贴士

| 场景 | 谁找谁 |
|---|---|
| D 不知道接口长啥样 | 找 E 要 API 文档 |
| E 没法测端到端 | 找 D 跑 mock 上报 |
| B 装不进外壳 | 找 C 改模型 |
| C 不知道元件尺寸 | 找 B 量 |
| 任何人卡住超过 15 分钟 | **找 A** |

> 💡 **黄金法则**：宁可多说一句，不要少说一句。群里多 @，多对齐，少返工。
