# Variant Prompt Package — AI 自律发带 前端重设计

> 将此文档完整粘贴给 Variant（或任何 AI UI 生成工具）。目标：在完全保留现有功能、函数名、state 结构、localStorage key、网络请求逻辑、service worker 注册的前提下，把 `demo/index.html` 的视觉层重写成一个现代、有力量感、略带"辛辣警告"气质的移动端 PWA。

---

## 1. 产品定位

**AI 自律发带** 是一套"硬件 + PWA"的自律系统。用户佩戴一个带摄像头的发带，板子（ESP32/Raspberry Pi 类设备，跑 `server.py`）以 HTTP 暴露 `/frame`（当前画面 JPEG）和 `/scene`（Kimi 视觉模型生成的场景描述 + base64 帧）两个接口；PWA 每 5 秒拉取 `/scene`，把场景描述连同用户自定义的规则一起发给 Claude，Claude 返回哪些规则被触发，触发即执行用户预设的惩罚（震动、蜂鸣、LED、推送、扣钱、社死等）。PWA 本体是整个系统的"控制中心"，承载规则管理、实时监控、战绩统计、以及好友社交博弈（奖池/打卡/契约/PK/互设规矩）。

气质关键词：**自律、辛辣、社死警告、不废话的私教、略带游戏化**。用户不想要柔和的"习惯养成 app"——他们要的是能把自己管死的工具。

---

## 2. 核心页面清单（底部 Tab Bar + 全局模块）

PWA 是单页、移动端优先（`max-w-md mx-auto`），底部 4 个 Tab + 右上角设置齿轮 + 若干弹窗。

| Tab | id | 图标 | 中文 | 作用 |
|---|---|---|---|---|
| 1 | `plan` | 🎯 | 教练 | LLM 反向提问式规划助手，产出可采纳的 todos/donts |
| 2 | `rules` | 📋 | 规则 | 用户自定义行为规则的增删改查 |
| 3 | `monitor` | 📷 | 监控 | 实时画面 + 场景描述 + 规则匹配日志 + 战绩统计 |
| 4 | `friends` | 👥 | 好友 | 多人游戏中心（奖池/打卡/契约/PK/互设规矩） |

全局元素：
- **顶部 header**：固定，标题"AI 自律发带"+ 副标题（"未连接 API" 或 "✅ API 已连接"）+ 右上角 ⚙️ 齿轮打开设置弹窗
- **设置弹窗 `#settings-modal`**：两个字段（Anthropic API Key、发带地址），保存/取消
- **规则编辑弹窗 `#rule-modal`**：全字段表单，新建和编辑共用
- **游戏类型选择器 `#game-picker`**：从底部滑出的 5 种游戏类型卡片
- **游戏创建表单 `#game-form`**：动态字段表单，按游戏类型渲染

---

## 3. 每个页面的完整功能清单

### 3.1 教练页（`data-page="plan"`）

**顶部**
- 标题 `🎯 AI 规划教练`
- 右上角"重开"按钮 → `resetPlan()`，清空 `state.planHistory` 和 `#plan-result`
- 一句话说明："告诉 AI 你想达成什么。AI 会先反问你几个问题，把目标拆清楚，再给出可执行方案和规则。"

**聊天区 `#plan-chat`**
- 空状态：🎯 emoji + "先说一句你想达成什么" + 例子
- 消息气泡：用户（橙色 `bubble-user`）右对齐，助手（灰 `bubble-ai`）左对齐
- 助手消息渲染时**必须剥离 ```json 代码块**（`m.content.replace(/```json[\s\S]*?```/g, '')`），只显示人话部分
- 消息来自 `state.planHistory`

**方案结果区 `#plan-result`**
- `sendPlan()` 后如果助手回复里匹配到 JSON（`/```json\s*([\s\S]*?)```/` 或 `/\{[\s\S]*"donts"[\s\S]*\}/`），调用 `renderPlanResult(plan)` 渲染
- 结构：
  - `summary` 卡片（橙色调，顶部图钉 📌）
  - `todos` 列表（绿色调，每项有 name / detail / 🕒 time_desc）标题"✅ 要做的事（N）"
  - `donts` 列表（红色调，每项有 name / 识别条件 / 🕒 time_desc / 建议惩罚 chip）标题"🚫 不能做的事（N）"
  - 底部"一键采纳为规则（N 条）"按钮 → `adoptAllDonts(encoded)` 把 donts base64 解码并 push 进 `state.rules`

