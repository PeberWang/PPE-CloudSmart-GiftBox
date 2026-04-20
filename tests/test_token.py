# -*- coding: utf-8 -*-
"""测试Token获取和使用"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ppe_giftbox.services.feishu_service import FeishuService


async def test():
    feishu = FeishuService()
    
    try:
        # 获取token
        print("1. 获取token...")
        token = await feishu.get_tenant_access_token()
        print(f"   Token: {token[:20]}...")
        
        # 列出知识空间
        print("\n2. 列出知识空间...")
        headers = await feishu._get_headers()
        print(f"   Headers: {headers}")
        
        spaces = await feishu.list_wiki_spaces()
        print(f"   找到 {len(spaces)} 个空间")
        for s in spaces[:3]:
            print(f"   - {s['name']}: {s['space_id']}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await feishu.close()


if __name__ == "__main__":
    asyncio.run(test())
