# PPE-CloudSmart-GiftBox · 项目规范

> 本文件是 Claude Code 在本项目中的最高优先级参考。所有决策以本文为准。
> 合并自：GLUE_CODING_GUIDE.md、整改方案-20260525.md

---

## 一、会话规范（每次 Session 必须执行）

**每次 Session 开始时，第一步：** 在 `log/` 目录创建本次会话日志。

```
文件名：log/YYYY-MM-DD-HH.md（HH = 当前小时，24h制）
格式：# Session YYYY-MM-DD-HH

## 关键决策
（本次 Session 的主要决策）

## 执行进程
- [ ] 任务1
- [ ] 任务2
...

## 备注
（遇到的障碍、关键发现、需要用户协助的事项）
```

**每完成一个主要阶段，更新日志进度。**

---

## 二、业务背景

PPE云端智能大礼包是为**南开大学PPE专业**设计的课程资料平台，部署在飞书云上。

**五项核心功能：**
1. **知识库构建**：按年级→课程层级创建飞书知识库，每课程节点含课程信息和学习指南
2. **多维表格**：自动创建课程信息表格，填充课程元数据（教师、学期、类型等）
3. **文档生成**：用 LLM（智谱 GLM）基于课程资料生成"学长学姐视角"学习指南，写入飞书文档
4. **资料上传**：将本地课程资料（PDF、DOCX 等）上传到飞书云盘并关联知识库节点
5. **权限配置**：配置知识库和表格的访问权限

飞书凭据通过 `.env` 文件配置（参考 `.env.example`）。

---

## 三、核心理念：胶水编程

**连接而非创造。** 最大化复用成熟开源组件，只编写必要的胶水代码来连接它们。

- 评价标准不是"写了多少代码"，而是"是否正确地站在成熟系统之上构建新系统"
- 自定义代码只负责：**组合、调用、封装、适配**
- 所有底层能力优先使用经过社区验证的库，**禁止重复造轮子**
- 实现任何新功能前，先调查 GitHub 是否有成熟且活跃维护的库，调查报告写入 `research/`

---

## 四、四层架构

```
deploy.py (CLI入口)
    ↓
glue/          ← 编排层：串联services，零业务逻辑
    ↓
services/      ← 业务层：功能单元，调用libs
    ↓
libs/          ← 适配层：统一接口，封装第三方库差异
    ↓
third_party/   ← 黑盒：成熟开源库，禁止修改
```

### 依赖方向（单向向下，严格遵守）

1. 依赖方向：`glue → services → libs → third_party`
2. **禁止反向**：service 不能调另一个 service，lib 不能调 service
3. **禁止跨层**：service 不能直接 import third_party，必须走 libs
4. **同级不互通**：两个 service 通信时，通过 glue 层中转传参

---

## 五、各层职责与规范

### libs/ — 适配层

- 每个文件一个关注点，**代码量控制在 50-100 行以内**
- 对外暴露干净的接口，隐藏第三方库实现细节
- 统一错误类型：将 SDK 异常转换为项目自定义异常（见 `libs/exceptions.py`）
- **当前飞书适配器**：`libs/feishu/`（基于 `lark-oapi` 官方 SDK）

### services/ — 业务层

- 每个 service 解决一个明确的业务问题
- **只调用 libs/ 层接口**，不直接依赖任何第三方 SDK
- 包含业务校验逻辑，不包含基础设施逻辑（如 HTTP 重试）

### glue/ — 编排层

- 代码风格：像写配置一样写——全是调用，没有条件分支和业务逻辑
- 唯一知道"先做什么、后做什么"的地方
- **代码量不超过 200 行**

---

## 六、代码质量红线

1. **third_party/ 代码零修改** — 如需定制，在 libs/ 层封装
2. **libs/ 每文件不超过 100 行** — 超过说明封装粒度太粗
3. **services/ 不直接 import 任何第三方 SDK** — 必须走 libs/
4. **无硬编码路径** — 所有路径通过配置传入
5. **无硬编码 API Key** — 全部通过 .env 管理
6. **每个 service 可独立测试** — 不依赖其他 service
7. **glue/ 零业务逻辑** — 只有调用和流程控制
8. **错误类型统一** — libs/ 将 SDK 异常转换为自定义异常

