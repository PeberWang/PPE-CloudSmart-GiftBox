# -*- coding: utf-8 -*-
"""飞书权限管理模块 - 基于 lark-oapi SDK"""

from typing import Dict, List
from lark_oapi.api.wiki.v2 import (
    CreateSpaceMemberRequest, Member,
    ListSpaceMemberRequest,
)
from lark_oapi.api.drive.v1 import (
    CreatePermissionMemberRequest,
    PatchPermissionPublicRequest,
    PermissionPublic,
)
from lark_oapi.api.drive.v1.model.base_member import BaseMember
from libs.exceptions import FeishuAPIException


class PermMixin:
    """权限管理操作"""

    async def open_doc_public(self, token: str, doc_type: str,
                              link_share_entity: str = "anyone_editable") -> Dict:
        """设置云文档的链接分享权限（不需要加协作者，凭链接即可访问）。

        link_share_entity 选项：
        - "closed" — 关闭链接分享
        - "tenant_readable" — 组织内可阅读
        - "tenant_editable" — 组织内可编辑
        - "anyone_readable" — 任何人可阅读
        - "anyone_editable" — 任何人可编辑（个人版飞书常用）
        """
        body = (PermissionPublic.builder()
                .link_share_entity(link_share_entity)
                .build())
        req = (PatchPermissionPublicRequest.builder()
               .token(token)
               .type(doc_type)
               .request_body(body)
               .build())
        resp = await self.client.drive.v1.permission_public.apatch(req)
        if not resp.success():
            raise FeishuAPIException(
                f"修改链接分享权限失败: {resp.msg}", error_code=str(resp.code))
        return {"token": token, "link_share_entity": link_share_entity}

    async def add_doc_member(self, token: str, doc_type: str,
                             member_type: str, member_id: str,
                             perm: str = "full_access",
                             notify: bool = False) -> Dict:
        """添加云文档协作者（适用于 bitable/docx/sheet 等所有云文档）。

        member_type: "email" / "openid" / "userid" / "departmentid"
        perm: "view" / "edit" / "full_access"
        """
        member = (BaseMember.builder()
                  .member_type(member_type)
                  .member_id(member_id)
                  .perm(perm)
                  .build())
        req = (CreatePermissionMemberRequest.builder()
               .token(token)
               .type(doc_type)
               .need_notification(notify)
               .request_body(member)
               .build())
        resp = await self.client.drive.v1.permission_member.acreate(req)
        if not resp.success():
            raise FeishuAPIException(
                f"添加协作者失败: {resp.msg}", error_code=str(resp.code))
        return {"member_id": member_id, "member_type": member_type,
                "perm": perm, "doc_type": doc_type}

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