**输入栏 `#plan-input-bar`**
- 固定在底部 tab bar 上方（`fixed bottom-16`），单行可自适应的 textarea + 橙色"发送"按钮
- `sendPlan()`：追加用户消息 → push "思考中..." → `callClaude(msgs, PLAN_SYSTEM)` → 替换 loading → 保存 `planHistory` → 尝试解析 JSON → `renderPlanResult`

**PLAN_SYSTEM prompt**（严厉、反问式，分 3 阶段）——见源码 `PLAN_SYSTEM` 常量，Variant **不得修改**这个 system prompt 字符串。

### 3.2 规则页（`data-page="rules"`）

**顶部**
- 标题 `📋 我的规则` + 右上角橙色"+ 新建"按钮 → `newRule()`

**列表 `#rules-list`**
- 空状态：📋 emoji + "还没有规则" + "去'规划'页让 AI 帮你生成，或手动新建"
- 每条规则卡片：
  - `r.name`（加粗）
  - `r.condition`（灰色次行）
  - 右上角复选框 `toggleRule(i)` 控制 `r.enabled`
  - 底部元信息：`🕒 r.time_desc · N 项惩罚`
  - 两个按钮："编辑" → `editRule(i)`，"删除" → `deleteRule(i)`

**规则编辑弹窗 `#rule-modal`**（新建和编辑复用）
- 标题 `#rule-modal-title`（"新建规则" / "编辑规则"）
- 字段：
  - **规则名称** `#rule-name`（text）
  - **触发条件** `#rule-condition`（textarea，placeholder "画面中我正在抽烟或手里有点燃的香烟"）
  - **类型** `#rule-type`（select）："instant" 即时违规 / "window" 任务窗口
  - **⏰ 生效时间** `#rule-time-preset`（select）：
    - `always` 全天任何时候
    - `hours` 每天某时段
    - `weekdays` 仅工作日某时段
    - `weekends` 仅周末某时段
    - `daily_before` 每天某时间之前
    - `daily_after` 每天某时间之后
  - **时间范围输入** `#time-range-box`（hidden；hours/weekdays/weekends 时显示）：`#rule-time-start` + "→" + `#rule-time-end`（两个 type="time"）
  - **单时间点输入** `#time-single-box`（hidden；daily_before/after 时显示）：`#rule-time-single`（type="time"）
  - **⚠️ 选择惩罚（多选）** `#punish-options`：12 张 `PUNISHMENTS` 卡片，每张 `<label class="punish-card">` 带 checkbox、icon、name、level、desc，点中后 `.checked` 样式（橙底橙边）
- 两个按钮："取消" → `closeRuleModal()`，橙色"保存" → `saveRule()`
- `saveRule()` 验证 name/cond/至少一个惩罚，调用 `buildTimeScopeFromForm()` 生成 `{scope, desc}`，写入 `state.rules`

**PUNISHMENTS 数组**（12 项，按危险等级分色）
```js
🟢 vibrate 发带震动 / buzzer 发带蜂鸣 / led LED 闪光
🟡 bark 推送通知 / email 邮件提醒
🟠 wecom 企微钉钉群通报 / sms 短信监督人 / social 微博朋友圈打卡失败
🔴 deduct 扣押金 / donate 强制捐款 / lock 锁电脑
🟣 release 释放质押文件（不可逆）
```
视觉上应该按 level 分段用不同色带区分。

### 3.3 监控页（`data-page="monitor"`）

**顶部**
- 标题 `📷 实时监控`
- `#board-status`：`🔗 http://...` 或 `⚠️ 未配置发带地址`

