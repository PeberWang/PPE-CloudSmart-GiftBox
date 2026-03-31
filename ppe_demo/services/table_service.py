# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 多维表格管理服务
负责创建学年多维表格、设置字段、添加课程记录
"""

import sys
import os
import json
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.feishu_service import FeishuService
from config import (
    WIKI_YEAR_NODES,
    COURSES_BY_YEAR,
    BITABLE_COURSE_FIELDS,
)


class TableService:
    """多维表格管理服务

    功能：
    - 为每个学年创建一个多维表格
    - 设置标准字段结构（课程名称、授课老师等）
    - 批量添加课程记录
    - 更新学习指南链接
    """

    def __init__(self, feishu: FeishuService):
        """初始化

        Args:
            feishu: FeishuService 实例
        """
        self.feishu = feishu
        # {学年: {"app_token": ..., "table_id": ...}}
        self.tables: Dict[str, dict] = {}

    async def create_all_tables(self) -> Dict[str, dict]:
        """为所有学年创建多维表格

        Returns:
            {学年: {"app_token": ..., "table_id": ..., "url": ...}}
        """
        print("📊 开始创建学年多维表格...")

        for year in WIKI_YEAR_NODES:
            try:
                result = await self._create_year_table(year)
                print(f"  ✅ [{year}] 创建成功: {result['url']}")
            except Exception as e:
                print(f"  ❌ [{year}] 创建失败: {e}")

        # 保存配置
        config_path = os.path.join(os.path.dirname(__file__), "..", "bitable_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.tables, f, ensure_ascii=False, indent=2)
        print(f"  💾 配置已保存: {config_path}")

        return self.tables

    async def populate_all_tables(self, wiki_builder=None) -> None:
        """向所有学年表格添加课程记录

        Args:
            wiki_builder: WikiBuilder 实例（可选，用于自动关联文档链接）
        """
        print("\n📝 开始填充课程记录...")

        for year, courses in COURSES_BY_YEAR.items():
            if year not in self.tables:
                print(f"  ⚠️ [{year}] 无对应表格，跳过")
                continue

            table_info = self.tables[year]
            print(f"\n  📋 [{year}]（{len(courses)}门课）:")

            for course in courses:
                try:
                    # 构建学习指南链接
                    guide_url = ""
                    if wiki_builder:
                        guide_url = wiki_builder.get_doc_url(year, course["name"]) or ""

                    await self._add_course_record(
                        app_token=table_info["app_token"],
                        table_id=table_info["table_id"],
                        course=course,
                        guide_url=guide_url
                    )
                    print(f"    ✅ {course['name']}")
                except Exception as e:
                    print(f"    ❌ {course['name']}: {e}")

        print("\n✅ 课程记录填充完成!")

    async def update_guide_link(
        self,
        year: str,
        course_name: str,
        guide_url: str
    ) -> bool:
        """更新某门课程的学习指南链接

        Args:
            year: 学年
            course_name: 课程名称
            guide_url: 文档链接

        Returns:
            是否成功
        """
        if year not in self.tables:
            print(f"  ⚠️ [{year}] 无对应表格")
            return False

        table_info = self.tables[year]
        try:
            # 查找记录
            records = await self._find_record_by_name(
                table_info["app_token"],
                table_info["table_id"],
                course_name
            )
            if records:
                record_id = records[0]["record_id"]
                await self.feishu.update_bitable_record(
                    app_token=table_info["app_token"],
                    table_id=table_info["table_id"],
                    record_id=record_id,
                    fields={"学习指南": guide_url}
                )
                print(f"  ✅ [{year}] {course_name} 链接已更新")
                return True
        except Exception as e:
            print(f"  ❌ 更新失败: {e}")
        return False

    # ── 内部方法 ──

    async def _create_year_table(self, year: str) -> dict:
        """创建单个学年的多维表格

        Args:
            year: 学年名称（如"大一"）

        Returns:
            {"app_token": ..., "table_id": ..., "url": ...}
        """
        table_name = f"PPE{year}课程表"

        # 创建多维表格
        result = await self.feishu.create_bitable(table_name)
        app_token = result["app"]["app_token"]
        table_id = result["app"]["default_table_id"]
        url = result["app"]["url"]

        # 设置字段
        for field_name, field_type in BITABLE_COURSE_FIELDS:
            try:
                await self.feishu.create_bitable_field(
                    app_token, table_id, field_name, field_type
                )
            except Exception:
                # 字段可能已存在（默认创建的字段），跳过
                pass

        self.tables[year] = {
            "app_token": app_token,
            "table_id": table_id,
            "url": url
        }

        return self.tables[year]

    async def _add_course_record(
        self,
        app_token: str,
        table_id: str,
        course: dict,
        guide_url: str = ""
    ) -> dict:
        """向表格添加一条课程记录

        Args:
            app_token: 多维表格token
            table_id: 数据表ID
            course: 课程信息字典
            guide_url: 学习指南链接

        Returns:
            添加的记录
        """
        fields = {
            "课程名称": course["name"],
            "授课老师": course.get("teacher", ""),
            "开课学期": course.get("semester", ""),
            "课程类型": course.get("type", "必修"),
            "考试形式": course.get("exam", ""),
            "资料数量": 0,
            "贡献者": "",
        }

        if guide_url:
            fields["学习指南"] = guide_url

        return await self.feishu.add_bitable_record(
            app_token=app_token,
            table_id=table_id,
            fields=fields
        )

    async def _find_record_by_name(
        self,
        app_token: str,
        table_id: str,
        course_name: str
    ) -> list:
        """按课程名称查找记录

        Args:
            app_token: 多维表格token
            table_id: 数据表ID
            course_name: 课程名称

        Returns:
            匹配的记录列表
        """
        url = (
            f"{self.feishu.base_url}"
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        )
        headers = await self.feishu._get_headers()

        params = {
            "filter": json.dumps({
                "conditions": [
                    {
                        "field_name": "课程名称",
                        "operator": "is",
                        "value": [course_name]
                    }
                ]
            })
        }

        response = await self.feishu.client.get(url, headers=headers, params=params)
        result = response.json()

        if result.get("code") == 0:
            return result["data"]["items"]
        return []