---

## 七、当前整改优先级

> 来源：整改方案-20260525.md

### 第一阶段：SDK 迁移 🔴（最高优先）

- 将 `libs/feishu/` 从手写 httpx 迁移到 `lark-oapi` 官方 SDK
- SDK 自动处理 Token 刷新（解决 2 小时过期问题）、请求格式、错误重试
- 迁移过程保持四层架构不变，保持 FeishuAdapter 对外接口不变

### 第二阶段：修复已知 Bug 🔴（高）

- **Bug 2**：多维表格数据写入位置不对（从第一行开始填，不是末尾追加）
- **Bug 3**：`glue/rollback.py` 中 `_delete_wiki_space`、`_delete_document` 为空实现

### 第三阶段：端到端测试 🟡（中）

- 用真实数据跑 `python deploy.py --mode full`
- 验证知识库结构、表格数据、文档生成、资料上传
- 测试增量更新和回滚

### 第四阶段：工程优化 🟢（低）

- 补充单元测试和集成测试（pytest + Mock）
- 清理旧代码，更新 README

---

## 八、项目目录说明

```
PPE-CloudSmart-GiftBox/
├── CLAUDE.md              ← 本文件，项目规范
├── pyproject.toml         ← pytest 配置 + 项目元信息
├── requirements.txt       ← 依赖清单（锁定版本）
├── deploy.py              ← CLI 入口（typer，调用 glue/deploy.py）
├── .env / .env.example    ← 环境变量（API Key等，.env不入库）
│
├── config/                ← 配置管理
│   ├── settings.py        # pydantic-settings 配置定义
│   ├── course_schema.py   # 课程数据结构
│   └── prompts/           # LLM 提示词模板（Jinja2 .j2 文件）
│
├── libs/                  ← 适配层（薄封装）
│   ├── feishu/            # 飞书 SDK 适配器（6 个模块）
│   ├── llm_adapter.py     # LLM 调用统一接口
│   ├── data_adapter.py    # 数据文件适配器（Excel/CSV）
│   └── exceptions.py      # 自定义异常
│
├── services/              ← 业务层
│   ├── wiki_service.py    # 知识库节点创建
│   ├── table_service.py   # 多维表格操作
│   ├── doc_service.py     # 文档生成（LLM → 飞书文档）
│   ├── material_service.py # 资料上传
│   ├── import_service.py  # Excel/CSV 数据导入
│   └── perm_service.py    # 权限配置
│
├── glue/                  ← 编排层
│   ├── deploy.py          # 主部署流程
│   ├── pipeline.py        # 子流程定义
│   └── rollback.py        # 回滚逻辑
│
├── data/                  ← 业务数据（课程资料、元数据）
├── docs/                  ← 技术文档
├── log/                   ← Session 日志（YYYY-MM-DD-HH.md）
├── research/              ← 调研报告
│   └── introduction/      # CLI/SDK 规范文档
├── tests/                 ← 测试套件
│   ├── conftest.py        # MockFeishuAdapter fixture
│   ├── test_services/     # services 层单元测试
│   └── report/            # 测试报告
└── third_party/           ← 第三方源码（当前为空，优先 pip）
```

---

## 九、研究报告规范

实现任何新功能前，先在 `research/` 中写调查报告：

- 功能调研（GitHub 库评估）→ `research/<功能名>.md`
- CLI/SDK 技术规范 → `research/introduction/<名称>.md`

可使用 `/research-pkg <包名>` SKILL 触发标准化调查流程。

---

## 十、README 维护规则

> 产品理解在 plan mode 中不断演进。README 必须与当前理解同步。

1. **每当 plan mode 中产生较大的产品/架构认知变化，即刻重写 README.md**（不等整个 plan 做完）。
2. **旧版 README 编号后移入 `docs/README_history/`**：
   - 命名规则：`README_v{N}.md`，N 从当前 README 里的版本号递推。
   - 移入前先检查 `docs/README_history/` 有无同名文件，有则跳过（防止重复备份）。
3. **README 内容要求**：
   - 反映当前产品定位（搜集→整合→分发）、知识库结构、数据流、部署模式。
   - 技术细节（字段列表、依赖声明等）随代码变更同步更新。
   - 不使用表情符号（emoji）。