**视频预览区**
- 黑底 `aspect-video` 容器
- `<img id="board-frame">` 显示板子画面（hidden 当无地址）
- `<div id="board-placeholder">` 占位文字"未连接发带 / 右上角 ⚙️ 填入板子地址"

**控制按钮组**
- `#monitor-toggle` → `toggleMonitor()`：两态，"▶️ 开始监控" / "⏸ 停止监控"
- 旁边灰色按钮 `🔍 立刻检测一次` → `pollSceneOnce()`

**当前场景卡片**
- `👀 当前看到 <span id="current-scene-time">(5秒前)</span>`
- `#current-scene`：Kimi 返回的文字描述，loading 时"🔍 正在读取画面..."，错误时红色 ❌

**匹配日志 `#monitor-log`**
- 每次 `runDetection()` 插入一条卡片到列表顶部，最多 10 条
- 卡片包含：缩略图（base64 JPEG，`float-right w-20 h-14`）、时间戳、状态（`🔍 匹配规则中...` → `✅ 未触发任何规则` 或 `🚨 触发 N 条规则`）、原始场景引用、触发的规则名 + 惩罚 chip 列表
- 触发时调用 `navigator.vibrate([300, 100, 300, 100, 600])`

**战绩区（并入监控页下方）**
- `📊 我的战绩` 标题
- 3 个统计卡片：今日触发（橙）、连续自律天（绿）、累计触发（灰）
- "📉 最近 7 天" 柱状图（红=有触发，绿=0 触发）
- "🏆 最常违规的事"（TOP 5，按次数倒序）
- "清空战绩记录" 低调按钮 → `clearEvents()`
- 空状态："还没有任何触发记录 / 去上面模拟检测试试"

### 3.4 好友页（`data-page="friends"`）

**身份卡**（橙→红渐变大卡片）
- `${myName} · ${myId}`（myId 形如 `U` + 6 位大写随机）
- `🔥 N 天自律`（大字）
- `今日触发 X 次 · 免罚卡 Y 张`
- 右侧大 emoji：streak ≥ 7 显示 🏆，≥ 3 显示 ⭐，否则 💪
- 两个半透明按钮："✏️ 改名" → `editMyName()`，"📤 战报" → `shareMyStats()`

**创建 / 加入按钮组**
- 橙色"➕ 创建游戏" → `openCreateGame()` 打开游戏类型选择器
- 黑色"🔗 加入邀请" → `openJoinGame()`（`prompt` 粘贴 base64 邀请文本）

**我的游戏列表**
- 空状态：虚线边框卡片"还没有游戏 / 创建一个或加入好友的邀请"
- 标题：`我的游戏（N）`
- 每个游戏渲染 `renderGameCard(g)` —— 按 `g.type` 五种类型有不同的 body 和 footer

**GAME_TYPES（5 种）**
| type | icon | name | desc | 默认 config |
|---|---|---|---|---|
| `pool` | 💰 | 奖池对赌 | 每人押一笔钱，到期触发次数最少者通吃 | `{stake:10, days:7}` |
| `checkin` | 📅 | 打卡接力 | 每天每人都要打卡，断一人全队清零 | `{days:30}` |
| `contract` | 📜 | 自律契约 | 公开承诺一个目标，违约自动触发约定代价 | `{days:30, penalty:'...'}` |
| `duel` | ⚔️ | PK 对战 | N 天内触发次数最少的人赢 | `{days:7}` |
| `ruleset` | 🧷 | 互设规矩 | 别人给你写一条规则，N 天内不可删 | `{days:7, rule:'...'}` |

