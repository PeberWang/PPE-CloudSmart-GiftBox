# 飞书开放平台知识沉淀

> 本文档记录 PPE-CloudSmart-GiftBox 项目中与飞书 API 相关的实现细节、权限配置和最佳实践。

---

## 一、官方资源

### 1.1 SDK 与文档

| 资源 | 链接 | 说明 |
|------|------|------|
| Python SDK | https://github.com/larksuite/oapi-sdk-python | 官方 Python SDK |
| API 文档 | https://open.larksuite.com/document/uAjLw4CM/ukTMukTM/uETO1YjL4UTN24CO1UjN | Server SDK 文档 |
| Wiki API | https://open.larksuite.com/document/uAjLw4CM/ukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/overview | Wiki 空间总览 |
| 开放平台 | https://open.feishu.cn/ | 应用管理后台 |

### 1.2 关键 API 端点

| 功能 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 列出 Wiki 空间 | `/wiki/v2/spaces` | GET | `list` 参数支持分页 |
| 获取 Wiki 空间信息 | `/wiki/v2/spaces/:space_id` | GET | 根据 space_id 查询 |
| 创建 Wiki 节点 | `/wiki/v2/spaces/:space_id/nodes` | POST | 支持 parent_node_token |
| 列出 Wiki 节点 | `/wiki/v2/spaces/:space_id/nodes` | GET | 支持 parent_node_token 和 page_token |
| 创建 Wiki 空间 | `/wiki/v2/spaces` | POST | 需要 `wiki:space:create` 权限 |
| 创建文档 | `/docx/v1/documents` | POST | 支持关联 wiki 空间 |

---

## 二、权限体系

### 2.1 权限范围

飞书 API 使用两种主要 token：

| Token 类型 | 用途 | 权限要求 | 对应 API |
|------------|------|----------|----------|
| `tenant_access_token` | 租户级访问 | 大部分操作 | 创建节点、创建文档、上传文件 |
| `app_access_token` | 应用级访问 | 应用管理 | 创建空间、多维表格 |

### 2.2 权限配置流程

#### 配置步骤：
1. 登录飞书开放平台：https://open.feishu.cn/
2. 进入应用管理
3. 找到应用（App ID: `cli_a9283083fcf89cc2`）
4. 进入「权限管理」
5. 添加以下权限：
   - `wiki:space:create` - 创建知识空间
   - `wiki:node:create` - 创建知识库节点
   - `wiki:node:read` - 读取知识库节点
   - `docx:document:create` - 创建文档
   - `docx:document:read` - 读取文档
   - `drive:file:upload` - 上传文件

### 2.3 权限验证方法

```bash
# 验证应用是否有创建空间权限
curl -X POST https://open.feishu.cn/open-apis/wiki/v2/spaces \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试空间"}'

# 预期成功响应：{"code": 0, "data": {...}}
# 预期错误响应（无权限）：{"code": 99991663, "msg": "Invalid access token..."}
```

---

## 三、实现架构对比

### 3.1 官方推荐 vs 当前实现

| 项目 | 官方推荐 | 当前实现 | 差距 |
|------|----------|----------|------|
| SDK | `lark-oapi` | `httpx` 直接调用 | ❌ |
| Token 管理 | SDK 自动管理 | 手动管理 | ⚠️ |
| 错误处理 | SDK 内置 | 手动检查 | ⚠️ |
| 代码量 | 更少 | 更多 | ⚠️ |

### 3.2 迁移计划

**当前状态**：
- ✅ 基础架构已搭建（config/, libs/, services/, glue/）
- ✅ Wiki 节点创建 API 已实现
- ⚠️ 使用 `httpx` 而非 `lark-oapi` SDK
- ⚠️ 使用硬编码 space_id（7624453064019168209）

**建议迁移路径**：
1. **Phase 1**: 替换 `httpx` 为 `lark-oapi`
   - 修改 `libs/feishu_adapter.py`
   - 使用 `Client.builder()` 初始化
   - 利用 SDK 内置的重试和错误处理

2. **Phase 2**: 添加 Wiki Space 管理 API
   - 实现 `list_wiki_spaces()`
   - 实现 `get_wiki_space_info()`
   - 替换硬编码 space_id

