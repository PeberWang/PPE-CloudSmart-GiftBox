# -*- coding: utf-8 -*-
"""测试飞书云文档创建和块写入"""
import sys, os, asyncio
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ppe_demo'))

from services.feishu_service import FeishuService

async def test():
    print('初始化飞书服务...')
    feishu = FeishuService()

    print('创建测试文档...')
    doc = await feishu.create_document('测试文档-请删除')
    doc_id = doc['document_id']
    print(f'文档ID: {doc_id}')

    print('写入文档内容...')
    blocks = [
        FeishuService.create_heading_block('测试标题', level=1),
        FeishuService.create_text_block('这是一段测试内容。'),
        FeishuService.create_heading_block('二、子标题', level=2),
        FeishuService.create_text_block('PPE云端智能大礼包 - 文档生成测试通过。'),
        FeishuService.create_divider_block(),
    ]
    await feishu.create_blocks(doc_id, blocks)
    print('✅ 云文档创建+块写入成功！')

    await feishu.close()

asyncio.run(test())
