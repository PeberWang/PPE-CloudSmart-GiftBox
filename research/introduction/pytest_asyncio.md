# pytest-asyncio 使用规范

> 调查时间：2026-05-29  
> 适用版本：pytest-asyncio（已在 requirements.txt 需补充）

---

## 一、配置（pyproject.toml）

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

`asyncio_mode = "auto"` 意味着所有 `async def test_*` 函数自动被 pytest-asyncio 接管，无需手动添加 `@pytest.mark.asyncio` 装饰器。

---

## 二、安装

```bash
pip install pytest pytest-asyncio
```

连同 `requirements.txt` 中应有的声明：
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

---

## 三、conftest.py 模板

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_feishu():
    """MockFeishuAdapter - 用于 services/ 层单元测试，替代真实 API 调用"""
    adapter = MagicMock()

    # wiki 方法
    adapter.list_wiki_spaces = AsyncMock(return_value=[
        {"space_id": "test-space-id", "name": "测试空间"}
    ])
    adapter.create_wiki_space = AsyncMock(return_value={
        "space_id": "test-space-id", "name": "测试空间"
    })
    adapter.create_wiki_node = AsyncMock(return_value={
        "node_token": "test-node-token", "title": "测试节点"
    })
    adapter.get_wiki_space_info = AsyncMock(return_value={
        "space_id": "test-space-id", "name": "测试空间"
    })
    adapter.get_wiki_nodes = AsyncMock(return_value=[])
    adapter.delete_wiki_node = AsyncMock(return_value=True)

    # bitable 方法
    adapter.create_bitable_table = AsyncMock(return_value={
        "table_id": "test-table-id", "name": "大一"
    })
    adapter.get_bitable_tables = AsyncMock(return_value=[
        {"table_id": "test-table-id", "name": "大一"}
    ])
    adapter.add_bitable_record = AsyncMock(return_value={
        "record_id": "test-record-id"
    })
    adapter.update_bitable_record = AsyncMock(return_value=True)
    adapter.search_bitable_record = AsyncMock(return_value=None)
    adapter.list_bitable_fields = AsyncMock(return_value=[])
    adapter.create_bitable_fields = AsyncMock(return_value=True)
    adapter.delete_bitable_table = AsyncMock(return_value=True)

    return adapter
```

---

## 四、async 测试写法

```python
# tests/test_services/test_wiki_service.py
import pytest
from services.wiki_service import WikiService


async def test_get_space_by_name_found(mock_feishu):
    """找到指定名称的知识库空间"""
    service = WikiService(mock_feishu)
    result = await service.get_space_by_name("测试空间")
    assert result["space_id"] == "test-space-id"
    mock_feishu.list_wiki_spaces.assert_called_once()


async def test_get_space_by_name_not_found(mock_feishu):
    """找不到时返回 None"""
    service = WikiService(mock_feishu)
    result = await service.get_space_by_name("不存在的空间")
    assert result is None


async def test_create_course_nodes(mock_feishu):
    """批量创建课程节点"""
    from config.course_schema import Course
    service = WikiService(mock_feishu)
    courses = [Course(name="伦理学导论"), Course(name="微观经济学")]
    results = await service.create_course_nodes("test-space-id", "test-year-node", courses)
    assert len(results) == 2
    assert mock_feishu.create_wiki_node.call_count == 2
```

---

## 五、注意事项

1. **auto mode**：无需 `@pytest.mark.asyncio`，直接写 `async def test_*` 即可
2. **AsyncMock vs MagicMock**：async 方法必须用 `AsyncMock`，否则 `await` 会报错
3. **fixture 不需要 async**：`conftest.py` 中的 fixture 可以是普通函数（返回同步对象）
4. **依赖注入一致**：services 层接受 `feishu` adapter 构造参数，测试时传入 mock_feishu

---

## 六、运行命令

```bash
# 运行所有测试
python -m pytest tests/ -v

# 只运行 services 层测试
python -m pytest tests/test_services/ -v

# 运行并显示关键信息
python -m pytest tests/ -v --tb=short

# 带覆盖率（需安装 pytest-cov）
python -m pytest tests/ --cov=services --cov-report=term-missing
```
