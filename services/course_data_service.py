# -*- coding: utf-8 -*-
"""
课程数据服务 — 从飞书多维表格读取课程元数据。

数据源优先级：
    1. 飞书 Bitable nav 表（运行时源真相）
    2. data/db/*.json（本地缓存快照）
    3. COURSES_BY_YEAR 种子数据（最底限回退）

符合架构规范：只调用 libs/ 层（FeishuAdapter + data_adapter），不直接依赖第三方 SDK。
"""

from typing import List, Optional

from libs.feishu import FeishuAdapter
from libs.data_adapter import read_course_db
from config.course_schema import CourseData, COURSES_BY_YEAR, WIKI_YEAR_NODES
from config.settings import Settings


class CourseDataService:
    """课程数据读取服务。"""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def get_by_year(self, year: str, app_token: Optional[str] = None) -> List[CourseData]:
        """读取某学年课程列表（含 rich data）。"""
        # 1. 尝试从 bitable 读取基础字段
        if app_token:
            courses = await self._from_bitable(year, app_token)
            if courses:
                # 用本地 rich data（insights / materials / reflections）补全
                return self._merge_rich_data(year, courses)
        # 2. 本地 JSON 回退
        local = self._from_local(year)
        if local:
            return local
        # 3. 种子数据回退
        return [CourseData(year=year, **c) for c in COURSES_BY_YEAR.get(year, [])]

    async def get_all(self, app_token: Optional[str] = None) -> List[CourseData]:
        """读取全部学年课程列表。"""
        courses: List[CourseData] = []
        for year in WIKI_YEAR_NODES:
            courses.extend(await self.get_by_year(year, app_token))
        return courses

    # ── 内部方法 ──────────────────────────────────────────────────────

    async def _from_bitable(self, year: str, app_token: str) -> List[CourseData]:
        """从飞书多维表格读取课程元数据。"""
        try:
            feishu = FeishuAdapter(self.settings)
            tables = await feishu.get_bitable_tables(app_token)
            table_id = ""
            for t in tables:
                if year in t.get("name", ""):
                    table_id = t["table_id"]
                    break
            if not table_id:
                await feishu.close()
                return []

            records = await feishu.list_bitable_records(app_token, table_id)
            await feishu.close()

            courses: List[CourseData] = []
            for r in records:
                f = r.get("fields") or {}
                name = f.get("课程名称") or f.get("课程名称", "")
                if not name:
                    continue
                # 字段值可能是 [{"text": "xxx"}]（飞书 URL 字段格式），取原始值
                if isinstance(name, list):
                    name = name[0].get("text", "") if name else ""
                courses.append(CourseData(
                    name=str(name),
                    teacher=str(f.get("授课老师") or ""),
                    semester=str(f.get("开课学期") or ""),
                    type=str(f.get("课程类型") or ""),
                    exam=str(f.get("考试形式") or ""),
                    year=year,
                ))
            return courses
        except Exception:
            return []

    @staticmethod
    def _from_local(year: str) -> List[CourseData]:
        """从 data/db/{year}.json 读取。"""
        from config.settings import settings
        records = read_course_db(settings.course_db_dir, year)
        if records:
            return [CourseData.from_dict(r) for r in records]
        return []

    @staticmethod
    def _merge_rich_data(year: str, bitable_courses: List[CourseData]) -> List[CourseData]:
        """用本地 rich data 补全 bitable 的基础字段。"""
        local_map = {c.name: c for c in CourseDataService._from_local(year)}
        for c in bitable_courses:
            if c.name in local_map:
                rich = local_map[c.name]
                c.insights = rich.insights
                c.materials = rich.materials
                c.reflections = rich.reflections
                c.contributors = rich.contributors
        return bitable_courses
