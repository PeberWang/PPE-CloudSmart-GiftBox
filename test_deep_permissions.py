# -*- coding: utf-8 -*-
"""深度测试wiki权限 - 尝试不同API端点"""
import sys, os, asyncio, json
sys.stdout.reconfigure(encoding='utf-8')
import aiohttp
from dotenv import load_dotenv
load_dotenv()

async def test():
    async with aiohttp.ClientSession() as s:
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        r = await s.post(url, json={'app_id': os.getenv('FEISHU_APP_ID'), 'app_secret': os.getenv('FEISHU_APP_SECRET')})
        d = await r.json()
        token = d['tenant_access_token']
        print(f"Token: {token[:20]}... expire={d.get('expire')}s")
        h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # 测试1: wiki/v2/spaces (标准端点)
        print("\n--- wiki/v2/spaces ---")
        r = await s.post('https://open.feishu.cn/open-apis/wiki/v2/spaces', headers=h, json={'name': 'test_delete_me'})
        d = await r.json()
        print(f"POST: code={d.get('code')}, msg={d.get('msg')}")
        if d.get('code') == 0:
            sid = d['data']['space']['space_id']
            await s.delete(f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{sid}', headers=h)
            print(f"已清理测试空间 {sid}")

        # 测试2: docx文档创建
        print("\n--- docx:document ---")
        r = await s.post('https://open.feishu.cn/open-apis/docx/v1/documents', headers=h, json={
            'title': 'test_doc_delete',
            'folder_token': ''
        })
        d = await r.json()
        print(f"创建文档: code={d.get('code')}, msg={d.get('msg')}")
        if d.get('code') == 0:
            doc_id = d['data']['document']['document_id']
            print(f"文档ID: {doc_id}")
            # 清理
            await s.delete(f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}', headers=h)

        # 测试3: 获取app的scope信息
        print("\n--- 应用权限检查 ---")
        r = await s.get('https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal', headers=h)
        d = await r.json()
        print(f"app_token: code={d.get('code')}")

asyncio.run(test())
