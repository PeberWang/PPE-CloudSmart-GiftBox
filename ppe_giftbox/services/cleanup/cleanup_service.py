# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 清理服务
负责清理部署残留：空记录、冗余字段、空节点
"""

import json

from ppe_giftbox.services.core.feishu_service import FeishuService
from ppe_giftbox.services.wiki.wiki_builder import WikiBuilder
from ppe_giftbox.config import DEPLOY_OUTPUT_DIR
from ppe_giftbox.data.course_schema import BITABLE_COURSE_FIELDS


async def deploy_cleanup():
    """清理部署残留"""
    print("=" * 60)
    print("   🧹 PPE云端智能大礼包 - 清理模式")
    print("=" * 60)

    feishu = FeishuService()

    try:
        # 1. 清理多维表格空记录
        print("\n📋 清理多维表格空记录...")
        try:
            config_path = DEPLOY_OUTPUT_DIR / "bitable_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                tables = json.load(f)

            for year, table_info in tables.items():
                app_token = table_info.get("app_token")
                table_id = table_info.get("table_id")
                if not app_token or not table_id:
                    continue

                records = await feishu.list_bitable_records(app_token, table_id, page_size=500)
                deleted = 0
                for record in records:
                    fields = record.get("fields", {})
                    is_empty = True
                    for value in fields.values():
                        if isinstance(value, list):
                            if len(value) > 0 and value != [None]:
                                is_empty = False
                                break
                        elif value and value != 0:
                            is_empty = False
                            break
                    if is_empty:
                        try:
                            await feishu.delete_bitable_record(app_token, table_id, record["record_id"])
                            deleted += 1
                        except Exception:
                            pass
                if deleted:
                    print(f"  ✅ [{year}] 清理了 {deleted} 条空记录")
                else:
                    print(f"  ℹ️ [{year}] 无空记录")
        except FileNotFoundError:
            print("  ⚠️ 未找到 bitable_config.json，跳过表格清理")

        # 2. 清理知识库空节点
        print("\n📂 查找知识库空节点...")
        try:
            wiki = WikiBuilder(feishu)
            if not wiki.load_from_local():
                print("  ⚠️ 未找到本地知识库配置，跳过节点清理")
            else:
                nodes = await feishu.list_wiki_nodes(wiki.space_id)
                empty_nodes = []
                for node in nodes:
                    node_name = node.get("node_token", "")
                    title = node.get("title", "Untitled document")
                    if title == "" or title == "Untitled document":
                        empty_nodes.append(node)

                if empty_nodes:
                    print(f"  ⚠️ 发现 {len(empty_nodes)} 个空/未命名节点:")
                    for n in empty_nodes:
                        print(f"    - {n.get('node_token', '?')} ({n.get('title', 'Untitled document')})")
                    print("\n  ⚠️ 飞书API暂不支持删除知识库节点，请手动在客户端清理：")
                    print(f"     https://nkuyouth.feishu.cn/wiki/space/{wiki.space_id}")
                else:
                    print("  ✅ 无空/未命名节点")
        except Exception as e:
            print(f"  ⚠️ 查找节点失败: {e}")

        # 3. 清理默认冗余字段
        print("\n🔧 清理多维表格默认冗余字段...")
        try:
            config_path = DEPLOY_OUTPUT_DIR / "bitable_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                tables = json.load(f)

            custom_names = {f[0] for f in BITABLE_COURSE_FIELDS}

            for year, table_info in tables.items():
                app_token = table_info.get("app_token")
                table_id = table_info.get("table_id")
                if not app_token or not table_id:
                    continue

                fields = await feishu.list_bitable_fields(app_token, table_id)
                deleted = 0
                for field in fields:
                    fname = field.get("field_name", "")
                    if fname not in custom_names:
                        try:
                            await feishu.delete_bitable_field(app_token, table_id, field["field_id"])
                            deleted += 1
                        except Exception:
                            pass
                if deleted:
                    print(f"  ✅ [{year}] 清理了 {deleted} 个默认字段")
                else:
                    print(f"  ℹ️ [{year}] 无冗余字段")
        except FileNotFoundError:
            print("  ⚠️ 未找到 bitable_config.json，跳过字段清理")
        except Exception as e:
            print(f"  ⚠️ 字段清理失败: {e}")

        print("\n" + "=" * 60)
        print("   ✅ 清理完成！")
        print("=" * 60)

    finally:
        await feishu.close()
