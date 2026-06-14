# 操作说明：初始化管理 bitable（demo 准备第 1 步）

> 目标：用代码自动创建飞书管理 bitable（资料管理表 + 心得管理表），然后在 UI 上创建表单、填一条测试记录。
>
> 完成后告诉 Claude，由 Claude 从代码层读取真实字段结构，作为仿真数据模板。

---

## 前置确认（首次约 5 分钟）

### 1. 新开 PowerShell 窗口

开始菜单 → 搜索 "PowerShell" → 打开。

### 2. 切到项目目录

```powershell
cd "D:\c盘转移\Desktop\Code工作文件夹\PPE-CloudSmart-GiftBox"
```

### 3. 检查 Python 版本

```powershell
python --version
```

应该是 3.11 或更高（项目用 3.14 开发）。版本太低先升级。

### 4. 创建虚拟环境（首次必做，避免污染全局包）

在项目目录下创建独立 Python 环境：

```powershell
python -m venv .venv
```

执行后会生成 `.venv\` 文件夹。已被 `.gitignore` 排除，不会入库。

### 5. 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

**如果报错** `无法加载文件 ... 因为在此系统上禁止运行脚本`，是 PowerShell 默认执行策略限制。两种解决方式任选：

- **方式 A（推荐，只对当前窗口生效）**：
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\.venv\Scripts\Activate.ps1
  ```
- **方式 B（用 .bat 绕过）**：
  ```powershell
  cmd /c .venv\Scripts\activate.bat
  ```

激活成功后，命令提示符前面会出现 `(.venv)` 标记。

### 6. 升级 pip 并安装依赖

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

依赖约 50 个包，第一次安装 1-3 分钟。

### 7. 验证关键依赖

```powershell
python -c "import lark_oapi, oss2, openai, pypdf; print('依赖 OK')"
```

应该输出 `依赖 OK`。报 `ModuleNotFoundError` 说明没装全，重跑 `pip install -r requirements.txt`。

---

> **以后每次新开 PowerShell 跑项目命令前**，只需：
> ```powershell
> cd "D:\c盘转移\Desktop\Code工作文件夹\PPE-CloudSmart-GiftBox"
> .\.venv\Scripts\Activate.ps1
> ```
> 步骤 3-7 是一次性工作，不用重复。

> 提示：Windows 中文路径在 PowerShell 输出里可能显示成 `?` 或乱码，**不影响命令执行**，是控制台编码问题。想看清楚中文先跑 `chcp 65001`。

---

## 第 1 步：跑 `init-bitable` 创建 bitable

```powershell
python deploy.py init-bitable
```

### 预期输出（成功）

```
开始创建管理 bitable
多维表格应用创建成功  name=PPE大礼包管理表  app_token=xxxxxxxxxxxxxx
管理 bitable 创建完成  app_token=xxxxxxxxxxxxxx  url=https://xxx.feishu.cn/base/xxxxxxxxxxxxxx
app_token 已持久化，请填到 .env 的 BITABLE_APP_TOKEN
```

记下两样东西：
- **`app_token`**（一长串字符，类似 `bascnxxxxxxxxxxxxxxxxxx`）
- **`url`**（飞书 bitable 的访问链接）

### 可能的错误

| 报错 | 原因 | 处理 |
|---|---|---|
| `FeishuAPIException: 权限不足` / code 99991663 | 飞书应用没开通 `bitable:app` 权限 | 飞书开放平台 → 你的应用 → 权限管理 → 开通 `bitable:app`（读写多维表格） |
| `FeishuAPIException: invalid app_id` | `.env` 里 `FEISHU_APP_ID` 错 | 重新到飞书开放平台复制 |
| 网络超时 | 网络抖动 | 重试一次 |
| `ModuleNotFoundError` | 依赖没装 | `pip install -r requirements.txt` |

> 如果遇到表里没有的错误，把完整报错贴给 Claude。

---

## 第 2 步：把 app_token 填到 .env