**每种游戏卡片的特色**
- `pool`：大字显示总押金 `¥N`、参与人数、剩余天数、每人押金；成员列表显示违规次数；"结算"按钮 → `settleGame(id)`
- `checkin`：大字"第 N 天"、接力人数、目标天数；成员列表显示今日是否已打卡（绿✅/灰⏳）；未打卡时显示"打卡"按钮 → `checkinGame(id)`，已打卡显示"✅ 今日已打卡"
- `contract`：黑底卡片显示承诺内容、立约人、见证人、约定代价、剩余天数；违约后显示红色"⚠️ 已违约，控制权已移交给见证人"；按身份（iAmCreator / iAmWitness）显示不同按钮：
  - 未违约 + creator：`承认违约` + `达成`
  - 未违约 + witness：`举报 TA 违约了`
  - 未违约 + 其他：`围观中`
  - 已移交 + witness：`⚡ 执行惩罚` + `😇 饶 TA`
  - 已移交 + creator：`等待 XX 裁决…`
- `duel`：剩余天数 + 成员按违规数升序排名（第一名带 👑）；"结算"按钮
- `ruleset`：黄底卡片显示规则内容、设定人、锁定天数；未采纳显示"采纳到我的规则"按钮 → `acceptGame(id)`；已采纳显示绿色"✅ 已采纳，剩 N 天解锁"

每张卡片右上角有"🔗 邀请"按钮 → `shareGame(id)`，底部 footer 最右是灰色"删"按钮 → `deleteGame(id)`

**游戏类型选择器 `#game-picker`**
- 从底部滑出的 bottom sheet
- 标题"选择游戏类型" + 关闭 ×
- 5 张大卡片（icon 3xl + name + desc + 橙色 › 箭头），点击调用 `createGame(type)` → `openGameForm(type)`

**游戏创建表单 `#game-form`**
- 从底部滑出的 bottom sheet
- 顶部固定 header：icon + name + desc + 关闭 ×
- 中间动态字段（根据 `FORM_FIELDS[type]`）：
  - `pool`: name(text, req) + stake(number, 10) + days(number, 7)
  - `checkin`: name(text, req) + days(number, 30)
  - `contract`: name(text, req) + text(textarea, req) + penalty(textarea, req) + days(number, 30)
  - `duel`: name(text, req) + days(number, 7)
  - `ruleset`: name(text, req) + rule(textarea, req) + days(number, 7)
- 必填字段标签后加红色 `*`
- 底部固定两个按钮："取消" + 橙色"创建并邀请" → `submitGameForm(type)` → `finalizeGame(type, name, cfg)` → 自动调用 `shareGame(game.id)`

**邀请分享机制**
```js
const payload = btoa(unescape(encodeURIComponent(JSON.stringify(g))));
// 文本格式：
// 【AI 自律发带 · 游戏邀请】
// 💰 名称
// 奖池对赌 · N 人已加入
// 复制这段发给好友 → 在好友 Tab 点"加入邀请"粘贴：
// ---
// <base64 payload>
```
- 优先 `navigator.share()`，降级 `navigator.clipboard.writeText()`
- 加入时正则 `/([A-Za-z0-9+/=]{40,})/` 提取 base64，解码合并 members

### 3.5 设置弹窗 `#settings-modal`

- 标题"设置"
- **Anthropic API Key**（type=password，placeholder `sk-ant-...`）+ 小字"仅存在你手机本地，用于规则匹配"
- **发带地址（板子 IP）**（placeholder `http://192.168.50.197:5000`）+ 小字"板子上 server.py 跑起来后填这里"
- "取消" + 橙色"保存" → `saveSettings()`

---

## 4. 数据模型 `state`

```js
const state = {
  apiKey: localStorage.getItem('apiKey') || '',              // Anthropic API Key
  boardUrl: (localStorage.getItem('boardUrl') || '').replace(/\/$/, ''),  // 板子 HTTP 地址
  chatHistory: [...],    // 教练 tab 的老 chat（现已并入 plan）
  planHistory: [...],    // 规划对话历史 [{role, content}]
  rules: [...],          // 见下
  events: [...],         // 触发事件 [{ts, rule_id, rule_name, reason, punishments, snapshot_text, snapshot_image}]
  games: [...],          // 见下
  feed: [...],           // Timeline [{ts, actor, type?, text}]，上限 200
  mercyCards: 0,         // 免罚卡数量（forgiveContract 时 +1）
  myId: 'U' + 6位大写随机字符,  // 持久化到 localStorage
  myName: '',            // 昵称
  editingRule: null,     // 当前编辑的规则 index，null = 新建
};
```

