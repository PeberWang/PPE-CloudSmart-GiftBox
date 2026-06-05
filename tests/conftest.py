# -*- coding: utf-8 -*-
"""
pytest 全局 fixtures
MockFeishuAdapter 用于 services/ 层单元测试，替代真实 API 调用。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_feishu():
    """MockFeishuAdapter - 不发出真实 HTTP 请求，用于 services/ 层单元测试"""
    adapter = MagicMock()

    # ── wiki 方法 ──
    adapter.list_wiki_spaces = AsyncMock(return_value=[
        {"space_id": "space-001", "name": "Demo PPE CloudSmart Giftbox"},
    ])
    adapter.create_wiki_space = AsyncMock(return_value={
        "space_id": "space-001", "name": "Demo PPE CloudSmart Giftbox"
    })
    adapter.create_wiki_node = AsyncMock(return_value={
        "node_id": "node-001", "title": "测试节点", "url": ""
    })
    adapter.get_wiki_space_info = AsyncMock(return_value={
        "space_id": "space-001", "name": "Demo PPE CloudSmart Giftbox"
    })
    adapter.get_wiki_nodes = AsyncMock(return_value={"items": [], "page_token": None})
    adapter.delete_wiki_node = AsyncMock(return_value=True)

    # ── bitable 方法 ──
    adapter.create_bitable_table = AsyncMock(return_value={
        "table_id": "tbl-001", "table_name": "大一课程表", "url": ""
    })
    adapter.get_bitable_tables = AsyncMock(return_value=[
        {"table_id": "tbl-001", "name": "大一课程表"}
    ])
    adapter.add_bitable_record = AsyncMock(return_value={"record_id": "rec-001"})
    adapter.update_bitable_record = AsyncMock(return_value={"record_id": "rec-001"})
    adapter.search_bitable_record = AsyncMock(return_value=None)
    adapter.list_bitable_fields = AsyncMock(return_value=[])
    adapter.create_bitable_fields = AsyncMock(return_value=[])
    adapter.delete_bitable_table = AsyncMock(return_value=True)

    return adapter
