# PPE-CloudSmart-GiftBox · 胶水编程重构指南

> 本文档是 Claude Code 的最高优先级参考。重构过程中一切决策以本文为准。

---

## 一、核心理念

**连接而非创造。** 最大化复用成熟开源组件，只编写必要的胶水代码来连接它们。

- 评价标准不是"写了多少代码"，而是"是否正确地站在成熟系统之上构建新系统"
- 自定义代码只负责：组合、调用、封装、适配
- 所有底层能力优先使用经过社区验证的库，禁止重复造轮子

---

## 二、目标项目结构

```
PPE-CloudSmart-GiftBox/
│
├── third_party/          ← 第三方库源码（如需本地引入）
│   └── (可选，优先用pip)
│
├── libs/                 ← 第三方库的适配层（薄封装）
│   ├── __init__.py
│   ├── feishu_adapter.py   # 飞书SDK统一接口封装
│   ├── llm_adapter.py      # LLM调用统一接口封装
│   └── storage_adapter.py  # 文件存储统一接口封装
│
├── services/             ← 业务逻辑层（功能单元）
│   ├── __init__.py
│   ├── wiki_service.py     # 知识库构建：节点创建、内容填充
│   ├── table_service.py    # 多维表格：创建、填充、增量更新
│   ├── doc_service.py      # 文档生成：LLM调用→飞书文档写入
│   ├── material_service.py # 资料上传：文件→飞书云盘
│   └── perm_service.py     # 权限管理：知识库/表格权限配置
│
├── glue/                 ← 编排层（唯一知道整体流程的地方）
│   ├── __init__.py
│   ├── deploy.py           # 主部署流程：串联所有service
│   ├── pipeline.py         # 子流程定义（wiki流程、table流程等）
│   └── rollback.py         # 回滚逻辑
│
├── config/               ← 配置管理
│   ├── __init__.py
│   ├── settings.py         # pydantic-settings 配置定义
│   ├── course_schema.py    # 课程数据结构定义
│   └── prompts/            # LLM提示词模板
│       └── guide_gen.txt
│
├── data/                 ← 业务数据
│   ├── courses/            # 课程资料目录
│   └── materials.json      # 资料元数据
│
├── tests/                ← 测试
│   ├── test_libs/
│   ├── test_services/
│   └── test_glue/
│
├── requirements.txt      ← 依赖清单（锁定版本）
├── pyproject.toml        ← 项目元信息 + 开发工具配置
├── .env                  ← 环境变量（API Key等，不入库）
├── .env.example          ← 环境变量模板（入库）
├── deploy.py             ← CLI入口（调用 glue/deploy.py）
└── README.md
```

---

## 三、四层架构详解

### 层级关系

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

### 依赖规则

1. **依赖方向单向向下**：glue → services → libs → third_party
2. **禁止反向依赖**：service不能调另一个service，lib不能调service
3. **同级不互通**：两个service需要通信时，通过glue层中转传参
4. **禁止跨层调用**：service不能直接import third_party，必须走libs

### 各层职责与代码规范

#### third_party/ — 黑盒层

- 如需本地引入第三方源码（某些无法pip安装的库），放在此目录
- **铁律：禁止修改其中任何一行代码**
- 优先使用 pip install 安装依赖，third_party 是兜底方案
- 替换第三方库时，只需修改 libs/ 的适配代码，上层零影响

#### libs/ — 适配层

- 每个文件一个关注点，代码量尽量控制在50-100行以内
- 对外暴露干净的接口，隐藏第三方库的实现细节
- 统一错误类型：将不同SDK的异常转换为项目自定义异常
- 统一重试策略：所有外部调用在此层配置重试参数

示例（feishu_adapter.py）：

```python
from lark_oapi import Client
from ..config.settings import Settings

class FeishuAdapter:
    def __init__(self, settings: Settings):
        self.client = Client.builder() \
            .app_id(settings.feishu_app_id) \
            .app_secret(settings.feishu_app_secret) \
            .build()

    def create_doc(self, space_token: str, title: str) -> dict:
        """创建知识库文档，返回 {token, url}"""
        # 调用SDK，处理错误，统一返回格式
        ...

    def upload_file(self, file_path: str) -> dict:
        """上传文件到云盘，返回 {token, url}"""
        ...

    def create_table(self, app_token: str, table_name: str) -> dict:
        """创建多维表格，返回 {table_id, url}"""
        ...
```

#### services/ — 业务层

- 每个service解决一个明确的业务问题
- 只调用 libs/ 层的接口，不直接依赖任何第三方SDK
- 包含业务校验逻辑（如"文档标题不能为空"），但不包含基础设施逻辑（如"HTTP请求重试3次"）

示例（wiki_service.py）：

```python
from ..libs.feishu_adapter import FeishuAdapter
from ..config.course_schema import Course

class WikiService:
    def __init__(self, feishu: FeishuAdapter):
        self.feishu = feishu

    def create_course_node(self, space_token: str, course: Course) -> dict:
        """为一门课程创建知识库节点并填充内容"""
        node = self.feishu.create_wiki_node(space_token, course.title)
        # 业务逻辑：填充课程信息
        ...
        return node

    def build_full_space(self, space_token: str, courses: list[Course]) -> list[dict]:
        """批量构建整个知识库"""
        results = []
        for course in courses:
            node = self.create_course_node(space_token, course)
            results.append(node)
        return results
```