**Rule 结构**
```js
{
  id: Date.now() (+ Math.random() 兼容),
  name: '不许抽烟',
  condition: '画面中我正在抽烟或手里有点燃的香烟',
  type: 'instant' | 'window',
  time_scope: 'always' | 'hours:HH:MM-HH:MM' | 'weekdays:HH:MM-HH:MM' | 'weekends:HH:MM-HH:MM' | 'daily_before_HH:MM' | 'daily_after_HH:MM',
  time_desc: '全天任何时候',  // 中文描述，给用户看
  punishments: ['vibrate', 'bark', ...],  // PUNISHMENT id 数组
  enabled: true,
  locked_until?: timestamp,  // ruleset 采纳时会加，锁定到期前不可删
}
```

**Game 结构**
```js
{
  id: 'G' + 7位大写随机字符,
  type: 'pool'|'checkin'|'contract'|'duel'|'ruleset',
  name: '...',
  config: { stake?, days, text?, penalty?, rule? },
  createdAt: ts,
  createdBy: state.myId,
  createdByName: state.myName || '我',
  endTs: ts + days*86400000,
  members: [{ id, name, joinedAt, stake, violations, lastDay }],
  chain: 0,              // checkin 接力天数
  accepted: bool|undef,  // ruleset 是否已采纳
  handedOver: bool,      // contract 是否已移交控制权
  handedAt: ts,
}
```

**localStorage keys（全部必须保留）**
`apiKey`, `boardUrl`, `chatHistory`, `planHistory`, `rules`, `events`, `games`, `feed`, `mercyCards`, `myId`, `myName`

---

## 5. 关键交互流程

### 5.1 规则创建与编辑
1. 用户点 `+ 新建` → `newRule()` 清空 `editingRule`，把表单置空态，`showRuleModal()`
2. 或点某规则卡的"编辑" → `editRule(i)` 从 `state.rules[i]` 填回表单，调 `loadTimeScopeToForm(scope)` 解析 `time_scope` 字符串回 select + 时间输入框
3. `onTimePresetChange()` 控制 `#time-range-box`（hours/weekdays/weekends）和 `#time-single-box`（daily_before/after）的显示
4. `renderPunishOptions(selected)` 渲染 12 张惩罚卡片，选中态同步
5. 点"保存" → `saveRule()` 校验 → `buildTimeScopeFromForm()` → push/replace `state.rules` → `saveRules()` → 关弹窗 → `renderRules()`

### 5.2 监控：开始监控 → 每 5 秒 `/scene` 轮询 → Claude 规则匹配 → 违规弹窗
1. 进入 monitor tab → `refreshBoardStatus()` 判断有无 `boardUrl`，有则 `startFrameStream()` 每 1 秒刷 `<img src="${boardUrl}/frame?t=${Date.now()}">`
2. 用户点"▶️ 开始监控" → `toggleMonitor()` 校验 `boardUrl` 和 `apiKey`，按钮切"⏸ 停止监控"，立即 `pollSceneOnce()`，然后 `setInterval(pollSceneOnce, 5000)` 赋给 `sceneIntervalId` / `monitorTimer`，同时开 `sceneTimeTicker = setInterval(updateSceneTimeLabel, 1000)` 刷新"X秒前"标签
3. `pollSceneOnce()`：`fetch(boardUrl + '/scene', {cache: 'no-store'})` → 返回 `{text, image, scene?, error?}` → 把 image（base64 JPEG）塞进 `#board-frame`，把 text 塞进 `#current-scene`，`sceneLastUpdated = Date.now()` → 调 `runDetection({text, image})`
4. `runDetection(input)`：
   - 过滤 `state.rules.filter(r => r.enabled && isRuleActiveNow(r))`
   - 在 `#monitor-log` 顶部插入占位卡片（缩略图 + "🔍 匹配规则中..."）
   - 构造 system prompt：`你是行为审查助手。判断输入场景描述是否触发以下任一规则。返回严格 JSON: {"matched":["规则ID"...],"reason":"..."}`
   - `callClaude([{role:'user', content:'场景描述：' + text}], sys)` → `JSON.parse(reply.match(/\{[\s\S]*\}/)[0])`
   - 无匹配：绿色 ✅
   - 有匹配：红色 🚨，为每个 matched rule 渲染 name + 惩罚 chip，`navigator.vibrate(...)`，把 `{ts, rule_id, rule_name, reason, punishments, snapshot_text, snapshot_image}` push 进 `state.events`（上限 500），同时给所有 `state.games` 的 `me.violations++`，localStorage 三合一写入，调 `renderStats()`
