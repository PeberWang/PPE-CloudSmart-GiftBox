# -*- coding: utf-8 -*-
"""飞书知识库(Wiki)模块 - 基于 lark-oapi SDK"""

import httpx
from typing import Dict, Any, List
from lark_oapi.api.wiki.v2 import (
    CreateSpaceRequest, Space,
    CreateSpaceNodeRequest, Node,
    ListSpaceRequest, GetSpaceRequest,
    ListSpaceNodeRequest,
)
from libs.exceptions import FeishuAPIException


class WikiMixin:
    """知识库操作"""

    async def create_wiki_space(self, space_name: str) -> Dict[str, str]:
        request = (CreateSpaceRequest.builder()
                   .request_body(Space.builder().name(space_name).build())
                   .build())
        resp = await self.client.wiki.v2.space.acreate(request)
        if not resp.success():
            raise FeishuAPIException(f"创建知识空间失败: {resp.msg}", error_code=str(resp.code))
        return {"space_id": resp.data.space.space_id, "name": resp.data.space.name}

    async def create_wiki_node(self, space_id: str, parent_node_id: str, title: str) -> Dict[str, str]:
        builder = Node.builder().obj_type("docx").node_type("origin").title(title)
        if parent_node_id:
            builder = builder.parent_node_token(parent_node_id)
        request = (CreateSpaceNodeRequest.builder()
                   .space_id(space_id)
                   .request_body(builder.build())
                   .build())
        resp = await self.client.wiki.v2.space_node.acreate(request)
        if not resp.success():
            raise FeishuAPIException(f"创建知识库节点[{title}]失败: {resp.msg}", error_code=str(resp.code))
        node = resp.data.node
        url = getattr(node, "url", "") or ""
        obj_token = getattr(node, "obj_token", "") or ""
        return {"node_id": node.node_token, "obj_token": obj_token, "title": node.title or title, "url": url}

    async def list_wiki_spaces(self, page_size: int = 50) -> List[Dict]:
        spaces, page_token = [], None
        while True:
            builder = ListSpaceRequest.builder().page_size(page_size)
            if page_token:
                builder = builder.page_token(page_token)
            resp = await self.client.wiki.v2.space.alist(builder.build())
            if not resp.success():
                raise FeishuAPIException(f"列出Wiki空间失败: {resp.msg}", error_code=str(resp.code))
            for s in (resp.data.items or []):
                spaces.append({"space_id": s.space_id, "name": s.name})
            if not resp.data.has_more:
                break
            page_token = resp.data.page_token
        return spaces

    async def get_wiki_space_info(self, space_id: str) -> Dict[str, Any]:
        request = GetSpaceRequest.builder().space_id(space_id).build()
        resp = await self.client.wiki.v2.space.aget(request)
        if not resp.success():
            raise FeishuAPIException(f"获取知识空间信息失败: {resp.msg}", error_code=str(resp.code))
        s = resp.data.space
        return {"space_id": s.space_id, "name": s.name}

    async def get_wiki_nodes(self, space_id: str, parent_node_id: str) -> Dict[str, Any]:
        builder = ListSpaceNodeRequest.builder().space_id(space_id).page_size(100)
        if parent_node_id:
            builder = builder.parent_node_token(parent_node_id)
        resp = await self.client.wiki.v2.space_node.alist(builder.build())
        if not resp.success():
            raise FeishuAPIException(f"获取知识库节点失败: {resp.msg}", error_code=str(resp.code))
        items = [{"node_token": n.node_token, "title": n.title} for n in (resp.data.items or [])]
        return {"items": items, "page_token": resp.data.page_token}

    async def create_wiki_bitable_node(self, space_id: str, parent_node_token: str,
                                        title: str, bitable_token: str) -> Dict[str, str]:
        """在 wiki 中创建指向已有 bitable 的节点（shortcut 模式，bitable 数据保留在原处）。"""
        builder = (Node.builder()
                   .obj_type("bitable")
                   .node_type("shortcut")
                   .origin_node_token(bitable_token)
                   .parent_node_token(parent_node_token)
                   .title(title))
        request = (CreateSpaceNodeRequest.builder()
                   .space_id(space_id)
                   .request_body(builder.build())
                   .build())
        resp = await self.client.wiki.v2.space_node.acreate(request)
        if not resp.success():
            raise FeishuAPIException(f"创建多维表格节点[{title}]失败: {resp.msg}", error_code=str(resp.code))
        node = resp.data.node
        url = getattr(node, "url", "") or ""
        return {"node_id": node.node_token, "title": node.title or title, "url": url}

    async def delete_wiki_node(self, space_id: str, node_id: str) -> bool:
        # lark-oapi 1.6.5 不支持 wiki node 删除（SDK 无 space_node.adelete）
        # 使用 httpx 直接调用 REST API，每次获取新 Token 避免过期
        try:
            async with httpx.AsyncClient(timeout=15.0) as http:
                auth = await http.post(
                    f"{self.base_url}/auth/v3/tenant_access_token/internal",
                    json={"app_id": self.app_id, "app_secret": self.app_secret}
                )
                token = auth.json()["tenant_access_token"]
                resp = await http.delete(
                    f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes/{node_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                return resp.json().get("code") == 0
        except Exception as e:
            self.logger.error("删除知识库节点异常", error=str(e))
            return False
