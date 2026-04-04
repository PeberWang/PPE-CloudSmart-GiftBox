# -*- coding: utf-8 -*-
"""强制刷新token并测试wiki权限"""
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    async with aiohttp.ClientSession() as session:
        # 强制刷新：先获取token
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        resp = await session.post(url, json={
            'app_id': os.getenv('FEISHU_APP_ID'),
            'app_secret': os.getenv('FEISHU_APP_SECRET')
        })
        data = await resp.json()
        token = data.get('tenant_access_token', '')
        print(f"Token: {token[:20]}... expire={data.get('expire')}s")

        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # 测试wiki空间列表（只读，不需要创建权限也能测）
        resp = await session.get(
            'https://open.feishu.cn/open-apis/wiki/v2/spaces',
            headers=headers
        )
        data = await resp.json()
        print(f"\n列出知识空间: code={data.get('code')}, msg={data.get('msg')}")
        if data.get('code') == 0:
            items = data.get('data', {}).get('items', [])
            print(f"已有空间数: {len(items)}")

        # 测试创建知识空间
        print("\n创建测试知识空间...")
        resp = await session.post(
            'https://open.feishu.cn/open-apis/wiki/v2/spaces',
            headers=headers, json={'name': 'test_space_auto_delete'}
        )
        data = await resp.json()
        code = data.get('code')
        print(f"结果: code={code}, msg={data.get('msg')}")

        if code == 0:
            space_id = data['data']['space']['space_id']
            print(f"✅ wiki:wiki 权限已生效！space_id={space_id}")
            # 删除测试空间
            await session.delete(
                f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}',
                headers=headers
            )
            print("测试空间已清理")
        else:
            print(f"❌ 权限未生效 (code={code})")
            # 尝试用api/v4的auth看看能不能invalidate
            print("\n尝试通过api/v4/auth刷新...")
            resp2 = await session.post(
                'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal',
                json={
                    'app_id': os.getenv('FEISHU_APP_ID'),
                    'app_secret': os.getenv('FEISHU_APP_SECRET')
                }
            )
            data2 = await resp2.json()
            print(f"app_access_token: code={data2.get('code')}")

asyncio.run(test())
