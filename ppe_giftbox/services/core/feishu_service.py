# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 飞书服务
整合飞书Wiki、Docx、Bitable、Drive四大模块
"""

import httpx
import json
import time
import os
import asyncio
import logging
from typing import Optional, Dict, List

logger = logging.getLogger("feishu_service")

from ppe_giftbox.config import FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_BASE_URL


def api_retry(max_retries: int = 3, delay: float = 1.5, backoff: float = 2.0):
    """飞书 API 调用重试装饰器"""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            last_err = None
            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)
                except httpx.TimeoutException as e:
                    last_err = e
                    wait = delay * (backoff ** attempt)
                    logger.warning("请求超时(%s), 第%d次重试, 等待%.1fs...", func.__name__, attempt + 1, wait)
                    await asyncio.sleep(wait)
                except httpx.ConnectError as e:
                    last_err = e
                    wait = delay * (backoff ** attempt)
                    logger.warning("连接错误(%s), 第%d次重试, 等待%.1fs...", func.__name__, attempt + 1, wait)
                    await asyncio.sleep(wait)
            raise last_err
        return wrapper
    return decorator


class FeishuService:
    """飞书API统一服务"""

    def __init__(self):
        self.app_id = FEISHU_APP_ID
        self.app_secret = FEISHU_APP_SECRET
        self.base_url = FEISHU_BASE_URL
        self.tenant_access_token = None
        self.client = httpx.AsyncClient(timeout=30.0)

    # ==================== 认证模块 ====================

    @api_retry(max_retries=3)
    async def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {"app_id": self.app_id, "app_secret": self.app_secret}
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            self.tenant_access_token = result["tenant_access_token"]
            return self.tenant_access_token
        else:
            raise Exception(f"获取token失败: {result.get('msg')}")

    async def _get_headers(self, with_content_type: bool = True) -> dict:
        """获取请求头（包含token）"""
        if not self.tenant_access_token:
            await self.get_tenant_access_token()
        headers = {"Authorization": f"Bearer {self.tenant_access_token}"}
        if with_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    # ==================== Wiki模块 ====================

    async def list_wiki_spaces(self) -> List[dict]:
        url = f"{self.base_url}/wiki/v2/spaces"
        headers = await self._get_headers()
        response = await self.client.get(url, headers=headers)
        result = response.json()
        if result.get("code") == 0:
            return result["data"].get("items", [])
        else:
            raise Exception(f"获取知识空间列表失败: {result.get('msg')}")

    async def create_wiki_space(self, name: str) -> Dict:
        url = f"{self.base_url}/wiki/v2/spaces"
        headers = await self._get_headers()
        data = {"name": name}
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"创建知识库失败: {result.get('msg')}")

    @api_retry(max_retries=3)
    async def create_wiki_node(self, space_id: str, title: str, obj_type: str = "docx", parent_node_token: Optional[str] = None) -> Dict:
        url = f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes"
        headers = await self._get_headers()
        data = {"obj_type": obj_type, "node_type": "origin", "node_title": title}
        if parent_node_token:
            data["parent_node_token"] = parent_node_token
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            return result
        else:
            raise Exception(f"创建节点失败 [{title}]: {result.get('msg')}")

    @api_retry(max_retries=3)
    async def move_doc_to_wiki(self, space_id: str, obj_token: str, obj_type: str = "docx", parent_node_token: Optional[str] = None) -> Dict:
        url = f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes/move_docs_to_wiki"
        headers = await self._get_headers()
        data = {"obj_token": obj_token, "obj_type": obj_type}
        if parent_node_token:
            data["parent_node_token"] = parent_node_token
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"添加文档到知识库失败: {result.get('msg')}")

    # ==================== Docx模块 ====================

    async def create_document(self, title: str, folder_token: Optional[str] = None) -> Dict:
        url = f"{self.base_url}/docx/v1/documents"
        headers = await self._get_headers()
        data = {"title": title}
        if folder_token:
            data["folder_token"] = folder_token
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]["document"]
        else:
            raise Exception(f"创建文档失败: {result.get('msg')}")

    async def create_blocks(self, document_id: str, blocks: List[dict], parent_block_id: Optional[str] = None, index: Optional[int] = None) -> Dict:
        block_id = parent_block_id or document_id
        url = f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{block_id}/children"
        headers = await self._get_headers()
        payload = {"children": blocks, "index": index}
        max_retries = 3
        for attempt in range(max_retries):
            response = await self.client.post(url, headers=headers, json=payload)
            result = response.json()
            if result.get("code") == 0:
                return result["data"]
            elif result.get("code") == 99991400:
                wait_time = 2 ** attempt
                print(f"  ⚠️ 频率限制，等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
                continue
            else:
                raise Exception(f"创建块失败: {result.get('msg')}")
        raise Exception("创建块失败: 超过最大重试次数")

    @staticmethod
    def create_heading_block(content: str, level: int = 1) -> dict:
        block_type = level + 2
        heading_key = f"heading{level}"
        return {"block_type": block_type, heading_key: {"elements": [{"text_run": {"content": content}}]}}

    @staticmethod
    def create_text_block(content: str, bold: bool = False, italic: bool = False) -> dict:
        return {"block_type": 2, "text": {"elements": [{"text_run": {"content": content, "text_element_style": {"bold": bold, "italic": italic}}}]}}

    @staticmethod
    def create_link_block(text: str, url: str) -> dict:
        import urllib.parse
        encoded_url = urllib.parse.quote(url, safe='')
        return {"block_type": 2, "text": {"elements": [{"text_run": {"content": text, "text_element_style": {"link": {"url": encoded_url}}}}]}}

    @staticmethod
    def create_bullet_list_block(items: List[str]) -> List[dict]:
        return [{"block_type": 12, "bullet": {"elements": [{"text_run": {"content": item}}]}} for item in items]

    @staticmethod
    def create_divider_block() -> dict:
        return {"block_type": 22, "divider": {}}

    # ==================== Bitable模块 ====================

    async def create_bitable(self, name: str, folder_token: Optional[str] = None) -> Dict:
        url = f"{self.base_url}/bitable/v1/apps"
        headers = await self._get_headers()
        data = {"name": name}
        if folder_token:
            data["folder_token"] = folder_token
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"创建多维表格失败: {result.get('msg')}")

    async def create_bitable_field(self, app_token: str, table_id: str, field_name: str, field_type: int = 1) -> Dict:
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = await self._get_headers()
        data = {"field_name": field_name, "type": field_type}
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"创建字段失败: {result.get('msg')}")

    async def add_bitable_record(self, app_token: str, table_id: str, fields: Dict) -> Dict:
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = await self._get_headers()
        response = await self.client.post(url, headers=headers, json={"fields": fields})
        result = response.json()
        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"添加记录失败: {result.get('msg')}")

    async def list_bitable_records(self, app_token: str, table_id: str, page_size: int = 100) -> List[dict]:
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = await self._get_headers()
        params = {"page_size": page_size}
        response = await self.client.get(url, headers=headers, params=params)
        result = response.json()
        if result.get("code") == 0:
            return result["data"].get("items", [])
        else:
            raise Exception(f"获取记录失败: {result.get('msg')}")

    async def update_bitable_record(self, app_token: str, table_id: str, record_id: str, fields: Dict) -> Dict:
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        headers = await self._get_headers()
        response = await self.client.put(url, headers=headers, json={"fields": fields})
        result = response.json()
        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"更新记录失败: {result.get('msg')}")

    async def list_bitable_fields(self, app_token: str, table_id: str) -> List[dict]:
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = await self._get_headers()
        response = await self.client.get(url, headers=headers)
        result = response.json()
        if result.get("code") == 0:
            return result["data"].get("items", [])
        else:
            raise Exception(f"获取字段列表失败: {result.get('msg')}")

    async def delete_bitable_field(self, app_token: str, table_id: str, field_id: str) -> Dict:
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}"
        headers = await self._get_headers()
        response = await self.client.delete(url, headers=headers)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"删除字段失败: {result.get('msg')}")

    async def delete_bitable_record(self, app_token: str, table_id: str, record_id: str) -> Dict:
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        headers = await self._get_headers()
        response = await self.client.delete(url, headers=headers)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]
        else:
            raise Exception(f"删除记录失败: {result.get('msg')}")

    # ==================== Drive模块 ====================

    async def create_folder(self, name: str, parent_token: Optional[str] = None) -> Dict:
        url = f"{self.base_url}/drive/v1/folders"
        headers = await self._get_headers()
        data = {"name": name}
        if parent_token:
            data["parent_token"] = parent_token
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]["folder"]
        else:
            raise Exception(f"创建文件夹失败: {result.get('msg')}")

    @api_retry(max_retries=3)
    async def upload_file(self, file_path: str, parent_type: str = "bitable_file", parent_node: Optional[str] = None) -> str:
        url = f"{self.base_url}/drive/v1/medias/upload_all"
        headers = await self._get_headers(with_content_type=False)
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f:
            files = {'file_name': (None, file_name), 'parent_type': (None, parent_type), 'parent_node': (None, parent_node), 'size': (None, str(file_size)), 'file': (file_name, f)}
            response = await self.client.post(url, headers=headers, files=files)
        result = response.json()
        if result.get("code") == 0:
            return result["data"]["file_token"]
        else:
            raise Exception(f"上传文件失败: {result.get('msg')}")

    async def close(self):
        await self.client.aclose()

    # ==================== Wiki节点查询 ====================

    async def list_wiki_nodes(self, space_id: str, parent_node_token: Optional[str] = None, page_size: int = 50) -> List[dict]:
        url = f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes"
        headers = await self._get_headers(with_content_type=False)
        params = {"page_size": page_size}
        if parent_node_token:
            params["parent_node_token"] = parent_node_token
        all_nodes = []
        while True:
            response = await self.client.get(url, headers=headers, params=params)
            result = response.json()
            if result.get("code") == 0:
                items = result["data"].get("items", [])
                all_nodes.extend(items)
                page_token = result["data"].get("page_token")
                if not page_token:
                    break
                params["page_token"] = page_token
            else:
                raise Exception(f"获取知识库节点失败: {result.get('msg')}")
        return all_nodes


async def test_feishu_service():
    print("🧪 测试飞书服务...")
    service = FeishuService()
    try:
        print("\n1. 获取 tenant_access_token...")
        token = await service.get_tenant_access_token()
        print(f"✅ Token: {token[:20]}...")
        print("\n2. 列出知识空间...")
        spaces = await service.list_wiki_spaces()
        for space in spaces:
            print(f"  - {space['name']}: {space['space_id']}")
        print("\n3. 创建测试文档...")
        doc = await service.create_document("测试文档-PPE大礼包")
        print(f"✅ 文档创建成功: {doc['document_id']}")
        print("\n4. 写入文档内容...")
        blocks = [FeishuService.create_heading_block("测试标题", level=1), FeishuService.create_text_block("这是一段测试文本。"), FeishuService.create_divider_block(), FeishuService.create_heading_block("列表测试", level=2)]
        blocks.extend(FeishuService.create_bullet_list_block(["项目1", "项目2", "项目3"]))
        await service.create_blocks(doc['document_id'], blocks)
        print(f"✅ 内容写入成功")
        print("\n✅ 飞书服务测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        await service.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_feishu_service())
