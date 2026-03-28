# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 知识库构建服务
负责创建飞书知识库空间、学年节点、课程节点
"""

import sys
import os
import json
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.feishu_service import FeishuService
from config import WIKI_SPACE_NAME, WIKI_YEAR_NODES, COURSES_BY_YEAR


class WikiBuilder:
    """飞书知识库自动构建器

    功能：
    - 创建知识空间（如果不存在则复用）
    - 创建"大一/大二/大三/大四"四个学年节点
    - 在每个学年节点下为每门课创建子节点（docx类型）
    - 将课程文档关联到知识库节点
    """

    def __init__(self, feishu: FeishuService):
        """初始化

        Args:
            feishu: FeishuService 实例
        """
        self.feishu = feishu
        self.space_id: Optional[str] = None
        # 节点映射：{(学年, 课程名): node_token}
        self.node_map: Dict[tuple, str] = {}
        # 学年根节点映射：{学年: node_token}
        self.year_node_map: Dict[str, str] = {}

    async def init_space(self) -> str:
        """创建或获取知识空间

        Returns:
            space_id
        """
        if self.space_id:
            return self.space_id

        try:
            result = await self.feishu.create_wiki_space(WIKI_SPACE_NAME)
            self.space_id = result["space"]["space_id"]
            print(f"  ✅ 知识空间创建成功: {self.space_id}")
        except Exception:
            # 空间可能已存在，尝试列出查找
            print(f"  ⚠️ 知识空间可能已存在，尝试查找...")
            # 如果 create_wiki_space 在空间已存在时抛异常，
            # 需要手动在飞书后台获取 space_id 并设置
            raise Exception(
                f"无法创建知识空间 '{WIKI_SPACE_NAME}'。"
                f"请检查飞书后台是否已存在同名空间，或手动设置 space_id。"
            )

        return self.space_id

    async def build_year_nodes(self) -> Dict[str, str]:
        """创建学年根节点

        Returns:
            {学年名称: node_token} 字典
        """
        if not self.space_id:
            await self.init_space()

        for year_name in WIKI_YEAR_NODES:
            try:
                result = await self._create_wiki_node(
                    title=year_name,
                    obj_type="docx"
                )
                token = result["data"]["node"]["node_token"]
                self.year_node_map[year_name] = token
                print(f"  ✅ 学年节点 [{year_name}]: {token}")
            except Exception as e:
                print(f"  ❌ 创建学年节点 [{year_name}] 失败: {e}")

        return self.year_node_map

    async def build_course_nodes(self) -> Dict[tuple, str]:
        """为每个学年的每门课程创建知识库子节点

        Returns:
            {(学年, 课程名): node_token} 字典
        """
        if not self.year_node_map:
            await self.build_year_nodes()

        for year_name, courses in COURSES_BY_YEAR.items():
            parent_token = self.year_node_map.get(year_name)
            if not parent_token:
                print(f"  ⚠️ 学年 [{year_name}] 无根节点，跳过课程创建")
                continue

            print(f"\n  📁 {year_name}（{len(courses)}门课）:")
            for course in courses:
                course_name = course["name"]
                try:
                    result = await self._create_wiki_node(
                        title=course_name,
                        obj_type="docx",
                        parent_node_token=parent_token
                    )
                    token = result["data"]["node"]["node_token"]
                    self.node_map[(year_name, course_name)] = token
                    print(f"    ✅ {course_name}: {token}")
                except Exception as e:
                    print(f"    ❌ {course_name} 失败: {e}")

        return self.node_map

    async def build_all(self) -> dict:
        """一键构建完整知识库结构

        Returns:
            {"space_id": ..., "year_nodes": ..., "course_nodes": ...}
        """
        print("🏗️ 开始构建知识库结构...")

        await self.init_space()
        await self.build_year_nodes()
        await self.build_course_nodes()

        print(f"\n✅ 知识库构建完成!")
        print(f"   空间ID: {self.space_id}")
        print(f"   学年节点: {len(self.year_node_map)}")
        print(f"   课程节点: {len(self.node_map)}")

        result = {
            "space_id": self.space_id,
            "year_nodes": self.year_node_map,
            "course_nodes": {
                f"{k[0]}-{k[1]}": v for k, v in self.node_map.items()
            }
        }

        # 保存到本地
        output_path = os.path.join(os.path.dirname(__file__), "..", "wiki_structure.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"   结构已保存: {output_path}")

        return result

    async def _create_wiki_node(
        self,
        title: str,
        obj_type: str = "docx",
        parent_node_token: Optional[str] = None
    ) -> dict:
        """创建知识库节点

        Args:
            title: 节点标题
            obj_type: 节点类型（docx/folder）
            parent_node_token: 父节点token（None则放在空间根目录）

        Returns:
            API响应
        """
        if not self.space_id:
            await self.init_space()

        url = f"{self.feishu.base_url}/wiki/v2/spaces/{self.space_id}/nodes"
        headers = await self.feishu._get_headers()

        data = {
            "obj_type": obj_type,
            "node_title": title
        }
        if parent_node_token:
            data["parent_node_token"] = parent_node_token

        response = await self.feishu.client.post(url, headers=headers, json=data)
        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"创建节点失败 [{title}]: {result.get('msg')}")

        return result

    def get_course_node_token(self, year: str, course_name: str) -> Optional[str]:
        """获取课程节点的token

        Args:
            year: 学年（大一/大二/大三/大四）
            course_name: 课程名称

        Returns:
            node_token 或 None
        """
        return self.node_map.get((year, course_name))

    def get_doc_url(self, year: str, course_name: str) -> Optional[str]:
        """生成课程文档的飞书链接

        Args:
            year: 学年
            course_name: 课程名称

        Returns:
            飞书文档URL 或 None
        """
        node_token = self.get_course_node_token(year, course_name)
        if node_token and self.space_id:
            return f"https://nkuyouth.feishu.cn/wiki/{node_token}"
        return None