5. 再次点按钮 → 清所有 interval，按钮切回"▶️ 开始监控"

### 5.3 游戏创建流程
1. 点"➕ 创建游戏" → `openCreateGame()` 渲染 `#game-picker` bottom sheet
2. 点某类型 → `closeGamePicker()` + `createGame(type)` → `openGameForm(type)` 渲染 `#game-form`
3. 用户填完必填 → `submitGameForm(type)`：遍历 `FORM_FIELDS[type]`，校验 required，number 转整数，提取 name 和 cfg
4. `finalizeGame(type, name, cfg)`：生成 game 对象（含 id、endTs、初始 members 只包含自己），push 到 `state.games`，`saveGames()`，`feedAdd()`，`renderFriends()`，延迟 200ms 调 `shareGame(game.id)` 弹出原生 share
5. 好友收到后点"🔗 加入邀请" → `openJoinGame()` prompt 粘贴 → 正则提取 base64 → 解码 → 如果已存在则合并 members，否则把自己加进 members 后 push → 刷新

### 5.4 自律契约的"掌控权转交"模型
契约是 5 种游戏里最特殊的一种——它有一个"违约后控制权转移"的状态机：

**状态图**
```
[进行中 handedOver=false]
 ├── creator 点"达成" → completeGame() → 游戏删除，feed 写入"✅ 完成承诺"
 ├── creator 点"承认违约" → breakGame() → 找出 witness（第一个非 createdBy 的 member）→ 确认弹窗 → handedOver=true → 控制权移交
 └── witness 点"举报 TA 违约了" → reportBreak() → handedOver=true

[已移交 handedOver=true]
 ├── witness 点"⚡ 执行惩罚" → executeContract() → alert 通知执行 penalty → 游戏删除
 └── witness 点"😇 饶 TA" → forgiveContract() → mercyCards++ → 游戏删除

 creator 在 handedOver 状态下只能看到"等待 XX 裁决…"，无操作权
```

核心设计：**立约人承认违约的那一刻就失去控制权**，见证人才有决定权（执行或饶恕）。这是模拟"把自己的命交给朋友"的真实社交压力。

### 5.5 `isRuleActiveNow(rule)` 时间作用域判断
解析 `rule.time_scope` 字符串，返回 bool：
- `always` → true
- `hours:HH:MM-HH:MM` → 当前时间是否在区间（支持跨天，如 `22:00-06:00`）
- `weekdays:...` / `weekends:...` → 先判断周几再判区间
- `daily_before_HH:MM` → 当前时间 ≤ 阈值
- `daily_after_HH:MM` → 当前时间 ≥ 阈值

---

## 6. 技术约束（Variant 必须遵守）

- **单文件 HTML**：所有 HTML、CSS、JS 都在 `demo/index.html` 一个文件里，没有构建步骤，没有 npm
- **Tailwind CDN**：`<script src="https://cdn.tailwindcss.com"></script>`，不要换成其他 CSS 框架
- **原生 JS**：不要引入 React/Vue/Alpine/jQuery 等任何框架
- **localStorage 持久化**：所有状态写 localStorage，刷新页面必须恢复
- **PWA**：
  - `<link rel="manifest" href="manifest.json">`
  - `<meta name="apple-mobile-web-app-capable" content="yes">`
  - service worker 注册：`navigator.serviceWorker.register('service-worker.js').catch(()=>{});`
