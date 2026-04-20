# 深度模块化重构日志

**日期**: 2026-04-20 23:35
**操作者**: 小劳（AI）

## 改动概览

本次重构对 PPE-CloudSmart-GiftBox 项目进行了深度模块化改造，涉及 7 大类改动。

## 1. 包名更新: ppe_demo → ppe_giftbox

- 重命名 `ppe_demo/` 目录为 `ppe_giftbox/`
- 更新所有 import 语句（deploy.py、tests/、services/ 中所有文件）
- 更新 .gitignore 中相关路径

## 2. config.py 瘦身

将以下内容从 config.py 移至 `ppe_giftbox/data/course_schema.py`：
- `COURSES_BY_YEAR`（课程数据）
- `BITABLE_COURSE_FIELDS`（多维表格字段定义）
- `MATERIAL_TYPES`、`GRADES`、`WIKI_YEAR_NODES`
- `PROTECTED_FIELDS`
- `WIKI_SPACE_NAME`

config.py 现在只保留：路径解析、API凭据、目录常量、`DEPLOY_OUTPUT_DIR`（新增）。

## 3. deploy.py 拆分

- `deploy_cleanup()` → `ppe_giftbox/services/cleanup/cleanup_service.py`
- 编排逻辑（deploy_full、deploy_mode 中的流程控制）→ `ppe_giftbox/services/orchestrator.py`
- CLI 入口（argparse + main）保留在 deploy.py（仅 ~40 行）

## 4. services/ 按职责重组

| 子目录 | 文件 | 职责 |
|--------|------|------|
| `services/core/` | feishu_service.py, llm_service.py, pipeline.py, experience_service.py | 基础服务 |
| `services/wiki/` | wiki_builder.py | 知识库构建 |
| `services/bitable/` | table_service.py | 多维表格管理 |
| `services/docs/` | doc_generator.py, link_service.py | 文档生成与关联 |
| `services/materials/` | material_uploader.py, upload_service.py | 资料上传 |
| `services/cleanup/` | cleanup_service.py（新建） | 部署清理 |

每个子目录均包含 `__init__.py`。所有 import 语句已从 `from services.xxx` / `from config` / `from models` 更新为完整的包路径 `from ppe_giftbox.xxx`。

## 5. 部署产物分离

- `wiki_structure.json` → `output/wiki_structure.json`
- `bitable_config.json` → `output/bitable_config.json`
- 所有引用这两个文件路径的代码已更新为使用 `DEPLOY_OUTPUT_DIR`
- `materials.json`、`experiences.json`、`report.json` 等源数据留在 `ppe_giftbox/data/`

## 6. log 文件夹

已存在，保留现有日志不变。

## 7. README.md

更新目录结构、技术架构描述、更新日志（新增 v3.0）。

## 新增文件

- `ppe_giftbox/data/course_schema.py` — 课程数据与字段定义
- `ppe_giftbox/data/__init__.py`
- `ppe_giftbox/services/orchestrator.py` — 部署编排
- `ppe_giftbox/services/cleanup/__init__.py`
- `ppe_giftbox/services/cleanup/cleanup_service.py`
- `ppe_giftbox/services/core/__init__.py`
- `ppe_giftbox/services/wiki/__init__.py`
- `ppe_giftbox/services/bitable/__init__.py`
- `ppe_giftbox/services/docs/__init__.py`
- `ppe_giftbox/services/materials/__init__.py`

## 删除文件（通过重命名/移动）

- `ppe_demo/` 整个目录（所有文件移至 `ppe_giftbox/` 对应位置）

## 关键约束遵守

- ✅ 所有现有功能保持不变
- ✅ 未删除任何数据文件
- ✅ 所有 import 已正确更新
- ✅ 所有 .py 文件通过语法检查（py_compile）
- ✅ tests/ 下的 import 路径已更新