3. **Phase 3**: 添加文档创建 API
   - 实现使用 SDK 创建文档
   - 关联到 Wiki 空间

---

## 四、当前实现细节

### 4.1 Token 管理

**当前实现**（`libs/feishu_adapter.py`）：

```python
# 获取 tenant_access_token（用于创建节点、文档）
async def get_tenant_access_token(self) -> str:
    url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
    response = await self.client.post(url, json={
        "app_id": self.app_id,
        "app_secret": self.app_secret
    })
    result = response.json()
    if result["code"] == 0:
        self.tenant_access_token = result["tenant_access_token"]
    return self.tenant_access_token

# 获取 app_access_token（用于创建空间、表格）
async def get_app_access_token(self) -> str:
    url = f"{self.base_url}/auth/v3/app_access_token/internal"
    response = await self.client.post(url, json={
        "app_id": self.app_id,
        "app_secret": self.app_secret
    })
    result = response.json()
    if result["code"] == 0:
        self.app_access_token = result["app_access_token"]
    return self.app_access_token
```

### 4.2 Wiki 节点创建

**API 端点**：`POST /wiki/v2/spaces/{space_id}/nodes`

**请求参数**：
```json
{
  "obj_type": "docx",           // 节点类型：docx=文档, page=页面
  "node_type": "origin",         // 节点类型：origin=原始节点
  "node_title": "节点标题",
  "parent_node_token": ""       // 空表示挂在空间根目录
}
```

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "node": {
      "node_token": "xxx",      // 节点 token
      "origin_space_id": "xxx",  // 所属空间 ID
      "parent_node_token": "xxx",  // 父节点 token
      "title": "",                  // API 返回空标题
      "obj_type": "docx",
      "obj_token": "xxx",          // 文档对象 token
      "has_child": false
    }
  }
}
```

**错误码说明**：
| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| 99991663 | Token 类型错误 | 使用正确的 token 类型 |
| 131005 | 未找到资源 | 检查 parent_node_token 是否有效 |

---

## 五、配置管理

### 5.1 环境变量

`.env.example` 已定义以下变量：

```bash
# 飞书应用配置
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=your_app_secret_here
FEISHU_BASE_URL=https://open.feishu.cn/open-apis

# 智谱AI配置
ZHIPU_API_KEY=your_zhipu_api_key_here
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
ZHIPU_MODEL=glm-4-flash

# 路径配置
MATERIALS_BASE=./data/courses
COURSE_REFORM_NOTES_DIR=./data/course_reform_notes

# 知识库配置
WIKI_SPACE_NAME=Demo PPE CloudSmart Giftbox

# 多维表格配置
BITABLE_APP_TOKEN=  # 将在创建表格后填充

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=./logs/app.log
```

### 5.2 配置加载

使用 `pydantic-settings` 自动加载：

```python
# libs/feishu_adapter.py
from ..config.settings import Settings

settings = Settings()
# settings.feishu_app_id -> 从环境变量 FEISHU_APP_ID 读取
# settings.feishu_app_secret -> 从环境变量 FEISHU_APP_SECRET 读取
```

---

## 六、最佳实践

### 6.1 错误处理

**重试策略**：
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def create_wiki_node_with_retry(self, ...):
    # 自动重试，指数退避
    ...
```

**错误分类**：
- **可重试**：网络超时、连接错误、服务暂时不可用
- **不可重试**：权限不足、参数错误、资源不存在

### 6.2 日志规范

```python
import structlog

logger = structlog.get_logger()

# 不同级别
logger.info("开始部署")      # 信息
logger.warning("权限不足")   # 警告
logger.error("API调用失败")   # 错误

# 结构化日志
logger.info("创建节点", space_id=xxx, title=xxx)
```

### 6.3 分页处理

对于可能返回大量数据的 API，需要支持分页：

```python
async def get_all_wiki_nodes(self, space_id: str):
    """获取所有节点（支持分页）"""
    all_nodes = []
    page_token = None

    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token

        response = await self.client.get(url, params=params)
        result = response.json()

        all_nodes.extend(result["data"]["items"])
        page_token = result["data"].get("page_token")

        if not page_token:
            break

    return all_nodes
```

