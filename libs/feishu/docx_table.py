# -*- coding: utf-8 -*-
"""飞书 Docx 原生表格操作 Mixin — create_descendant_tree / list_top_blocks / delete_blocks。

从 docx.py 中分离，保持每文件 <=100 行约束。通过 FeishuAdapter 多重继承组合。
"""

from typing import Any, Dict, List, Union

import lark_oapi as lark
from lark_oapi.api.docx.v1 import (
    Block,
    ListDocumentBlockRequest,
    BatchDeleteDocumentBlockChildrenRequest,
    BatchDeleteDocumentBlockChildrenRequestBody,
)
from libs.exceptions import FeishuAPIException


class DocxTableMixin:
    """Docx 原生表格专用操作 — 需与 FeishuAdapter 组合使用（self.client 可用）。"""

    async def create_descendant_tree(self, doc_id: str, tree, index: int = -1) -> int:
        """通过 descendant API 创建嵌套块树（如原生表格），返回下一个空闲 index。

        tree: blocks.BlockTree（top_id + descendants dict 列表）
        index: -1 表示末尾追加；其他值表示精确位置

        实现用 lark.BaseRequest 发送 raw JSON（绕过 SDK 的 Block builder 限制），
        按 2026-06-18 FAQ 验证的两层结构（table → cell）。
        """
        body = {
            "index": index,
            "children_id": [tree.top_id],
            "descendants": tree.descendants,
        }
        req = (lark.BaseRequest.builder()
               .http_method(lark.HttpMethod.POST)
               .uri(f"/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/descendant")
               .queries([("document_revision_id", "-1")])
               .token_types({lark.AccessTokenType.TENANT})
               .body(body)
               .build())
        resp = await self.client.arequest(req)
        if not resp.success():
            raise FeishuAPIException(f"创建嵌套块树失败: {resp.msg}",
                                     error_code=str(resp.code))
        return index + 1 if index >= 0 else index

    async def write_mixed_blocks(self, doc_id: str,
                                 items: List[Union[Block, Any]], index: int = -1) -> int:
        """写入混合 block 列表（Block 或 BlockTree），返回末尾 index。

        自动按类型分发：Block 走 append_blocks；BlockTree 走 create_descendant_tree。
        连续的普通 Block 会合并为一次 append_blocks 调用，减少 API 往返。
        """
        from libs.feishu.blocks import BlockTree

        pending_regular: List[Block] = []
        for item in items:
            if isinstance(item, BlockTree):
                if pending_regular:
                    index = await self.append_blocks(doc_id, pending_regular, index=index)
                    pending_regular = []
                index = await self.create_descendant_tree(doc_id, item, index=index)
            else:
                pending_regular.append(item)
        if pending_regular:
            index = await self.append_blocks(doc_id, pending_regular, index=index)
        return index

    async def list_top_blocks(self, doc_id: str, page_size: int = 50) -> List[Dict]:
        """列出文档顶层块，返回 [{block_id, block_type, parent_id, text, ...}]。

        text 字段从 block.text.elements 提取，供 replace_year_overview 等
        按内容定位旧块的场景使用。
        """
        req = (ListDocumentBlockRequest.builder()
               .document_id(doc_id).page_size(page_size).build())
        resp = await self.client.docx.v1.document_block.alist(req)
        if not resp.success():
            raise FeishuAPIException(f"列出文档块失败: {resp.msg}", error_code=str(resp.code))
        items = resp.data.items or []
        result = []
        for item in items:
            # 提取 text 内容（如有）
            text_content = ""
            if hasattr(item, "text") and item.text and hasattr(item.text, "elements"):
                elements = item.text.elements or []
                text_content = "".join(
                    (e.text_run.content if e.text_run else "")
                    for e in elements if e
                )
            result.append({
                "block_id": item.block_id,
                "block_type": item.block_type,
                "parent_id": item.parent_id,
                "text": text_content,
            })
        return result

    async def delete_blocks(self, doc_id: str, start_index: int, end_index: int) -> None:
        """按 index 范围 [start, end) 删除文档根级块。"""
        body = (BatchDeleteDocumentBlockChildrenRequestBody.builder()
                .start_index(start_index).end_index(end_index).build())
        req = (BatchDeleteDocumentBlockChildrenRequest.builder()
               .document_id(doc_id).block_id(doc_id)
               .request_body(body).build())
        resp = await self.client.docx.v1.document_block_children.abatch_delete(req)
        if not resp.success():
            raise FeishuAPIException(f"批量删除块失败: {resp.msg}", error_code=str(resp.code))
