# 项目架构：给非技术读者的说明

> 你不需要看懂代码才能理解这个项目是怎么组织的。
> 把它想象成一栋四层建筑——每层有明确分工，上层调用下层，互不越级。

---

## 整体比喻：四层建筑

```
┌────────────────────────────────────────────┐
│  大门（CLI 入口）   deploy.py              │
│  "按哪个按钮做什么"                         │
├────────────────────────────────────────────┤
│  3楼（glue/ 编排层）                        │
│  "把各部门的工作按顺序串起来"               │
├────────────────────────────────────────────┤
│  2楼（services/ 业务层）                    │
│  "各部门各干各的活"                          │
├────────────────────────────────────────────┤
│  1楼（libs/ 适配层）                         │
│  "跟飞书、AI 外部系统说话的翻译官"           │
├────────────────────────────────────────────┤
│  地基（config/ + 第三方 pip 包）             │
│  "数据定义和外部依赖"                        │
└────────────────────────────────────────────┘
```

---

## 大门：deploy.py

**是什么：** 你每次运行的命令入口。

**文件：** `deploy.py`（根目录）

**你什么时候动它：** 想新增一种运行模式时（比如 `python deploy.py cleanup`）。平时不需要碰。

**常用命令：**
```bash
python deploy.py wiki          # 在飞书新建知识库节点
python deploy.py tables        # 在飞书新建多维表格
python deploy.py docs --limit 1  # 用 AI 生成一份学习指南
python deploy.py sync          # 增量同步课程记录（只添加新的，不覆盖旧的）
```

---

## 3楼：glue/ 编排层

**是什么：** 把各个功能模块（2楼）的调用顺序写下来，形成"部署流程"。

**文件：**
- `glue/deploy.py` — 决定每种部署模式（wiki/tables/docs/...）的具体步骤
- `glue/pipeline.py` — 可复用的子流程（wiki流程、表格流程、文档流程）
- `glue/rollback.py` — 出错时撤销已经创建的飞书资源（知识库节点、表格等）

**你什么时候关注它：** 部署流程出了问题、需要调整步骤顺序、或出错后想了解回滚逻辑时。

**关键原则：** 这一层**不含业务判断**，只负责"先做 A，再做 B，出错就回滚"。

---

## 2楼：services/ 业务层

**是什么：** 各部门各干各的活——知识库部门、表格部门、文档部门、资料部门、权限部门。

**文件：**
| 文件 | 负责什么 |
|------|---------|
| `services/wiki_service.py` | 创建/查找飞书知识空间和节点 |
| `services/table_service.py` | 创建多维表格、填写课程记录（含增量更新逻辑）|
| `services/doc_service.py` | 用 AI 生成学习指南文档 |
| `services/material_service.py` | 上传课程资料文件到飞书云盘 |
| `services/perm_service.py` | 配置知识空间访问权限 |

**你什么时候关注它：** 想修改业务逻辑（比如怎么判断增量更新、课程记录字段是什么）时。

**关键原则：** 这一层调用 1楼（libs/feishu）发出真实 API 请求；它自己**不直接写 HTTP**。

---

## 1楼：libs/ 适配层

**是什么：** 跟飞书、AI 外部系统交流的"翻译官"——把 Python 函数调用翻译成飞书 API 请求，把返回结果翻译成 Python 字典。

**文件：**
| 文件 | 负责什么 |
|------|---------|
| `libs/feishu/__init__.py` | 飞书 SDK 主入口，组合 5 个 Mixin |
| `libs/feishu/wiki.py` | 知识库 API（创建节点、列出空间等）|
| `libs/feishu/bitable.py` | 多维表格 API（创建表格、写记录等）|
| `libs/feishu/docx.py` | 飞书文档 API（创建文档、写内容）|
| `libs/feishu/drive.py` | 飞书云盘 API（上传文件）|
| `libs/feishu/perm.py` | 知识空间成员/权限 API |
| `libs/llm_adapter.py` | 智谱 AI（GLM-4）接口 |

**你什么时候关注它：** 飞书 API 调用报错、想了解某个 API 是怎么调的、或者需要新增 API 操作时。

**关键技术细节（只需知道结论）：** 基于 `lark-oapi` 官方 SDK，不需要手动管理 Token——SDK 自动刷新。唯一例外：删除知识库节点用 `httpx` 直接调，因为 SDK 暂不支持此操作。

---

## 地基：config/ + 外部依赖

**config/ 目录：**
| 文件 | 负责什么 |
|------|---------|
| `config/course_schema.py` | 所有课程数据（课程名、老师、学期、考试形式）+字段定义 |
| `config/settings.py` | 从 `.env` 文件读取环境变量（飞书 App ID、密钥、路径等）|

**你什么时候关注它：** 需要修改课程列表、添加新字段、或更换飞书应用时。

**外部依赖：** 在 `requirements.txt` 中列出，用 `pip install -r requirements.txt` 安装。核心依赖：
- `lark-oapi` — 飞书官方 SDK
- `structlog` — 结构化日志
- `pydantic-settings` — 环境变量配置
- `typer` — CLI 命令行工具

---

## 完整代码调用链示例

以 `python deploy.py wiki` 为例，程序经过这些层：

```
deploy.py (大门)
  ↓ call
glue/deploy.py → _deploy_wiki()  (3楼：决定先查空间、再创节点)
  ↓ call
glue/pipeline.py → wiki_pipeline()  (3楼：按顺序执行)
  ↓ call
services/wiki_service.py → get_space_by_name(), create_year_nodes(), create_course_nodes()  (2楼：业务决策)
  ↓ call
libs/feishu/wiki.py → list_wiki_spaces(), create_wiki_node()  (1楼：翻译成 API 请求)
  ↓ HTTP
飞书服务器  (外部)
```

---

## 测试文件在哪里

```
tests/
├── conftest.py              ← MockFeishuAdapter（假飞书，不发真实请求，用于单元测试）
├── test_services/
│   ├── test_wiki_service.py ← WikiService 的单元测试（9个测试）
│   └── test_table_service.py
└── report/
    └── 2026-05-29-test-report.md  ← 测试结果报告
```

**运行所有单元测试：**
```bash
python -m pytest tests/test_services/ -v
```