- **移动端优先**：`max-w-md mx-auto`，底部 tab bar `fixed bottom-0`，`textarea/input` 字体至少 16px 防 iOS 缩放
- **Claude API 直连浏览器**：`fetch('https://api.anthropic.com/v1/messages')` 带 `anthropic-dangerous-direct-browser-access: true` header，model `claude-opus-4-5`
- **板子 HTTP 接口**：`GET ${boardUrl}/frame?t=${ts}` 返回 JPEG 图片；`GET ${boardUrl}/scene` 返回 `{text, image(base64), scene?, error?}` JSON
- **`font-size: 16px` 在 textarea/input 上**，避免 iOS Safari 自动缩放

---

## 7. 视觉方向建议（这部分是 Variant 的创作自由度）

**当前问题**：页面是朴素 Tailwind utility 堆砌，灰白底 + 橙色主色 + emoji，功能全但看起来像 2018 年的 todo app demo。功能越硬核视觉越需要配得上。

**方向关键词**
- **Modern & energetic**：深色模式优先 / 半深色混合；高对比度；几何感强
- **略带 edgy**：匹配"自律、社死惩罚、把自己管死"的产品气质。不要糖水色、不要柔和圆角 app 味。可以考虑：亮橙/亮红的主色 + 深墨/炭黑底 + 荧光强调色；大号 display font（如 Space Grotesk / JetBrains Mono 用于数据数字）；噪点/扫描线纹理
- **Data-forward**：战绩区、身份卡的数字要像仪表盘一样大而硬，连续自律天数要有存在感
- **Clear visual hierarchy**：tab bar 要重新设计得有分量（可以考虑高亮胶囊、活动 tab 浮起等）
- **Micro-interactions**：
  - 规则开关 toggle 动画
  - 惩罚卡片 checked 态有一个小震动/发光
  - 监控状态"开始监控"按钮有脉冲/扫描动画
  - 违规触发时顶部横幅红色震动
  - 连续自律天数 badge 随天数升级（🔥 → ⭐ → 🏆 已有，可增强）
- **Empty states**：每个空态都值得一张插画式的小场景（当前只有灰色 emoji，太敷衍）
- **惩罚等级色编码**：12 个 PUNISHMENTS 有 `level: 🟢🟡🟠🔴🟣`，视觉上应该沿用这个危险度递增体系
- **Monitor 页的"凝视感"**：这是产品核心页面。画面预览区 + 场景描述 + 匹配日志应该让人有"AI 正在盯着我"的临场感，可以加扫描线、模拟 HUD 边框、时间戳跳动等
- **契约卡片的"重量感"**：目前是黑底白字，应该做得像一份"真的契约书"——有边饰、印章、破损/警告条纹

**但**：无论视觉如何变，所有交互的可用性不能降低。按钮要够大（≥ 44px touch target），文字不能因为风格化变得难读。

---

## 8. 保留不变的事（Variant 绝对不可以删的东西）

以下是**业务骨架**，Variant 只能重新装饰它们，不得删除或重命名：

### 8.1 `state` 字段和 localStorage key
所有字段名一个都不能改：
`apiKey / boardUrl / chatHistory / planHistory / rules / events / games / feed / mercyCards / myId / myName / editingRule`

localStorage key 与字段名一一对应，**不要加前缀、不要改驼峰**。

