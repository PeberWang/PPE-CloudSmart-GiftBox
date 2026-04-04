# -*- coding: utf-8 -*-
"""通过节点token查询知识空间ID"""
import sys, os, asyncio
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
        h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # 获取节点信息
        node_token = 'VnFwwapbOiRZSQkzQyZcpnGdnmf'
        r2 = await s.get(f'https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={node_token}', headers=h)
        d2 = await r2.json()
        print(f"code={d2.get('code')}, msg={d2.get('msg')}")
        if d2.get('code') == 0:
            node = d2['data']['node']
            print(f"space_id: {node.get('space_id')}")
            print(f"node_token: {node.get('node_token')}")
            print(f"obj_token: {node.get('obj_token')}")
            print(f"title: {node.get('title')}")
            print(f"parent_node_token: {node.get('parent_node_token')}")
        else:
            print(f"完整响应: {d2}")

        # 同时列出所有知识空间
        print("\n--- 所有知识空间 ---")
        r3 = await s.get('https://open.feishu.cn/open-apis/wiki/v2/spaces', headers=h)
        d3 = await r3.json()
        if d3.get('code') == 0:
            for item in d3.get('data', {}).get('items', []):
                space = item.get('space', item)
                print(f"  name={space.get('name')}, space_id={space.get('space_id')}, type={space.get('space_type')}")
        else:
            print(f"列出空间失败: {d3.get('code')}")

asyncio.run(test())
