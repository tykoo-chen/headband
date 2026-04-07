# 团队协作指南 🤝

> **总原则一句话：每人一个分支，不准直接推 main。不确定就在群里喊队长 A，不要瞎点。**

本文档写给 **完全零基础** 的队员。所有命令、所有按钮、所有步骤都写清楚了，照做就行。

---

## 🎯 总规矩（先记住这 5 条）

1. ✅ **每人一个分支**：`a/xxx`、`b/xxx`、`c/xxx`、`d/headband`、`e/server`
2. ✅ **只改自己目录下的文件**（见下表）
3. ✅ **想合并代码 → 开 PR（Pull Request）→ 队长 A 审核 → 队长合并**
4. ❌ **绝对不要直接 push 到 `main` 分支**
5. ❌ **遇到 `Merge Conflict` 红字 → 立刻群里喊队长，不要自己点**

---

## 📋 谁改哪个目录（背下来）

| 你是 | 你只能改 | 你绝对不许改 |
|---|---|---|
| **A 队长** | `产品原型文档.md`、`docs/`、`README.md` | `headband/`、`server/`、`demo/` 的代码 |
| **B 硬件** | `docs/images/`（上传组装照片） | 任何代码文件 |
| **C 结构** | `hardware/3d/`（自己建的目录）、`docs/images/` | 任何代码文件 |
| **D 发带端** | `headband/` 下所有文件 | `server/`、`demo/`、别人的文档 |
| **E 服务端** | `server/`、`demo/` | `headband/`、别人的文档 |

> 💡 想改不属于自己的目录？**先在群里说一声，让对方知道**，最好让对方自己改。

---

## 🛠 第一次设置（保姆级，10 分钟）

### Step 1：注册 GitHub 账号
1. 打开 <https://github.com/join>
2. 填邮箱、设密码、起个用户名（**用英文，不要中文**）
3. 验证邮箱
4. **把你的 GitHub 用户名发到群里 @队长 A**，让他把你加成 collaborator
5. 等队长把你加进去（你的邮箱会收到一封 invitation 邮件 → 点 Accept invitation）

### Step 2：装 GitHub Desktop（图形界面，不用命令行）
1. 打开 <https://desktop.github.com/>
2. 点中间大大的 **"Download for macOS / Windows"**
3. 下载完双击安装
4. 打开后用 GitHub 账号登录（**File → Options → Accounts → Sign in**）

### Step 3：把 repo 克隆到自己电脑
1. 在 GitHub Desktop 里点左上角 **File → Clone Repository...**
2. 在弹窗里选 **GitHub.com** 标签页
3. 列表里找到 `tykoo-chen/headband`，点它
4. **Local Path** 选一个你记得住的文件夹（比如桌面）
5. 点右下 **Clone** 按钮
6. 等几秒，下载完毕 ✅

### Step 4：创建你自己的分支
1. 在 GitHub Desktop 顶部，点 **Current Branch** 那个按钮（默认显示 `main`）
2. 点 **New Branch** 按钮
3. 在 **Name** 里输入你的分支名（**严格按照下表命名**）：

| 你是 | 分支名 |
|---|---|
| A | `a/docs` |
| B | `b/hardware-photos` |
| C | `c/3d-models` |
| D | `d/headband` |
| E | `e/server` |

4. **Based on** 选 `main`
5. 点 **Create Branch**
6. 弹窗问你要不要 publish → 点 **Publish Branch**（这一步把分支推到 GitHub 上）✅

🎉 第一次设置完成！

---

## 🔁 每天的工作流（雷打不动 6 步）

### 📥 Step 1：拉最新代码
1. 打开 GitHub Desktop
2. 顶部 **Current Branch** 切回 `main`
3. 点顶部 **Fetch origin** → 变成 **Pull origin** 后再点一下
4. 切回你自己的分支（比如 `d/headband`）
5. 点顶部 **Branch → Update from main**（让你的分支跟上最新的 main）

### ✂️ Step 2：切到自己的分支
（上一步已经切了，确认顶部 **Current Branch** 显示的是你自己的分支名，不是 `main`）

