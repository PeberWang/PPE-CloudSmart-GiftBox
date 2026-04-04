# -*- coding: utf-8 -*-
"""重新测试：强制刷新token后创建节点"""
import sys, os, asyncio, json
sys.stdout.reconfigure(encoding='utf-8')
import aiohttp
from dotenv import load_dotenv
load_dotenv()

async def test():
    async with aiohttp.ClientSession() as s:
        # 获取新token
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        r = await s.post(url, json={'app_id': os.getenv('FEISHU_APP_ID'), 'app_secret': os.getenv('FEISHU_APP_SECRET')})
        d = await r.json()
        token = d['tenant_access_token']
        print(f"Token: {token[:20]}... expire={d.get('expire')}s")
        h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        space_id = '7624453064019168209'

        # 先查空间信息
        print("\n--- 查看空间信息 ---")
        r2 = await s.get(f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}', headers=h)
        d2 = await r2.json()
        print(f"code={d2.get('code')}, msg={d2.get('msg')}")
        if d2.get('code') == 0:
            space = d2.get('data', {}).get('space', {})
            print(f"  name={space.get('name')}")
            print(f"  space_type={space.get('space_type')}")
            print(f"  visibility={space.get('visibility')}")
        else:
            print(f"  {json.dumps(d2, ensure_ascii=False)[:300]}")

        # 查空间成员
        print("\n--- 空间成员 ---")
        r3 = await s.get(f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/members', headers=h, params={'page_size': 50})
        d3 = await r3.json()
        print(f"code={d3.get('code')}, msg={d3.get('msg')}")
        if d3.get('code') == 0:
            items = d3.get('data', {}).get('items', [])
            print(f"成员数: {len(items)}")
            for item in items:
                m = item.get('member', item)
                print(f"  name={m.get('name')}, type={m.get('member_type')}, id={m.get('member_id', m.get('open_id', ''))}")

        # 创建节点
        print("\n--- 创建测试节点 ---")
        r4 = await s.post(
            f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes',
            headers=h,
            json={'obj_type': 'docx', 'title': '测试节点-请删除', 'node_type': 'origin'}
        )
        d4 = await r4.json()
        print(f"code={d4.get('code')}, msg={d4.get('msg')}")
        if d4.get('code') == 0:
            node = d4['data']['node']
            print(f"✅ 成功! node_token={node['node_token']}")
        else:
            print(f"❌ {json.dumps(d4, ensure_ascii=False)[:300]}")

asyncio.run(test())
