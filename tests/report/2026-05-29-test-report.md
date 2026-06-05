# 测试报告 2026-05-29

## 测试环境

| 项目 | 值 |
|------|-----|
| Python 版本 | 3.14.2 |
| pytest 版本 | 9.0.3 |
| pytest-asyncio 版本 | 1.4.0 |
| lark-oapi 版本 | 1.6.5 |
| 飞书应用 ID | cli_a9283083fcf89cc2 |
| 知识空间 ID | 7624453064019168209 |
| 测试时间 | 2026-05-29 00:55 |

---

## Mock 单元测试结果

**命令：** `python -m pytest tests/test_services/ -v`  
**结果：9 passed, 16 warnings in 7.07s ✅**

| 测试文件 | 测试名 | 状态 |
|----------|--------|------|
| test_wiki_service.py | test_get_space_by_name_found | ✅ PASSED |
| test_wiki_service.py | test_get_space_by_name_not_found | ✅ PASSED |
| test_wiki_service.py | test_create_course_nodes | ✅ PASSED |
| test_wiki_service.py | test_create_year_nodes | ✅ PASSED |
| test_table_service.py | test_create_year_table | ✅ PASSED |
| test_table_service.py | test_add_course_record | ✅ PASSED |
| test_table_service.py | test_add_course_record_raises_without_table | ✅ PASSED |
| test_table_service.py | test_populate_year_courses_incremental_skips_existing | ✅ PASSED |
| test_table_service.py | test_populate_year_courses_incremental_adds_new | ✅ PASSED |

**Warnings（均不影响功能）：**
- Pydantic V2 deprecation：`Field(env=...)` 改用 `json_schema_extra`
- lark-oapi `utcfromtimestamp()` deprecation（SDK 内部，无法修改）

---

## 集成测试结果

**命令：** `python deploy.py wiki`  
**结果：EXIT 0 ✅ — 全部 18 门课程节点创建成功**

### 执行流程

1. `get_space_by_name("Demo PPE CloudSmart Giftbox")` → 找到已有空间 ID `7624453064019168209`
2. 创建四个学年根节点：大一 / 大二 / 大三 / 大四
3. 在各学年节点下创建 18 个课程节点（大一6门、大二7门、大三4门、大四1门）

### 执行耗时

约 40 秒（网络 I/O 绑定，每个节点需 ~2s API 往返）

### 已验证的飞书 API 调用

| API | 状态 |
|-----|------|
| `wiki.v2.space.alist`（列出知识空间） | ✅ |
| `wiki.v2.space_node.acreate`（创建节点） | ✅ |

---

## 本次 Session 发现并修复的 Bug

| # | 位置 | 描述 | 修复方案 |
|---|------|------|----------|
| B1 | `deploy.py` | typer 不支持 `async def` 命令函数 → coroutine 未被 await | 改为 `def` + `asyncio.run()` |
| B2 | `glue/deploy.py` | `_deploy_wiki` 始终尝试创建新空间，不检查是否已有同名空间 | 先调用 `get_space_by_name`，找到则直接使用 |
| B3 | `glue/pipeline.py` | 访问 `node["title"]` 但 `create_course_nodes` 返回 `"course_name"` | 改为 `node["course_name"]` |
| B4 | `libs/feishu/wiki.py` | `parent_node_token("")` 传入空字符串导致飞书报 `field validation failed` | 空字符串时不调用 `.parent_node_token()` |
| B5 | `libs/feishu/wiki.py` | Node builder 缺少 `.node_type("origin")` — 必填参数 | 添加 `.node_type("origin")` |
| B6 | `libs/feishu/wiki.py` | 访问 `node.url` 但 lark-oapi 1.6.5 的 `Node` 类未反序列化 url 字段 | 改为 `getattr(node, "url", "")` |

---

## 已知限制（本次不修复）

| 限制 | 说明 |
|------|------|
| Wiki 空间创建需 user_access_token | 飞书设计：创建知识空间需要用户授权，无法仅用 app tenant_access_token 完成。当前方案：使用已有空间，避免触发此限制 |
| lark-oapi 无 wiki node delete | `wiki.v2.space_node` 无 `adelete`，已用 httpx 直接调 REST 作为 workaround（参见 `libs/feishu/wiki.py:delete_wiki_node`） |
| 节点去重 | `wiki_pipeline` 每次运行都会新增节点，不检查重复。已在飞书端手动清理测试中产生的重复节点 |

---

## 下一步建议

1. **修复节点幂等性**：`wiki_pipeline` 执行前先调 `get_wiki_nodes` 检查是否已有同名节点，避免重复创建
2. **Pydantic V2 迁移**：`config/settings.py` 中的 `Field(env=...)` 改为 `model_config = SettingsConfigDict(env_prefix="")`
3. **表格集成测试**：运行 `python deploy.py tables --incremental` 验证 bitable 模块
4. **文档生成测试**：运行 `python deploy.py docs --limit 1` 验证 LLM + docx 模块端到端
