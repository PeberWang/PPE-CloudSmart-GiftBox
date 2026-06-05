# lark-oapi Python SDK 调查报告

> 调查时间：2026-05-29  
> 版本：lark-oapi 1.6.5（已安装）  
> 仓库：https://github.com/larksuite/oapi-sdk-python

---

## 一、SDK 基础特性

| 特性 | 说明 |
|------|------|
| 自动 Token 刷新 | ✅ Client 内部管理，2小时过期问题彻底解决 |
| 同步/异步 | 同步方法名直接调用，异步方法在方法名前加 `a` 前缀 |
| 请求构造 | Builder 模式，链式调用，类型安全 |
| 错误处理 | 统一 BaseResponse，有 `.success()` 方法和 `code/msg` 字段 |
| 安装 | `pip install lark-oapi`（已在 requirements.txt） |

---

## 二、Client 初始化

```python
import lark_oapi as lark

client = lark.Client.builder() \
    .app_id(settings.feishu_app_id) \
    .app_secret(settings.feishu_app_secret) \
    .build()
```

**注意：Client 是同步构造，不需要 async。**

---

## 三、异步调用模式

所有资源方法均有同步和异步两种版本：
- 同步：`client.wiki.v2.space.create(request)`
- 异步：`await client.wiki.v2.space.acreate(request)`

**本项目使用异步版本（与原 httpx 代码一致）。**

---

## 四、SDK Namespace 结构

```
client.wiki.v2
    .space          → acreate, aget, alist, aget_node
    .space_node     → acreate, alist, amove, acopy, aupdate_title
    .space_member   → acreate, adelete, alist

client.bitable.v1
    .app_table          → acreate, adelete, alist, abatch_create, abatch_delete
    .app_table_record   → acreate, adelete, aget, alist, aupdate, asearch, abatch_create, abatch_delete
    .app_table_field    → acreate, adelete, alist, aupdate

client.docx.v1
    .document                   → acreate, aget, araw_content
    .document_block_children    → acreate, aget, abatch_delete

client.drive.v1
    .media  → aupload_all
    .file   → adelete, alist, amove

client.wiki.v2.space_member → acreate, adelete, alist
```

---

## 五、18 方法迁移对照表

### Wiki（知识库）

| 原 httpx 方法 | lark-oapi 等价 | 说明 |
|---|---|---|
| `list_wiki_spaces()` | `await client.wiki.v2.space.alist(request)` | 分页获取 |
| `create_wiki_space(name)` | `await client.wiki.v2.space.acreate(request)` | |
| `create_wiki_node(space_id, parent, title)` | `await client.wiki.v2.space_node.acreate(request)` | |
| `get_wiki_space_info(space_id)` | `await client.wiki.v2.space.aget(request)` | |
| `get_wiki_nodes(space_id, parent)` | `await client.wiki.v2.space_node.alist(request)` | 分页 |
| `delete_wiki_node(space_id, node_id)` | ⚠️ **SDK 无此方法** | 见下方说明 |

### Bitable（多维表格）

| 原 httpx 方法 | lark-oapi 等价 | 说明 |
|---|---|---|
| `create_bitable_table(app_token, name)` | `await client.bitable.v1.app_table.acreate(request)` | |
| `get_bitable_tables(app_token)` | `await client.bitable.v1.app_table.alist(request)` | |
| `delete_bitable_table(app_token, table_id)` | `await client.bitable.v1.app_table.adelete(request)` | |
| `list_bitable_fields(app_token, table_id)` | `await client.bitable.v1.app_table_field.alist(request)` | |
| `create_bitable_fields(app_token, table_id, fields)` | `await client.bitable.v1.app_table_field.acreate(request)` × N | 逐个创建 |
| `add_bitable_record(app_token, table_id, fields)` | `await client.bitable.v1.app_table_record.acreate(request)` | |
| `update_bitable_record(app_token, table_id, record_id, fields)` | `await client.bitable.v1.app_table_record.aupdate(request)` | |
| `search_bitable_record(app_token, table_id, field, value)` | `await client.bitable.v1.app_table_record.asearch(request)` | 用 FilterInfo/Condition |

### Docx（文档）

| 原 httpx 方法 | lark-oapi 等价 | 说明 |
|---|---|---|
| `create_docx(space_id, title)` | `await client.docx.v1.document.acreate(request)` | |
| `write_docx_content(doc_id, content)` | `await client.docx.v1.document_block_children.acreate(request)` | |

### Drive（云盘）