> ⚠️ 如果你看到 **Current Branch: main**，**立刻停下来**，先切到自己的分支再改东西！

### ✍️ Step 3：改文件
- 用你顺手的编辑器（VS Code 推荐）打开本地文件夹
- **只改自己目录下的文件**（看上面的表格）
- 改完保存

### 💬 Step 4：写 commit 说明
1. 切回 GitHub Desktop
2. 左侧 **Changes** 一栏会自动列出你改过的文件
3. 左下角 **Summary（必填）** 写一句话描述你干了啥，比如：
   - `D：补完摄像头采集 mock`
   - `E：加 /api/rules 的 GET 接口`
   - `A：更新硬件清单`
4. **Description（可选）** 可以不写
5. 点蓝色按钮 **Commit to <你的分支名>**

### ☁️ Step 5：Push 到 GitHub
1. 顶部出现 **Push origin** 按钮，点它
2. 等几秒，推送完成 ✅

### 🔀 Step 6：开 PR 让队长合并
1. 推送完成后，GitHub Desktop 会弹出 **Create Pull Request** 按钮 → 点它
2. 浏览器自动跳到 GitHub 网页
3. **base** 选 `main`，**compare** 是你自己的分支
4. **Title** 写清楚改了啥（和 commit 一样就行）
5. 点 **Create pull request**
6. **去群里 @队长 A**，说"PR 开好了，请合并"
7. 等队长合并完，你的工作就告一段落 ✅

---

## ⚠️ 冲突处理（Merge Conflict）

如果某天你 Push / Pull 时弹出红字 **"Merge Conflict"** 或 **"Conflicts"**：

🛑 **立刻停下，不要点任何按钮！**

1. 截图弹窗
2. 发到群里 + @队长 A
3. 写一句："我在做 XX，遇到冲突了，怎么办？"
4. 等队长来线下 / 远程帮你

> 💡 为什么不让你自己处理？因为冲突处理一旦点错，可能把别人的代码覆盖掉。10 秒钟问一下队长，比 1 小时排查损失划算。

---

## 🚫 禁忌清单（违反任何一条 = 全队加班）

| ❌ 禁忌 | 为啥不能干 |
|---|---|
| 直接改 `main` 分支 | 没人审核，错了直接炸线上 |
| 改别人目录下的文件 | 会和对方冲突，且对方不知情 |
| `force push`（强推） | 会把别人的提交直接抹掉 |
| commit API Key / 密码 / `.env` | 公开 repo，全世界都能看到 |
| commit 大于 10MB 的文件 | repo 会变得超慢，git 会卡 |
| 在群里不说话偷偷改 | 别人不知道你在干啥，重复劳动 |

> 💡 **API Key、密码、token** 一律放在本地的 `.env` 文件里（已被 `.gitignore` 忽略），永远不进 git。

---

## 🆘 紧急联系 / 应急备份

| 角色 | 主负责 | 应急备份 |
|---|---|---|
| 产品 / 队长 | A | E |
| 硬件焊接 | B | C |
| 3D 打印 | C | B |
| 发带端代码 | D | E |
| 服务端代码 | E | D |

> 💡 **A 不在场时，所有 PR 默认由 E 兜底审核合并**。

---

## 🤔 遇到问题怎么办（万能三步）

1. 📸 **截图**（整个屏幕，不要只截一小块）
2. 📝 **写一句话**：你在干啥 + 想做啥 + 出了啥错
3. 💬 **发群里 @队长 A**

**不要做的事**：
- ❌ 不要默默憋着试 1 小时
- ❌ 不要自己百度乱点
- ❌ 不要假装没看见报错继续干

> 🕐 黑客松只有 2 天，**5 分钟解决不了的问题立刻喊人**。

---

## 📚 延伸阅读

- 完全零基础 Git → [`docs/quickstart-for-beginners.md`](docs/quickstart-for-beginners.md)
- 你的角色具体干啥 → [`docs/role-playbook.md`](docs/role-playbook.md)
- 项目总览 → [`README.md`](README.md)
