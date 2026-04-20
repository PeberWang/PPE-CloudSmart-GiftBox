# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 部署编排服务
管理完整部署流程和各模式部署逻辑
"""

from ppe_giftbox.services.core.feishu_service import FeishuService
from ppe_giftbox.services.wiki.wiki_builder import WikiBuilder
from ppe_giftbox.services.bitable.table_service import TableService
from ppe_giftbox.services.docs.doc_generator import DocGenerator
from ppe_giftbox.services.docs.link_service import LinkService
from ppe_giftbox.services.core.llm_service import LLMService


async def deploy_wiki(feishu: FeishuService) -> dict:
    """部署知识库结构"""
    print("\n" + "=" * 60)
    print("   📚 步骤1: 构建知识库结构")
    print("=" * 60)
    wiki = WikiBuilder(feishu)
    result = await wiki.build_all()
    return result


async def deploy_tables(feishu: FeishuService, wiki: WikiBuilder = None, incremental: bool = True) -> dict:
    """部署多维表格"""
    mode_str = "增量更新" if incremental else "全量覆盖"
    print(f"\n{'=' * 60}")
    print(f"   📊 步骤2: 创建多维表格（{mode_str}）")
    print("=" * 60)
    table_svc = TableService(feishu)
    space_id = wiki.space_id if wiki else None
    year_node_map = wiki.year_node_map if wiki else None
    result = await table_svc.create_all_tables(space_id=space_id, year_node_map=year_node_map)

    print(f"\n{'=' * 60}")
    print(f"   📝 步骤3: 填充课程记录（{mode_str}）")
    print("=" * 60)
    await table_svc.populate_all_tables(wiki_builder=wiki, incremental=incremental)
    return result


async def deploy_docs(feishu: FeishuService, wiki: WikiBuilder, limit: int = 1) -> int:
    """部署云文档"""
    print("\n" + "=" * 60)
    print("   📄 步骤4: 生成并上传课程文档")
    print("=" * 60)
    llm = LLMService()
    doc_gen = DocGenerator(feishu, llm)
    success_count = await doc_gen.generate_all_course_docs(limit=limit, wiki_builder=wiki)
    await llm.close()
    return success_count


async def deploy_upload(feishu: FeishuService) -> dict:
    """上传资料到飞书云空间"""
    print("\n" + "=" * 60)
    print("   📎 步骤5: 上传资料到飞书")
    print("=" * 60)
    print("⚠️ 当前 materials.json 为空，跳过资料上传")
    print("   如需上传真实资料，请先填充 materials.json")
    return {}


async def deploy_link(feishu: FeishuService, wiki: WikiBuilder) -> int:
    """关联表格与文档"""
    print("\n" + "=" * 60)
    print("   🔗 步骤6: 关联表格与文档")
    print("=" * 60)
    link_svc = LinkService(feishu, wiki)
    success_count = await link_svc.link_all_courses()
    return success_count


async def deploy_sync():
    """增量同步课程记录（不覆盖用户手动修改的字段）"""
    print("=" * 60)
    print("   🔄 PPE云端智能大礼包 - 增量同步")
    print("=" * 60)
    feishu = FeishuService()
    try:
        wiki = WikiBuilder(feishu)
        wiki_loaded = wiki.load_from_local()
        table_svc = TableService(feishu)
        await table_svc.populate_all_tables(
            wiki_builder=wiki if wiki_loaded else None,
            incremental=True
        )
    finally:
        await feishu.close()


async def deploy_full():
    """完整部署流程"""
    print("=" * 60)
    print("   🚀 PPE云端智能大礼包 - 完整部署")
    print("=" * 60)
    feishu = FeishuService()
    try:
        wiki_result = await deploy_wiki(feishu)
        wiki = WikiBuilder(feishu)
        wiki.space_id = wiki_result["space_id"]
        wiki.year_node_map = wiki_result["year_nodes"]
        await deploy_tables(feishu, wiki)
        await deploy_docs(feishu, wiki, limit=None)
        await deploy_upload(feishu)
        await deploy_link(feishu, wiki)
        print("\n" + "=" * 60)
        print("   ✅ 完整部署完成！")
        print("=" * 60)
        print("\n📋 部署结果:")
        print(f"  - 知识空间ID: {wiki.space_id}")
        print(f"  - 学年节点: {len(wiki.year_node_map)}")
        print(f"\n🌐 访问链接:")
        print(f"  - 知识库: https://nkuyouth.feishu.cn/wiki/space/{wiki.space_id}")
    except Exception as e:
        print(f"\n❌ 部署失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await feishu.close()


async def deploy_mode(mode: str):
    """按模式部署"""
    feishu = FeishuService()
    try:
        if mode == "wiki":
            await deploy_wiki(feishu)
        elif mode == "tables":
            await deploy_tables(feishu)
        elif mode == "docs":
            wiki = WikiBuilder(feishu)
            if not wiki.load_from_local():
                print("❌ 请先运行 --mode wiki 创建知识库结构")
                return
            await deploy_docs(feishu, wiki, limit=1)
        elif mode == "upload":
            await deploy_upload(feishu)
        elif mode == "link":
            wiki = WikiBuilder(feishu)
            if not wiki.load_from_local():
                print("❌ 请先运行 --mode wiki 创建知识库结构")
                return
            await deploy_link(feishu, wiki)
        elif mode == "full":
            await deploy_full()
        elif mode == "cleanup":
            from ppe_giftbox.services.cleanup.cleanup_service import deploy_cleanup
            await deploy_cleanup()
        elif mode == "sync":
            await deploy_sync()
    finally:
        await feishu.close()
