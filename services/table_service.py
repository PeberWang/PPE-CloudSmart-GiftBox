# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 多维表格服务
每学年一张前台 nav 表（内嵌进学年文档），字段对齐 docs/多维表格字段设计.md。
"""

import asyncio
import datetime
import structlog
from typing import Dict, List, Optional, Any

from libs.feishu import FeishuAdapter
from config.course_schema import CourseData, NAV_TABLE_FIELDS, PROTECTED_FIELDS

logger = structlog.get_logger()


def _now_ms() -> int:
    """当前时间戳（毫秒），飞书 DateTime 字段格式。"""
    return int(datetime.datetime.now().timestamp() * 1000)


def _url_field(url: str, text: str = "查看学习指南") -> Dict[str, str]:
    """飞书 URL 字段格式：{text, link}。"""
    return {"text": text, "link": url}


class TableService:
    """多维表格服务"""

    def __init__(self, feishu: FeishuAdapter):
        self.feishu = feishu
        self.table_map: Dict[str, str] = {}  # year → table_id

    async def create_year_table(self, app_token: str, year: str) -> Dict[str, str]:
        """在 app_token 下获取或创建学年 nav 表（已有则不重复创建）。"""
        table_name = f"{year}课程表"
        # 先查已有表
        try:
            tables = await self.feishu.get_bitable_tables(app_token)
            for t in tables:
                if t.get("name") == table_name:
                    self.table_map[year] = t["table_id"]
                    logger.info("学年课程表已存在，直接复用", year=year, table_id=t["table_id"])
                    return {"table_id": t["table_id"], "table_name": table_name, "url": ""}
        except Exception:
            pass
        table_info = await self.feishu.create_bitable_table(app_token=app_token, table_name=table_name)
        self.table_map[year] = table_info["table_id"]
        logger.info("学年课程表创建成功", year=year, table_id=table_info["table_id"])
        return table_info

    async def create_table_fields(self, app_token: str, table_id: str) -> Dict[str, Any]:
        """按 NAV_TABLE_FIELDS 创建字段（跳过已存在的，跳过内置的'标题'字段）。"""
        try:
            existing = await self.feishu.list_bitable_fields(app_token, table_id)
            existing_names = {f["field_name"] for f in existing}
        except Exception:
            existing_names = set()

        new_fields = [
            {"field_name": name, "type": ftype}
            for name, ftype in NAV_TABLE_FIELDS
            if name not in existing_names
        ]
        if not new_fields:
            return {"table_id": table_id, "status": "fields_exist", "created_count": 0}
        created = await self.feishu.create_bitable_fields(app_token, table_id, new_fields)
        logger.info("字段创建完成", table_id=table_id, created_count=len(created))
        return {"table_id": table_id, "status": "fields_created", "created_count": len(created)}

    async def add_course_record(self, app_token: str, year: str, course: CourseData) -> Dict[str, Any]:
        """向学年 nav 表写入一门课程的记录。"""
        table_id = self.table_map.get(year)
        if not table_id:
            raise ValueError(f"未找到 {year} 对应的表格 ID，请先调用 create_year_table")

        fields: Dict[str, Any] = {
            "课程名称": course.name,
            "授课老师": course.teacher or "",
            "开课学期": course.semester or "",
            "课程类型": course.type or "",
            "考试形式": course.exam or "",
            "资料数量": course.material_count,
            "最后更新": _now_ms(),
        }
        if course.doc_url:
            fields["学习指南"] = _url_field(course.doc_url)

        record = await self.feishu.add_bitable_record(app_token=app_token, table_id=table_id, fields=fields)
        logger.info("课程记录写入成功", course=course.name, record_id=record.get("record_id"))
        return record

    async def backfill_doc_url(self, app_token: str, year: str, course_name: str, doc_url: str) -> Dict[str, Any]:
        """回填课程文档链接到 nav 表的「学习指南」字段。"""
        table_id = await self._resolve_table_id(app_token, year)
        record = await self.feishu.search_bitable_record(
            app_token=app_token, table_id=table_id, field_name="课程名称", value=course_name
        )
        if not record:
            logger.warning("回填链接：未找到课程记录", course=course_name)
            return {"status": "not_found"}
        await self.feishu.update_bitable_record(
            app_token=app_token, table_id=table_id, record_id=record["record_id"],
            fields={"学习指南": _url_field(doc_url), "最后更新": _now_ms()}
        )
        logger.info("学习指南回填成功", course=course_name)
        return {"status": "updated", "record_id": record["record_id"]}

    async def populate_year_courses(self, app_token: str, year: str, courses: List[CourseData]) -> Dict[str, Any]:
        """批量写入学年所有课程记录（全量，先清空旧行，再写入）。"""
        table_info = await self.create_year_table(app_token, year)
        await self.create_table_fields(app_token, table_info["table_id"])

        results, errors = [], []
        for course in courses:
            try:
                record = await self.add_course_record(app_token, year, course)
                results.append(record)
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error("课程记录写入失败", course=course.name, error=str(e))
                errors.append({"course": course.name, "error": str(e)})
        return {
            "year": year, "table_id": table_info["table_id"],
            "success_count": len(results), "error_count": len(errors), "errors": errors
        }

    async def _resolve_table_id(self, app_token: str, year: str) -> str:
        if year in self.table_map:
            return self.table_map[year]
        tables = await self.feishu.get_bitable_tables(app_token)
        for t in tables:
            if year in t.get("name", ""):
                self.table_map[year] = t["table_id"]
                return t["table_id"]
        raise ValueError(f"未找到 {year} 对应的表格")