| 原 httpx 方法 | lark-oapi 等价 | 说明 |
|---|---|---|
| `upload_file(file_path, file_name)` | `await client.drive.v1.media.aupload_all(request)` | |
| `delete_file(file_token)` | `await client.drive.v1.file.adelete(request)` | |

### Perm（权限）

| 原 httpx 方法 | lark-oapi 等价 | 说明 |
|---|---|---|
| `add_wiki_space_members(space_id, members)` | `await client.wiki.v2.space_member.acreate(request)` | 逐个创建 |
| `list_wiki_space_members(space_id)` | `await client.wiki.v2.space_member.alist(request)` | 分页 |

---

## 六、⚠️ SDK 不支持 Wiki Node/Space 删除

**已核实**：lark-oapi 1.6.5 的 `wiki.v2.space_node` 和 `wiki.v2.space` 均无 `adelete` 方法。

```
wiki.v2.space 的方法：acreate, aget, aget_node, alist（无 adelete）
wiki.v2.space_node 的方法：acreate, alist, amove, acopy, aupdate_title（无 adelete）
```

**处理方案**：保留 `libs/feishu/wiki.py` 中 `delete_wiki_node` 的 httpx 实现。
该方法仅在 rollback 流程中使用，2小时 Token 问题对回滚操作影响可接受。
在代码中添加注释说明此限制。

---

## 七、请求构造示例

### 创建知识库（Space）

```python
from lark_oapi.api.wiki.v2 import CreateSpaceRequest, Space

request = (CreateSpaceRequest.builder()
    .request_body(Space.builder().name("空间名称").build())
    .build())
response = await client.wiki.v2.space.acreate(request)
if not response.success():
    raise FeishuAPIException(f"创建空间失败: {response.msg}")
return {"space_id": response.data.space.space_id, "name": response.data.space.name}
```

### 创建知识库节点（Node）

```python
from lark_oapi.api.wiki.v2 import CreateSpaceNodeRequest, Node

request = (CreateSpaceNodeRequest.builder()
    .space_id(space_id)
    .request_body(Node.builder()
        .obj_type("doc")
        .parent_node_token(parent_node_token)
        .title(title)
        .build())
    .build())
response = await client.wiki.v2.space_node.acreate(request)
if not response.success():
    raise FeishuAPIException(f"创建节点失败: {response.msg}")
return {"node_token": response.data.node.node_token, "title": response.data.node.title}
```

### 列出知识库（分页）

```python
from lark_oapi.api.wiki.v2 import ListSpaceRequest

spaces = []
page_token = None
while True:
    builder = ListSpaceRequest.builder().page_size(50)
    if page_token:
        builder = builder.page_token(page_token)
    response = await client.wiki.v2.space.alist(builder.build())
    if not response.success():
        break
    spaces.extend(response.data.items or [])
    if not response.data.has_more:
        break
    page_token = response.data.page_token
```

### 搜索多维表格记录

```python
from lark_oapi.api.bitable.v1 import (
    SearchAppTableRecordRequest, SearchAppTableRecordRequestBody,
    FilterInfo, Condition
)

request = (SearchAppTableRecordRequest.builder()
    .app_token(app_token)
    .table_id(table_id)
    .request_body(SearchAppTableRecordRequestBody.builder()
        .filter(FilterInfo.builder()
            .conjunction("and")
            .conditions([
                Condition.builder()
                    .field_name(field_name)
                    .operator("is")
                    .value([value])
                    .build()
            ])
            .build())
        .build())
    .build())
response = await client.bitable.v1.app_table_record.asearch(request)
```

### 一次性上传文件到云盘

```python
from lark_oapi.api.drive.v1 import UploadAllMediaRequest, UploadAllMediaRequestBody
import os

file_size = os.path.getsize(file_path)
with open(file_path, "rb") as f:
    request = (UploadAllMediaRequest.builder()
        .request_body(UploadAllMediaRequestBody.builder()
            .file_name(file_name)
            .parent_type("drive_file")
            .parent_node("root")
            .size(file_size)
            .file(f)
            .build())
        .build())
response = await client.drive.v1.media.aupload_all(request)
```

---

## 八、响应对象访问模式

```python
response = await client.wiki.v2.space.alist(request)
response.success()           # bool，调用是否成功
response.code                # int，错误码（0=成功）
response.msg                 # str，错误信息
response.data                # 响应体对象（类型化的Python对象）
response.data.items          # List[Space]，分页结果
response.data.has_more       # bool，是否还有更多
response.data.page_token     # str，下一页token
```

---

## 九、已安装版本信息

```
lark-oapi == 1.6.5
Python >= 3.10（本项目要求）
```
