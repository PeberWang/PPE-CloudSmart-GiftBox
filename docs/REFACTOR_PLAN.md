# PPE-CloudSmart-GiftBox 重构任务追踪

> 最后更新：2026-05-18

---

## 当前状态

**重构阶段**：架构合规清理（第五阶段）
**入口 CLI**：typer（已替换 argparse）

---

## 已完成任务

### 第一阶段：基础设施搭建 ✅
- [x] config/settings.py — pydantic-settings 配置管理
- [x] config/course_schema.py — 课程数据结构
- [x] libs/feishu/ — 飞书适配器（拆分为 5 个子模块）
- [x] libs/llm_adapter.py — LLM 适配器（精简版，仅 generate_completion + generate_with_json）
- [x] libs/data_adapter.py — 数据文件适配器（封装 pandas/openpyxl）
- [x] libs/exceptions.py — 自定义异常类

### 第二阶段：业务层迁移 ✅
- [x] services/wiki_service.py
- [x] services/table_service.py
- [x] services/doc_service.py（Jinja2 模板驱动）
- [x] services/material_service.py
- [x] services/import_service.py（通过 DataAdapter 调用）
- [x] services/perm_service.py

### 第三阶段：编排层 ✅
- [x] glue/deploy.py（精简至 133 行，字典调度）
- [x] glue/pipeline.py
- [x] glue/rollback.py

### 第四阶段：入口与清理 ✅
- [x] deploy.py 迁移至 typer CLI
- [x] 删除旧 ppe_giftbox/ 和 ppe_demo/ 目录
- [x] 删除重复目录（support/, memorandum/, auto/）
- [x] 删除死代码（config/table_fields.py, libs/course_db.py）
- [x] 删除旧测试文件（10 个根目录 + 6 个 tests/ 文件）
- [x] 清理 __pycache__

### 第五阶段：架构合规修复 ✅
- [x] feishu_adapter.py 拆分为 libs/feishu/ 包（6 个模块）
- [x] LLM 业务逻辑从 libs/ 移至 services/doc_service.py
- [x] Jinja2 模板系统（config/prompts/guide_gen.j2）
- [x] 创建 libs/data_adapter.py（修复 import_service 架构违规）
- [x] 删除重复数据模型（course_db.py, table_fields.py）
- [x] glue/deploy.py 简化（360 → 133 行）

---

### 第六阶段：Stub 实现 ✅
- [x] **Task 6.1** — 实现表字段创建（BitableMixin + create_bitable_fields/list_bitable_fields API，create_table_fields 跳过已存在字段）
- [x] **Task 6.2** — 实现记录更新（update_course_record 搜索+更新+新增回退逻辑，_resolve_table_id 辅助方法）
- [x] **Task 6.3** — 实现权限服务（新增 libs/feishu/perm.py PermMixin，wiki 空间成员管理 API）
- [x] **Task 6.4** — 实现增量同步（_deploy_sync 函数，populate_year_courses 支持 is_incremental 参数，跳过已有记录）
- [x] **Task 6.5** — 修复硬编码 space_id（list_wiki_spaces API + get_space_by_name 实际搜索逻辑）

## 待完成任务

### 中期

- [ ] **Task 7.1** — 从 httpx 迁移到 lark-oapi SDK
- [ ] **Task 7.2** — 替换自定义 api_retry 为 tenacity
- [ ] **Task 7.3** — 实现表单数据导入（Excel/CSV → 多维表格）

### 测试

- [ ] **Task 8.1** — libs/ 层单元测试
- [ ] **Task 8.2** — services/ 层单元测试
- [ ] **Task 8.3** — glue/ 层单元测试
- [ ] **Task 8.4** — 端到端集成测试

---

## 项目结构（当前）

```
PPE-CloudSmart-GiftBox/
├── config/
│   ├── settings.py
│   ├── course_schema.py
│   └── prompts/
│       └── guide_gen.j2          # Jinja2 模板
├── libs/
│   ├── feishu/                   # 飞书适配器包
│   │   ├── __init__.py           # FeishuAdapter 外观类
│   │   ├── auth.py               # 认证模块
│   │   ├── wiki.py               # 知识库模块
│   │   ├── docx.py               # 文档模块
│   │   ├── drive.py              # 云盘模块
│   │   ├── bitable.py            # 表格模块
│   │   └── perm.py               # 权限模块
│   ├── llm_adapter.py            # LLM 适配器（精简）
│   ├── data_adapter.py           # 数据文件适配器
│   └── exceptions.py
├── services/
│   ├── wiki_service.py
│   ├── table_service.py
│   ├── doc_service.py            # Jinja2 模板渲染
│   ├── material_service.py
│   ├── import_service.py         # 通过 DataAdapter
│   └── perm_service.py
├── glue/
│   ├── deploy.py                 # 133 行，字典调度
│   ├── pipeline.py
│   └── rollback.py
├── tests/
│   ├── test_rollback.py
│   ├── test_material_upload.py
│   └── test_doc_link.py
├── data/
├── docs/
├── log/
├── tools/
├── deploy.py                     # typer CLI 入口
├── requirements.txt
├── .env.example
├── .gitignore
├── GLUE_CODING_GUIDE.md
└── README.md
```
