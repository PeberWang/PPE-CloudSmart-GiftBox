# -*- coding: utf-8 -*-
"""
编排层：子流程定义。串联 services，零业务逻辑。
"""

import asyncio
import structlog
from typing import Dict, List, Optional, Any

from libs.feishu import FeishuAdapter
from libs.llm_adapter import LLMAdapter
from libs.feishu import blocks as B
from libs.data_adapter import read_json, write_json
from libs.operation_log import log_operation
from services.wiki_service import WikiService
from services.table_service import TableService
from services.doc_service import DocService
from services.material_service import MaterialService
from services.perm_service import PermService
from services.sync_service import SyncService
from config.course_schema import get_courses_by_year, get_all_courses, WIKI_YEAR_NODES
from config.settings import Settings
from glue.rollback import RollbackManager

logger = structlog.get_logger()
_STATE_FILE = "data/deploy_state.json"


def _year_placeholder_blocks(year: str, course_count: int) -> List:
    """学年文档占位结构（WP5 将补充 LLM 总论内容）。"""
    return [
        B.heading(f"{year}学年课程学习指南", 1),
        B.text(f"本文档汇集了 {year} 各门课程的学习资料与学长学姐的高分心得，共 {course_count} 门课程。"),
        B.text("课程导航见下方表格：点击任一行，即可进入对应课程的专属学习指南。"),
        B.divider(),
        B.heading("课程导航", 2),
        B.text("（下表由部署脚本自动生成，学习指南链接将在文档生成步骤后自动填入）"),
    ]


