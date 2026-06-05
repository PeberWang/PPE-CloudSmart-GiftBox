# -*- coding: utf-8 -*-
"""飞书权限管理模块 - 基于 lark-oapi SDK"""

from typing import Dict, List
from lark_oapi.api.wiki.v2 import (
    CreateSpaceMemberRequest, Member,
    ListSpaceMemberRequest,
)
from libs.exceptions import FeishuAPIException


class PermMixin:
    """权限管理操作"""

    async def add_wiki_space_members(self, space_id: str, members: List[Dict[str, str]]) -> List[Dict]:
        """批量添加知识空间成员
        members: [{"member_type": "openid", "member_id": "ou_xxx", "perm_role": "editor"}, ...]
        """
        results = []
        for m in members:
            member = (Member.builder()
                      .member_type(m["member_type"])
                      .member_id(m["member_id"])
                      .member_role(m["perm_role"])
                      .build())
            request = (CreateSpaceMemberRequest.builder()
                       .space_id(space_id)
                       .request_body(member)
                       .build())
            resp = await self.client.wiki.v2.space_member.acreate(request)
            status = "added" if resp.success() else "failed"
            results.append({"member": m, "status": status})
        return results

    async def list_wiki_space_members(self, space_id: str, page_size: int = 50) -> List[Dict]:
        """列出知识空间成员（分页）"""
        all_members, page_token = [], None
        while True:
            builder = ListSpaceMemberRequest.builder().space_id(space_id).page_size(page_size)
            if page_token:
                builder = builder.page_token(page_token)
            resp = await self.client.wiki.v2.space_member.alist(builder.build())
            if not resp.success():
                raise FeishuAPIException(f"列出空间成员失败: {resp.msg}", error_code=str(resp.code))
            for member in (resp.data.items or []):
                all_members.append({"member_id": member.member_id, "member_type": member.member_type})
            if not resp.data.has_more:
                break
            page_token = resp.data.page_token
        return all_members
