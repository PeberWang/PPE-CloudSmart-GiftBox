# -*- coding: utf-8 -*-
"""测试创建知识空间"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ppe_demo"))
from ppe_demo.services.feishu_service import FeishuService


async def test():
    feishu = FeishuService()
    
    try:
        # 获取token
        print("1. 获取token...")
        token = await feishu.get_tenant_access_token()
        print(f"   ✅ Token: {token[:20]}...")
        
        # 尝试创建知识空间
        print("\n2. 尝试创建知识空间...")
        try:
            result = await feishu.create_wiki_space("测试空间-PPE")
            print(f"   ✅ 创建成功: {result}")
        except Exception as e:
            print(f"   ❌ 创建失败: {e}")
            
            # 尝试获取更多错误信息
            import httpx
            url = f"{feishu.base_url}/wiki/v2/spaces"
            headers = await feishu._get_headers()
            print(f"\n   调试信息:")
            print(f"   - URL: {url}")
            print(f"   - Headers: {headers}")
            
            # 直接发送请求看结果
            response = await feishu.client.post(url, headers=headers, json={"name": "测试空间-PPE"})
            print(f"   - 响应状态码: {response.status_code}")
            print(f"   - 响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await feishu.close()


if __name__ == "__main__":
    asyncio.run(test())