class Pipeline:
    """部署流程集合"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.rollback_manager = RollbackManager()

    # ── 知识库构建流程（学年文档 + 内嵌 nav 表） ─────────────────────────

    @log_operation("wiki_pipeline")
    async def wiki_pipeline(self, space_id: str = None, space_name: str = None) -> Dict[str, Any]:
        logger.info("开始知识库构建流程")
        feishu = FeishuAdapter(self.settings)
        wiki = WikiService(feishu)
        table = TableService(feishu)
        app_token = self.settings.bitable_app_token

        try:
            # 1. 找/建知识空间
            if not space_id:
                sn = space_name or self.settings.wiki_space_name
                existing = await wiki.get_space_by_name(sn)
                if existing["space_id"]:
                    space_id = existing["space_id"]
                else:
                    result = await wiki.create_space(sn)
                    space_id = result["space_id"]
                    self.rollback_manager.record_wiki_space(space_id, sn)

            # 2. 学年节点 → 内容 → nav 表 → 嵌套 bitable
            year_data: Dict[str, Any] = {}
            for year in WIKI_YEAR_NODES:
                courses = get_courses_by_year(year)
                if not courses:
                    continue

                node = await wiki.build_year_nodes(space_id, [year])
                node_info = node[year]
                obj_token = node_info["obj_token"]
                year_data[year] = {**node_info, "table_id": ""}
                self.rollback_manager.record_wiki_node(node_info["node_id"], year, space_id)

                # 占位块写入学年文档
                if obj_token:
                    placeholder = _year_placeholder_blocks(year, len(courses))
                    next_idx = await feishu.append_blocks(obj_token, placeholder, index=0)

                # 建 nav 表 + 填课程行
                if app_token and obj_token:
                    tbl_result = await table.populate_year_courses(app_token, year, courses)
                    table_id = tbl_result["table_id"]
                    year_data[year]["table_id"] = table_id
                    # 在学年 wiki 节点下挂载 bitable 子节点（侧栏可见）
                    await wiki.attach_bitable_to_year(
                        space_id, node_info["node_id"], year, app_token, table_id
                    )
                    logger.info("多维表格挂载完成", year=year, table_id=table_id)

            # 3. 保存部署状态（供 doc 步骤使用）
            state = {"space_id": space_id, "app_token": app_token or "", "year_nodes": year_data}
            write_json(_STATE_FILE, state)

            await feishu.close()
            logger.info("知识库构建完成", space_id=space_id, years=len(year_data))
            return {"space_id": space_id, "year_nodes": year_data}

        except Exception as e:
            logger.error("知识库构建失败", error=str(e))
            await feishu.close()
            raise

    # ── 多维表格独立流程（--mode tables）───────────────────────────────────

    @log_operation("table_pipeline")
    async def table_pipeline(self, app_token: str, year: str, courses: list) -> Dict[str, Any]:
        logger.info("开始多维表格构建流程", year=year)
        feishu = FeishuAdapter(self.settings)
        table = TableService(feishu)
        wiki = WikiService(feishu)
        if not app_token:
            await feishu.close()
            return {"status": "skipped", "reason": "未配置 App Token"}
        result = await table.populate_year_courses(app_token, year, courses)

        # 挂载 bitable 到 wiki 学年节点（从 deploy_state 读取 space_id 和 node_id）
        state = read_json(_STATE_FILE) or {}
        space_id = state.get("space_id")
        year_node = (state.get("year_nodes") or {}).get(year, {})
        year_node_id = year_node.get("node_id")
        table_id = result.get("table_id")
        if space_id and year_node_id and table_id:
            try:
                await wiki.attach_bitable_to_year(space_id, year_node_id, year, app_token, table_id)
                logger.info("多维表格已挂载到 Wiki 节点", year=year, table_id=table_id)
            except Exception as e:
                logger.warning("多维表格挂载失败", year=year, error=str(e))

        await feishu.close()
        return {"year": year, "result": result}

    # ── 课程文档生成流程（WP5 实现）─────────────────────────────────────────

    @log_operation("doc_pipeline")
    async def doc_pipeline(self, space_id: str = None, courses: list = None, limit: int = None) -> Dict[str, Any]:
        logger.info("开始文档生成流程", limit=limit)
        feishu = FeishuAdapter(self.settings)
        llm = LLMAdapter(self.settings)
        doc = DocService(feishu, llm)
        state = read_json(_STATE_FILE) or {}
        all_courses = courses or get_all_courses()
        try:
            result = await doc.generate_all_course_guides(
                space_id=state.get("space_id") or space_id,
                courses=all_courses, limit=limit
            )
            course_to_doc_map = {item["course_name"]: item["url"] for item in result.get("results", []) if item.get("url")}

            # 追加学年总论（仅全量运行；limit != None 视为测试模式，跳过）
            if not limit:
                for year, node_info in (state.get("year_nodes") or {}).items():
                    obj_token = node_info.get("obj_token") if node_info else None
                    if obj_token:
                        try:
                            await doc.append_year_overview(obj_token, year, get_courses_by_year(year))
                        except Exception as e:
                            logger.warning("学年总论追加失败，跳过", year=year, error=str(e))

            await feishu.close(); await llm.close()
            return {"result": result, "course_to_doc_map": course_to_doc_map}
        except Exception as e:
            logger.error("文档生成失败", error=str(e))
            await feishu.close(); await llm.close()
            raise

    # ── 资料上传流程 ─────────────────────────────────────────────────────────

    @log_operation("material_pipeline")
    async def material_pipeline(self, app_token: str = None) -> Dict[str, Any]:
        import os
        config_path = "data/materials.json"
        if not os.path.exists(config_path):
            return {"status": "skipped", "reason": "data/materials.json 不存在"}
        feishu = FeishuAdapter(self.settings)
        material = MaterialService(feishu)
        try:
            result = await material.upload_materials_from_config(config_path)
            if app_token and result.get("total_success", 0) > 0:
                result["link_result"] = await material.link_materials_to_tables(app_token)
            return result
        finally:
            await feishu.close()

    # ── 权限配置流程 ─────────────────────────────────────────────────────────

    async def perm_pipeline(self, space_id: str, app_token: str, table_id: str = "") -> Dict[str, Any]:
        feishu = FeishuAdapter(self.settings)
        perm = PermService(feishu)
        try:
            result = await perm.set_default_permissions(space_id, app_token, table_id)
            return {"status": "completed", "result": result}
        finally:
            await feishu.close()

    # ── 文档链接回填流程 ─────────────────────────────────────────────────────

    @log_operation("link_pipeline")
    async def link_pipeline(self, app_token: str, course_to_doc_map: Dict[str, str]) -> Dict[str, Any]:
        if not course_to_doc_map:
            return {"status": "skipped", "reason": "未提供文档映射"}
        feishu = FeishuAdapter(self.settings)
        table = TableService(feishu)
        results, errors = [], []
        try:
            for year in WIKI_YEAR_NODES:
                try:
                    table_id = await table._resolve_table_id(app_token, year)
                    table.table_map[year] = table_id
                except Exception:
                    continue
                for course in get_courses_by_year(year):
                    doc_url = course_to_doc_map.get(course.name)
                    if not doc_url:
                        continue
                    try:
                        r = await table.backfill_doc_url(app_token, year, course.name, doc_url)
                        results.append({"year": year, "course": course.name, **r})
                    except Exception as e:
                        errors.append({"year": year, "course": course.name, "error": str(e)})
        finally:
            await feishu.close()
        return {"success_count": len(results), "error_count": len(errors), "results": results, "errors": errors}

    # ── 表单同步流程 ─────────────────────────────────────────────────────────

    @log_operation("sync_form_pipeline")
    async def sync_form_pipeline(self, app_token: str) -> Dict[str, Any]:
        """从 bitable 管理表拉取已批准记录，合并到 data/db/*.json。"""
        logger.info("开始表单数据同步")
        feishu = FeishuAdapter(self.settings)
        try:
            svc = SyncService(feishu, self.settings.course_db_dir)
            return await svc.sync(app_token)
        finally:
            await feishu.close()