#### glue/ — 编排层

- 代码风格：像写配置一样写代码，全是调用，没有条件分支和业务逻辑
- 唯一知道"先做什么、后做什么"的地方
- 错误处理：决定某个步骤失败时是继续还是回滚

示例（deploy.py）：

```python
from ..services.wiki_service import WikiService
from ..services.table_service import TableService
from ..services.doc_service import DocService
from ..services.material_service import MaterialService
from ..config.settings import Settings

def run_full_deploy(settings: Settings):
    feishu = FeishuAdapter(settings)
    wiki = WikiService(feishu)
    table = TableService(feishu)
    doc = DocService(feishu, settings.llm)
    material = MaterialService(feishu)

    space = wiki.create_space(settings.space_name)

    for course in settings.courses:
        wiki.create_course_node(space['token'], course)
        material.upload_course_files(course)
        doc.generate_guide(course)
        table.add_course_record(course)
```

---

## 四、重构策略：用什么替换什么

### 当前自写代码 → 应复用的成熟库

| 当前模块（自写） | 推荐替换为 | 理由 |
|----------------|-----------|------|
| feishu_service.py（手写HTTP请求+重试+认证） | `lark-oapi`（飞书官方Python SDK） | 官方维护，内置认证、重试、分页、类型定义 |
| llm_service.py（手写OpenAI格式调用） | `openai` SDK + 智谱base_url | 智谱API兼容OpenAI格式，直接用官方SDK |
| httpx调用逻辑 | 已有httpx，但统一到libs层 | 避免各处散落HTTP请求 |
| config.py（手写配置加载） | `pydantic-settings` | 带类型校验、环境变量支持、.env自动读取 |
| 分散的重试逻辑 | `tenacity` 或SDK内置重试 | 统一重试策略，避免各处参数不一致 |
| print日志 | `logging` + `structlog` | 标准化、可配置级别、可输出到文件 |
| orchestrator.py（5593行） | 拆入glue/层 | 编排代码不应超过200行 |

### 硬编码路径处理

当前 `config.py` 包含本地路径（`D:\c盘转移\...`），必须：
1. 删除所有硬编码绝对路径
2. 通过 `.env` 文件或命令行参数传入
3. `pydantic-settings` 自动读取环境变量并提供默认值
4. `.env.example` 中标注各变量的含义和示例值

### 依赖安装方式

```bash
pip install lark-oapi openai pydantic-settings tenacity structlog httpx python-dotenv
pip freeze > requirements.txt
```

---

## 五、重构执行步骤

### 第一阶段：基础设施搭建（不动旧代码）

1. 创建新目录结构（third_party/、libs/、services/、glue/、config/）
2. 搭建 `config/settings.py`（pydantic-settings），从.env读取所有配置
3. 实现 `libs/feishu_adapter.py`（基于lark-oapi）
4. 实现 `libs/llm_adapter.py`（基于openai SDK）
5. 编写对应的单元测试（tests/test_libs/）

### 第二阶段：业务层迁移

6. 重写 `services/wiki_service.py`，调用libs层
7. 重写 `services/table_service.py`，调用libs层
8. 重写 `services/doc_service.py`，调用libs层
9. 重写 `services/material_service.py`，调用libs层
10. 编写对应的集成测试（tests/test_services/）

### 第三阶段：编排层 + 入口

11. 实现 `glue/deploy.py`，串联所有service
12. 实现 `glue/pipeline.py`，拆分子流程
13. 更新 `deploy.py`（CLI入口）指向新的glue层
14. 编写端到端测试（tests/test_glue/）

### 第四阶段：清理

15. 删除旧代码（旧的services/目录、orchestrator.py等）
16. 更新 README.md
17. 确认所有测试通过，实际部署一次验证

---

## 六、代码质量红线

以下规则在重构过程中不可违反：

1. **third_party里的代码零修改** — 如需定制，在libs层封装
2. ** libs/ 每个文件不超过100行** — 超过说明封装粒度太粗
3. **services/ 不直接import任何第三方SDK** — 必须走libs
4. **无硬编码路径** — 所有路径通过配置传入
5. **无硬编码API Key** — 全部通过.env管理
6. **每个service可独立测试** — 不依赖其他service
7. **glue/层零业务逻辑** — 只有调用和流程控制
8. **错误类型统一** — libs层将SDK异常转换为自定义异常

---

## 七、大礼包项目的业务背景

PPE云端智能大礼包是一个为南开大学PPE专业设计的课程资料平台，部署在飞书云上。核心功能：

1. **知识库构建**：按年级→课程的层级创建飞书知识库，每个课程节点包含课程信息和学习指南
2. **多维表格**：自动创建课程信息表格，填充课程元数据（教师、学期、类型等）
3. **文档生成**：用LLM（智谱GLM）基于课程资料生成"学长学姐视角"的学习指南，写入飞书文档
4. **资料上传**：将本地课程资料（PDF、DOCX等）上传到飞书云盘并关联到对应知识库节点
5. **权限配置**：配置知识库和表格的访问权限

飞书应用凭据（通过.env配置）：
- App ID / App Secret
- 知识库 Space Token
- 多维表格 App Token

---

*本文档随重构进展持续更新。*
*创建时间：2026-05-11*
