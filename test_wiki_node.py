# -*- coding: utf-8 -*-
"""测试在已有知识空间下创建节点（带node_type）"""
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
        h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        space_id = '7624453064019168209'

        # 尝试不同的node_type
        for node_type in ['origin', 'custom']:
            print(f"\n尝试 node_type={node_type}...")
            r2 = await s.post(
                f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes',
                headers=h,
                json={
                    'obj_type': 'docx',
                    'title': f'测试节点-{node_type}-请删除',
                    'node_type': node_type
                }
            )
            d2 = await r2.json()
            print(f"  code={d2.get('code')}, msg={d2.get('msg')}")

            if d2.get('code') == 0:
                node = d2['data']['node']
                print(f"  ✅ 成功！node_token={node['node_token']}")
                break
            else:
                print(f"  ❌ {json.dumps(d2.get('error', {}), ensure_ascii=False)}")

asyncio.run(test())