---

## 七、已知问题与限制

### 7.1 当前已知问题

| 问题 | 状态 | 说明 |
|------|------|------|
| 无法创建 Wiki 空间 | ❌ | 应用缺少 `wiki:space:create` 权限 |
| 使用 httpx 而非 lark-oapi | ⚠️ | 无法利用 SDK 内置特性 |
| 硬编码 space_id | ⚠️ | 需要动态获取或配置 |
| 缺少 Wiki Space List API | ⚠️ | 无法列出多个空间 |

### 7.2 限制说明

| 限制 | 值 | 说明 |
|------|------|------|
| 单次请求分页大小 | 100 | 飞书 API 限制 |
| Token 有效期 | ~2 小时 | 需要刷新 |
| 文件上传大小 | 1GB | 飞书限制 |

---

## 八、待完善功能

### 8.1 高优先级

- [ ] 实现 `list_wiki_spaces()` API
- [ ] 实现 `get_wiki_space_info()` API
- [ ] 替换硬编码 space_id 为配置项
- [ ] 添加文档创建 API（使用 SDK）
- [ ] 实现文件上传到 Wiki 关联

### 8.2 中优先级

- [ ] 迁移到 `lark-oapi` SDK
- [ ] 实现完整的重试机制（tenacity）
- [ ] 添加结构化日志（structlog）
- [ ] 实现分页支持

### 8.3 低优先级

- [ ] 添加 Wiki 空间删除 API
- [ ] 添加节点删除/移动 API
- [ ] 实现文档内容批量更新
- [ ] 添加多维表格字段管理

---

## 九、参考代码片段

### 9.1 使用 lark-oapi SDK（目标实现）

```python
from lark_oapi import Client, LogLevel
from lark_oapi.api.wiki.v2 import CreateSpaceNodeRequest, CreateSpaceNodeRequestBodyBuilder

class FeishuAdapterV2:
    """使用 lark-oapi SDK 的飞书适配器"""

    def __init__(self, settings: Settings):
        self.client = Client.builder() \
            .app_id(settings.feishu_app_id) \
            .app_secret(settings.feishu_app_secret) \
            .log_level(LogLevel.INFO) \
            .build()

    async def create_wiki_node(self, space_id: str, parent_node_id: str, title: str) -> dict:
        """创建 Wiki 节点"""
        request_body = CreateSpaceNodeRequestBodyBuilder() \
            .obj_type("docx") \
            .node_type("origin") \
            .node_title(title) \
            .parent_node_token(parent_node_id) \
            .build()

        request = CreateSpaceNodeRequest.builder() \
            .space_id(space_id) \
            .request_body(request_body) \
            .build()

        response = await self.client.request(request)

        if response.code != 0:
            raise FeishuAPIException(f"创建节点失败: {response.msg}")

        return {
            "node_id": response.data.node.node_token,
            "title": response.data.node.title,
            "url": response.data.node.url
        }

    async def close(self):
        await self.client.close()
```

### 9.2 Wiki Space 管理（待实现）

```python
from lark_oapi.api.wiki.v2 import ListSpacesRequest

async def list_wiki_spaces(self):
    """列出所有可访问的 Wiki 空间"""
    request = ListSpacesRequest.builder().build()
    response = await self.client.request(request)

    if response.code != 0:
        raise FeishuAPIException(f"列出空间失败: {response.msg}")

    return response.data.items
```

---

## 十、快速参考

### 10.1 常用命令

```bash
# 测试应用权限（需要先配置）
curl -X POST https://open.feishu.cn/open-apis/wiki/v2/spaces \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试空间"}'

# 列出 Wiki 空间
curl "https://open.feishu.cn/open-apis/wiki/v2/spaces" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 10.2 调试技巧

1. **启用详细日志**：在 Settings 中设置 `log_level = DEBUG`
2. **使用飞书调试工具**：https://open.feishu.cn/api-explorer/
3. **查看请求日志**：在飞书开放平台的「调用记录」中查看
4. **验证 Token**：使用 Token 验证工具确保 token 有效

---

*最后更新：2026-05-11*
