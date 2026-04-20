# -*- coding: utf-8 -*-
"""测试多维表格创建和记录填充"""
import sys, os, asyncio
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ppe_demo'))

from ppe_giftbox.services.core.feishu_service import FeishuService
from ppe_giftbox.services.bitable.table_service import TableService

async def test():
    print('初始化飞书服务...')
    feishu = FeishuService()
    table_svc = TableService(feishu)

    print('创建大一课程多维表格...')
    result = await table_svc._create_year_table('大一')
    print(f'app_token: {result["app_token"]}')
    print(f'table_id: {result["table_id"]}')
    print(f'URL: {result["url"]}')

    print('添加测试课程记录...')
    await table_svc._add_course_record(
        result['app_token'], result['table_id'],
        {'name': '测试课程-请删除', 'teacher': '测试老师', 'semester': '大一上', 'type': '必修', 'exam': '闭卷'},
        ''
    )
    print('✅ 多维表格创建+记录填充成功！')

    await feishu.close()

asyncio.run(test())