用编辑器（VS Code / Sublime / Notepad）打开项目根目录的 `.env` 文件，找到这一行：

```
BITABLE_APP_TOKEN=
```

改成（**等号两边不要加空格，token 后不要加引号**）：

```
BITABLE_APP_TOKEN=你刚才记下的 app_token
```

保存。

---

## 第 3 步：获得 bitable 的 UI 操作权限（关键，必须做）

**为什么需要这步**：应用（飞书机器人）是 bitable 的 owner，自动有权限；但你作为人在 UI 上操作时**没有自动权限**。直接在浏览器打开 url 会看到「申请权限」按钮——这个申请是发给 owner（机器人）的，机器人收不到通知，所以你也找不到地方批准。

**两种解决方案任选其一**：

### 方案 A（推荐）：用 `open-bitable` 设置链接分享

**适合手机号登录、不想查 ID 的场景**。一行命令，**不需要任何 ID**：

```powershell
python deploy.py open-bitable
```

默认设置成 `anyone_editable`（任何人凭链接可编辑）。

预期输出：
```
开始设置 bitable 链接分享  app_token=xxxxxxxx  link_share_entity=anyone_editable
链接分享设置完成  token=xxxxxxxx  link_share_entity=anyone_editable
```

跑完后刷新浏览器，bitable 应该能直接编辑。

如果 `anyone_editable` 报错（飞书禁止外部访问），改用：
```powershell
python deploy.py open-bitable -e tenant_editable
```

### 方案 B：用 `grant-bitable` 加为协作者

**适合有 email 的人**，权限更精准：

```powershell
python deploy.py grant-bitable 你的飞书登录邮箱
```

例如：
```powershell
python deploy.py grant-bitable peber@example.com
```

飞书会给你发「文档已共享给你」的消息，1-2 秒后刷新浏览器即可。

如果用手机号登录、没 email：跳过方案 B，用方案 A。

### 命令完整参数

```
# 方案 A：链接分享（不需要 ID）
python deploy.py open-bitable [--entity anyone_editable]
  --entity / -e: closed / tenant_readable / tenant_editable / anyone_readable / anyone_editable

# 方案 B：加协作者（需要 ID）
python deploy.py grant-bitable <member> [--type email] [--perm full_access]
  --type / -t: email / openid / userid / departmentid（默认 email）
  --perm / -p: view / edit / full_access（默认 full_access）
```

### 常见报错

| 报错 | 原因 | 处理 |
|---|---|---|
| `member not found`（grant-bitable） | email/ID 不对 | 确认 ID 正确，或改用方案 A |
| `permission denied` / code 99991663 | 飞书应用缺权限 | 飞书开放平台 → 你的应用 → 权限管理 → 开通「云文档相关权限」（含 `drive:permission:member` 和 `drive:permission:public`），等几分钟生效后重试 |
| `external_access denied`（open-bitable） | 飞书禁止外部访问 | 改用 `-e tenant_editable` |

---

## 第 4 步：打开 bitable 验证

1. 浏览器打开第 1 步的 **url**
2. 应该看到 2 张表（不再有「申请权限」提示）：
   - **资料管理表**（11 字段：贡献者/年级/课程/资料类型/推荐理由/文件附件/资料名称/原始文件名/文件链接/上传时间/审核状态）
   - **心得管理表**（8 字段：作者/年级/课程/成绩/心得内容/提交时间/审核状态/审核人）
3. 你应该能直接编辑（不需要再加协作者，第 3 步已经做完了）

---

## 第 4 步：配置资料管理表的表单

这是 demo 真正要测的核心——学生填表的入口。

