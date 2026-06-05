# -*- coding: utf-8 -*-
"""表单采集同步服务 — 从 bitable 管理表拉取已批准记录，合并到 data/db/*.json。"""

import structlog
from collections import defaultdict
from typing import Dict, Any, List

from libs.feishu import FeishuAdapter
from libs.data_adapter import read_course_db, write_course_db
from config.course_schema import (
    CourseData, Material, Insight,
    MATERIALS_TABLE_FIELDS, INSIGHTS_TABLE_FIELDS,
    WIKI_YEAR_NODES,
)

logger = structlog.get_logger()

MATERIALS_TABLE_NAME = "资料管理表"
INSIGHTS_TABLE_NAME = "心得管理表"


class SyncService:
    """将已批准的 bitable 表单记录同步到本地 data/db/*.json。"""

    def __init__(self, feishu: FeishuAdapter, db_dir: str):
        self.feishu = feishu
        self.db_dir = db_dir

    async def ensure_tables(self, app_token: str) -> Dict[str, str]:
        """确保资料/心得管理表存在且字段正确，返回 {"materials": tid, "insights": tid}。"""
        tables = await self.feishu.get_bitable_tables(app_token)
        name_to_id = {t["name"]: t["table_id"] for t in tables}

        result = {}
        for name, fields_def in [(MATERIALS_TABLE_NAME, MATERIALS_TABLE_FIELDS),
                                  (INSIGHTS_TABLE_NAME, INSIGHTS_TABLE_FIELDS)]:
            if name in name_to_id:
                tid = name_to_id[name]
            else:
                info = await self.feishu.create_bitable_table(app_token, name)
                tid = info["table_id"]

            existing = await self.feishu.list_bitable_fields(app_token, tid)
            existing_names = {f["field_name"] for f in existing}
            new_fields = [{"field_name": fn, "type": ft}
                          for fn, ft in fields_def if fn not in existing_names]
            if new_fields:
                await self.feishu.create_bitable_fields(app_token, tid, new_fields)
            result[name] = tid

        return {"materials": result[MATERIALS_TABLE_NAME],
                "insights": result[INSIGHTS_TABLE_NAME]}

    async def sync(self, app_token: str) -> Dict[str, Any]:
        """主入口：拉取已批准记录 → 按年级+课程合并到 data/db/*.json。"""
        table_ids = await self.ensure_tables(app_token)

        materials_raw = await self.feishu.list_bitable_records(app_token, table_ids["materials"])
        insights_raw = await self.feishu.list_bitable_records(app_token, table_ids["insights"])

        approved_materials = [r["fields"] for r in materials_raw
                              if r["fields"].get("审核状态") == "已通过"]
        approved_insights = [r["fields"] for r in insights_raw
                             if r["fields"].get("审核状态") == "已通过"]

        # 按 (年级, 课程名) 分组
        m_by_course = defaultdict(list)
        for m in approved_materials:
            key = (m.get("年级", ""), m.get("课程", ""))
            if key[0] and key[1]:
                m_by_course[key].append(m)

        i_by_course = defaultdict(list)
        for ins in approved_insights:
            key = (ins.get("年级", ""), ins.get("课程", ""))
            if key[0] and key[1]:
                i_by_course[key].append(ins)

        all_keys = set(m_by_course.keys()) | set(i_by_course.keys())
        updated, skipped = 0, 0

        for year in WIKI_YEAR_NODES:
            year_keys = {k for k in all_keys if k[0] == year}
            if not year_keys:
                continue
            records = read_course_db(self.db_dir, year)
            name_map = {r["name"]: r for r in records}

            for _, course_name in year_keys:
                if course_name not in name_map:
                    logger.warning("课程不在 data/db 中，跳过", year=year, course=course_name)
                    skipped += 1
                    continue
                course = name_map[course_name]

                for m in m_by_course.get((year, course_name), []):
                    material = Material(
                        name=m.get("资料名称", ""),
                        material_type=m.get("资料类型", ""),
                        contributor=m.get("贡献者", ""),
                        grade=m.get("年级", ""),
                        recommendation_reason=m.get("推荐理由", ""),
                        file_link=m.get("文件链接", ""),
                        review_status="已通过",
                    )
                    existing_names = {x.get("name") for x in course.get("materials", [])}
                    if material.name not in existing_names:
                        course.setdefault("materials", []).append(material.model_dump())

                for ins in i_by_course.get((year, course_name), []):
                    existing_contents = {x.get("content") for x in course.get("insights", [])}
                    if ins.get("心得内容", "") and ins["心得内容"] not in existing_contents:
                        course.setdefault("insights", []).append(Insight(
                            author=ins.get("作者", ""),
                            grade=ins.get("年级", ""),
                            score=ins.get("成绩", ""),
                            content=ins["心得内容"],
                        ).model_dump())

                updated += 1

            write_course_db(self.db_dir, year, records)
            logger.info("学年同步完成", year=year, courses=len(records))

        return {"updated_courses": updated, "skipped": skipped,
                "materials_found": len(approved_materials),
                "insights_found": len(approved_insights)}
