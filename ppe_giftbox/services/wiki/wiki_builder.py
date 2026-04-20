# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 知识库构建服务
负责创建飞书知识库空间、学年节点、课程节点
"""

import json
from typing import Dict, Optional

from ppe_giftbox.services.core.feishu_service import FeishuService
from ppe_giftbox.data.course_schema import WIKI_SPACE_NAME, WIKI_YEAR_NODES, COURSES_BY_YEAR
from ppe_giftbox.config import DEPLOY_OUTPUT_DIR


class WikiBuilder:
    """飞书知识库自动构建器"""

    def __init__(self, feishu: FeishuService):
        self.feishu = feishu
        self.space_id: Optional[str] = None
        self.node_map: Dict[tuple, dict] = {}
        self.year_node_map: Dict[str, str] = {}

    async def init_space(self, force_create: bool = False) -> str:
        if self.space_id:
            return self.space_id
        print(f"\n🔍 查找知识空间 '{WIKI_SPACE_NAME}'...")
        spaces = await self.feishu.list_wiki_spaces()
        for item in spaces:
            space = item.get("space", item)
            if space.get("name") == WIKI_SPACE_NAME:
                if not force_create:
                    self.space_id = space["space_id"]
                    print(f"  ✅ 找到现有空间，复用: {self.space_id}")
                    return self.space_id
                else:
                    print(f"  ⚠️ 空间已存在，将创建新空间...")
        try:
            result = await self.feishu.create_wiki_space(WIKI_SPACE_NAME)
            self.space_id = result["space"]["space_id"]
            print(f"  ✅ 知识空间创建成功: {self.space_id}")
        except Exception as e:
            print(f"  ❌ 创建知识空间失败: {e}")
            raise
        return self.space_id

    async def build_year_nodes(self) -> Dict[str, str]:
        if not self.space_id:
            await self.init_space()
        print(f"\n📚 创建学年节点...")
        for year_name in WIKI_YEAR_NODES:
            try:
                result = await self.feishu.create_wiki_node(space_id=self.space_id, title=year_name, obj_type="docx")
                token = result["data"]["node"]["node_token"]
                obj_token = result["data"]["node"]["obj_token"]
                self.year_node_map[year_name] = token
                print(f"  ✅ [{year_name}]: {token}")
            except Exception as e:
                print(f"  ❌ 创建学年节点 [{year_name}] 失败: {e}")
        return self.year_node_map

    async def build_course_nodes(self) -> Dict[tuple, dict]:
        if not self.year_node_map:
            await self.build_year_nodes()
        print(f"\n📖 创建课程节点...")
        for year_name, courses in COURSES_BY_YEAR.items():
            parent_token = self.year_node_map.get(year_name)
            if not parent_token:
                print(f"  ⚠️ 学年 [{year_name}] 无根节点，跳过课程创建")
                continue
            print(f"\n  📁 {year_name}（{len(courses)}门课）:")
            for course in courses:
                course_name = course["name"]
                try:
                    result = await self.feishu.create_wiki_node(space_id=self.space_id, title=course_name, obj_type="docx", parent_node_token=parent_token)
                    node_token = result["data"]["node"]["node_token"]
                    obj_token = result["data"]["node"]["obj_token"]
                    self.node_map[(year_name, course_name)] = {"node_token": node_token, "obj_token": obj_token}
                    print(f"    ✅ {course_name}: {node_token}")
                except Exception as e:
                    print(f"    ❌ {course_name} 失败: {e}")
        return self.node_map

    async def build_all(self) -> dict:
        print("🏗️ 开始构建知识库结构...")
        await self.init_space()
        await self.build_year_nodes()
        print(f"\n✅ 知识库构建完成!")
        print(f"   空间ID: {self.space_id}")
        print(f"   学年节点: {len(self.year_node_map)}")
        result = {"space_id": self.space_id, "year_nodes": self.year_node_map}
        # 保存到 output/wiki_structure.json
        output_path = DEPLOY_OUTPUT_DIR / "wiki_structure.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"   结构已保存: {output_path}")
        return result

    def get_course_node(self, year: str, course_name: str) -> Optional[dict]:
        return self.node_map.get((year, course_name))

    def get_doc_url(self, year: str, course_name: str) -> Optional[str]:
        # 优先查找独立文档映射
        try:
            mapping_path = DEPLOY_OUTPUT_DIR / "doc_mapping.json"
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            key = f"{year}-{course_name}"
            if key in mapping:
                return f"https://nkuyouth.feishu.cn/docx/{mapping[key]}"
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        node_info = self.get_course_node(year, course_name)
        if node_info and self.space_id:
            return f"https://nkuyouth.feishu.cn/wiki/{node_info['node_token']}"
        return None

    def load_from_local(self) -> bool:
        try:
            output_path = DEPLOY_OUTPUT_DIR / "wiki_structure.json"
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.space_id = data.get("space_id")
            self.year_node_map = data.get("year_nodes", {})
            for key, value in data.get("course_nodes", {}).items():
                year, course_name = key.split("-", 1)
                self.node_map[(year, course_name)] = value
            print(f"✅ 从本地加载知识库结构成功")
            print(f"   空间ID: {self.space_id}")
            print(f"   课程节点: {len(self.node_map)}")
            return True
        except FileNotFoundError:
            print(f"⚠️ 本地未找到 wiki_structure.json")
            return False
        except Exception as e:
            print(f"❌ 加载本地结构失败: {e}")
            return False