1. 进入「资料管理表」
2. 顶部菜单栏 → **「表单」按钮** → 创建表单
3. 在表单配置界面：
   - **字段显示设置**：只勾选前 6 个字段让学生看到
     - ✅ 贡献者
     - ✅ 年级
     - ✅ 课程
     - ✅ 资料类型
     - ✅ 推荐理由
     - ✅ 文件附件
     - ❌ 资料名称（隐藏，代码归档时自动填）
     - ❌ 原始文件名（隐藏，代码归档时自动填）
     - ❌ 文件链接（隐藏，代码归档后回填 OSS URL）
     - ❌ 上传时间（隐藏，系统时间戳）
     - ❌ 审核状态（隐藏，管理员审核时填）
   - **单选字段配置选项**（飞书会自动从已有选项读取，确认一下）：
     - 年级：22级 / 23级 / 24级
     - 课程：世界经济概论 / 中国经济概论 / 伦理学导论 / 宪法学 / 西方政治思想史 / 中国政治思想史 / 比较政治制度 / 外国经济学说史 / 概率论与数理统计
     - 资料类型：PPT / 笔记 / 真题 / 阅读材料 / 教材 / 复习大纲 / 练习题 / 其他
4. **表单顶部说明**（重要，告诉学生一次可传多份）：
   > 可以一次上传多份资料，多份资料共用一段推荐理由完全没问题——理由混在一起写就行，不影响后续整理。

5. **保存表单** → 复制填表链接（类似 `https://xxx.feishu.cn/share/base/form/xxxxx`）

---

## 第 5 步：填一条测试记录

打开填表链接（可以用浏览器无痕模式模拟学生视角），填一份完整记录：

| 字段 | 建议填的内容 |
|---|---|
| 贡献者 | `测试-小张`（随便一个化名） |
| 年级 | 22级 |
| 课程 | 世界经济概论 |
| 资料类型 | 复习大纲 |
| 推荐理由 | 随便写几句，3-5 行即可。例如："这份资料是雷鸣老师 2023 年期末划的重点，按贸易/金融/发展三条主线整理……" |
| 文件附件 | 上传一个小 PDF（< 1MB）。**推荐从 `data/courses/大二上/世界经济概论（雷鸣老师）开卷/` 选一个**，比如 `备考指南.txt`（不过它是 .txt 不是 PDF，得先转）或直接挑一个小的 PDF |

> 关键：附件字段是这次实测的核心——飞书在 bitable 记录里返回附件字段时，结构不是简单字符串，而是 `[{file_token, name, size, tmp_download_url, ...}]` 这样的列表。Claude 需要实测样本才能正确仿真。

提交后，回到 bitable，应该能在「资料管理表」看到这条新记录。

---

## 第 6 步：告诉 Claude 继续

回到 Claude Code 会话，说：

> "已填测试记录，app_token 是 xxx，记录 ID 是 xxx"

或者更简单：

> "init-bitable 跑完了，测试记录已填，你读一下"

Claude 会从代码层读取这条记录，分析附件字段、URL 字段、单选 value 的真实结构，然后基于这个真实模板生成仿真数据。

---

## 附：可选 — 同时配置心得管理表的表单

如果时间充裕，可以一并配置心得管理表的表单（同样流程，但学生填字段是：作者/年级/课程/成绩/心得内容）。

不配也行——这次 demo 测试重点在资料管理表（它是文件链接归档逻辑的源头）。心得管理表可以下次再测。

---

## 故障排查

### 跑 `init-bitable` 后没有看到 url

检查 PowerShell 输出。如果只有"开始创建"但没有"创建完成"，可能是网络或权限问题。把完整输出贴给 Claude。

### 浏览器打开 url 提示"无权限"

说明你不是协作者。回到第 3 步，确认把自己加为协作者。

### 表单配置时找不到「文件附件」字段

可能 `init-bitable` 跑的时候 schema 还是旧的（没有附件字段）。
检查方法：

```powershell
python -c "from config.course_schema import MATERIALS_TABLE_FIELDS; print([n for n,_ in MATERIALS_TABLE_FIELDS])"
```

应该看到 `'文件附件'`。如果没有，说明 course_schema.py 的修改没生效，告诉 Claude 重新检查。

### 飞书附件字段类型不是 17

飞书有时调整字段类型编号。如果 `init-bitable` 报"字段类型不支持"或类似错误，告诉 Claude，需要查飞书最新文档确认附件字段类型编号。