### 8.2 所有函数名（全局可被 `onclick` 调用）
```
switchTab / openSettings / closeSettings / saveSettings
renderStats / clearEvents
renderFriends / renderGameCard
openCreateGame / closeGamePicker / createGame
openGameForm / closeGameForm / submitGameForm / finalizeGame
saveGames / feedAdd
shareGame / openJoinGame
deleteGame / settleGame / checkinGame
breakGame / reportBreak / executeContract / forgiveContract / completeGame / acceptGame
editMyName / shareMyStats
callClaude
renderChat / sendChat
renderPlanChat / sendPlan / renderPlanResult / adoptAllDonts / resetPlan
isRuleActiveNow
renderRules / toggleRule / deleteRule / saveRules / newRule / editRule
onTimePresetChange / loadTimeScopeToForm / buildTimeScopeFromForm
renderPunishOptions / saveRule / showRuleModal / closeRuleModal
refreshBoardStatus / startFrameStream / stopFrameStream
toggleMonitor / pollSceneOnce / runDetection
formatSceneAgo / updateSceneTimeLabel
escapeHtml
myStreak
```

这些函数的**签名和行为不可修改**。Variant 可以重写它们的内部实现来适配新 DOM，但参数、返回值、副作用必须一致。

### 8.3 网络请求
**`/frame` 流**（每 1 秒刷新板子画面）
```js
img.src = state.boardUrl + '/frame?t=' + Date.now();
```

**`/scene` 轮询**（每 5 秒）
```js
const r = await fetch(state.boardUrl + '/scene', { cache: 'no-store' });
const data = await r.json();
// data: { text, image (base64), scene?, error? }
```

**Claude API**（`callClaude`）
```js
fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'content-type': 'application/json',
    'x-api-key': state.apiKey,
    'anthropic-version': '2023-06-01',
    'anthropic-dangerous-direct-browser-access': 'true',
  },
  body: JSON.stringify({ model: 'claude-opus-4-5', max_tokens: 1024, messages, system }),
});
```
Model 名、header、endpoint 都不可改。

### 8.4 Service Worker 注册
```js
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('service-worker.js').catch(()=>{});
  });
}
```

### 8.5 五种游戏类型的业务逻辑
`GAME_TYPES` 和 `FORM_FIELDS` 这两个常量的结构和字段不得删减。特别是：
- `pool` 的押注/结算逻辑（`settleGame` 找 winner，`total` 计算，所有 member 平分/通吃）
- `checkin` 的接力天数计算（`breakGame` 链断清零 / 昨天打了今天打则 chain++）
- `contract` 的 `handedOver` 状态机（creator 承认违约 → handedOver → witness 决定）
- `duel` 的违规计数排名
- `ruleset` 的"被别人的规则锁定 N 天不可删"（`locked_until` 字段和 `accepted` 标志）

### 8.6 `PUNISHMENTS` 数组
12 项 id 顺序和内容不动：
`vibrate, buzzer, led, bark, email, wecom, sms, social, deduct, donate, lock, release`

### 8.7 `PLAN_SYSTEM` 字符串
规划教练的 system prompt 是产品核心资产之一（反向提问、3 阶段流程、JSON schema 约束），不可修改。

### 8.8 违规事件写入管线
`runDetection` 里触发违规后这套副作用必须保留：
1. push `state.events`（带 `snapshot_image` base64）
2. unshift `state.feed`
3. 遍历 `state.games` 所有 `me.violations++`
4. `navigator.vibrate([300, 100, 300, 100, 600])`
5. 三合一 `localStorage.setItem`
6. `renderStats()`

---

## 9. 交付要求

Variant 输出一个完整的 `demo/index.html` 文件：
- 单文件、可直接在浏览器打开、功能与现版等价
- 现代视觉（见第 7 节）
- 所有 `onclick` handler 和 `id` 引用都保留
- 不要省略任何功能、不要"下个版本再做"、不要用占位符
- 保留 `<meta>` PWA 相关标签、manifest link、theme-color、service worker 注册脚本
- 顶部引用 Tailwind CDN；可以在 `<style>` 里加自定义 CSS（custom properties、动画、字体）
- 可以引入 Google Fonts（比如 `Space Grotesk`、`Inter`、`JetBrains Mono`）

交付后我会直接替换 `demo/index.html`，然后在手机上 PWA 测试规则创建、监控轮询、游戏流程三条主链路，任何一条跑不通都视为重做。

加油，把这个产品做得配得上它的野心。
