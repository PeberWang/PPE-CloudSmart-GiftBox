# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 资料上传服务
将 materials.json 中的资料文件上传到飞书知识库对应课程节点下
支持增量/全量更新模式
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ppe_giftbox.services.core.feishu_service import FeishuService
from ppe_giftbox.config import DATA_DIR

logger = logging.getLogger("material_uploader")


# ── 课程 → (学年, 课程名) 映射 ──
COURSE_YEAR_MAP: Dict[str, Tuple[str, str]] = {}


def _build_course_year_map() -> Dict[str, Tuple[str, str]]:
    """从 config.COURSES_BY_YEAR 构建反向映射: 课程名 → (学年, 课程名)"""
    from ppe_giftbox.data.course_schema import COURSES_BY_YEAR
    mapping: Dict[str, Tuple[str, str]] = {}
    for year, courses in COURSES_BY_YEAR.items():
        for c in courses:
            mapping[c["name"]] = (year, c["name"])
    return mapping


# ── 通用重试装饰器 ──
def retry_async(max_retries: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """异步函数重试装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    wait = delay * (backoff ** attempt)
                    logger.warning(
                        "第%d次尝试失败: %s, %0.1fs后重试...",
                        attempt + 1, e, wait
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait)
            raise last_err
        return wrapper
    return decorator


class MaterialUploader:
    """资料上传器

    读取 materials.json 中的资料元数据，将本地文件上传到飞书知识库
    对应课程节点下，并创建子节点。

    用法:
        uploader = MaterialUploader(mode="incremental")
        await uploader.run()
    """

    def __init__(
        self,
        mode: str = "incremental",
        wiki_structure_path: Optional[str] = None,
        dry_run: bool = False,
        batch_delay: float = 1.0,
    ):
        """
        Args:
            mode: 上传模式
                - "incremental": 只上传新增资料，跳过已存在的节点
                - "full": 重新上传所有资料
            wiki_structure_path: wiki_structure.json 路径（默认在 data/ 目录下）
            dry_run: 试运行模式，只检查不实际上传
            batch_delay: 每次上传后的间隔秒数（避免频率限制）
        """
        self.mode = mode
        self.dry_run = dry_run
        self.batch_delay = batch_delay

        # 路径
        self.materials_path = DATA_DIR / "materials.json"
        if not wiki_structure_path:
            wiki_structure_path = str(DEPLOY_OUTPUT_DIR / "wiki_structure.json")
        self.wiki_structure_path = wiki_structure_path

        # 加载数据
        self.materials: List[dict] = self._load_materials()
        self.wiki_structure: dict = self._load_wiki_structure()
        self.course_year_map = _build_course_year_map()

        # 已上传记录文件（用于增量判断）
        self.upload_record_path = DATA_DIR / "upload_records.json"
        self.upload_records: Dict[str, dict] = self._load_upload_records()

        # 统计
        self.stats = {
            "total": 0,
            "skipped_exists": 0,
            "skipped_no_node": 0,
            "skipped_no_file": 0,
            "uploaded": 0,
            "failed": 0,
            "errors": [],
        }

        # 飞书服务
        self.feishu: Optional[FeishuService] = None

    # ── 数据加载 ──

    def _load_materials(self) -> List[dict]:
        """加载 materials.json"""
        if not self.materials_path.exists():
            raise FileNotFoundError(f"materials.json 不存在: {self.materials_path}")
        with open(self.materials_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    def _load_wiki_structure(self) -> dict:
        """加载 wiki_structure.json"""
        if not os.path.exists(self.wiki_structure_path):
            raise FileNotFoundError(f"wiki_structure.json 不存在: {self.wiki_structure_path}")
        with open(self.wiki_structure_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_upload_records(self) -> Dict[str, dict]:
        """加载已上传记录"""
        if self.upload_record_path.exists():
            with open(self.upload_record_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_upload_records(self):
        """保存已上传记录"""
        with open(self.upload_record_path, "w", encoding="utf-8") as f:
            json.dump(self.upload_records, f, ensure_ascii=False, indent=2)

    # ── 节点查找 ──

    def _find_course_node(self, course_name: str) -> Optional[dict]:
        """根据课程名查找知识库节点

        Args:
            course_name: 课程名

        Returns:
            {"node_token": ..., "obj_token": ...} 或 None
        """
        course_nodes = self.wiki_structure.get("course_nodes", {})

        # 直接匹配 "学年-课程名" 格式
        year_info = self.course_year_map.get(course_name)
        if year_info:
            key = f"{year_info[0]}-{course_name}"
            if key in course_nodes:
                return course_nodes[key]

        # 模糊匹配：遍历所有节点，检查课程名部分
        for key, node in course_nodes.items():
            if "-" in key and key.split("-", 1)[1] == course_name:
                return node

        return None

    # ── 上传逻辑 ──

    async def _upload_file_to_feishu(
        self, file_path: str, parent_node_token: str
    ) -> str:
        """上传文件到飞书，然后将文件添加到知识库

        Args:
            file_path: 本地文件路径
            parent_node_token: 知识库父节点 token

        Returns:
            wiki_node_token
        """
        # Step 1: 上传文件到云空间
        file_token = await self.feishu.upload_file(
            file_path=file_path,
            parent_type="wiki_file",
            parent_node=parent_node_token,
        )
        logger.info("文件上传成功, file_token: %s", file_token)

        # Step 2: 将上传的文件添加到知识库节点
        space_id = self.wiki_structure["space_id"]
        result = await self.feishu.move_doc_to_wiki(
            space_id=space_id,
            obj_token=file_token,
            obj_type="file",
            parent_node_token=parent_node_token,
        )
        node_token = result.get("node_token")
        logger.info("文件已添加到知识库, node_token: %s", node_token)
        return node_token

    async def _process_material(self, material: dict) -> bool:
        """处理单个资料

        Args:
            material: materials.json 中的一条记录

        Returns:
            是否处理成功
        """
        material_id = material["material_id"]
        course_name = material["course_name"]
        file_path = material["file_path"]
        original_name = material["original_name"]

        self.stats["total"] += 1

        # ── 增量模式：跳过已上传 ──
        if self.mode == "incremental" and material_id in self.upload_records:
            logger.debug("跳过已上传: %s", material_id)
            self.stats["skipped_exists"] += 1
            return True

        # ── 检查文件是否存在 ──
        if not os.path.exists(file_path):
            logger.warning("文件不存在: %s", file_path)
            self.stats["skipped_no_file"] += 1
            self.stats["errors"].append({
                "material_id": material_id,
                "reason": "file_not_found",
                "file_path": file_path,
            })
            return False

        # ── 查找课程节点 ──
        course_node = self._find_course_node(course_name)
        if not course_node:
            logger.warning("未找到课程节点: %s", course_name)
            self.stats["skipped_no_node"] += 1
            self.stats["errors"].append({
                "material_id": material_id,
                "reason": "no_course_node",
                "course_name": course_name,
            })
            return False

        parent_token = course_node["node_token"]

        # ── 试运行模式 ──
        if self.dry_run:
            logger.info(
                "[DRY RUN] 将上传: %s → 课程: %s",
                original_name, course_name,
            )
            self.stats["uploaded"] += 1
            return True

        # ── 实际上传 ──
        try:
            node_token = await self._upload_file_to_feishu(
                file_path, parent_token
            )

            # 记录上传结果
            self.upload_records[material_id] = {
                "node_token": node_token,
                "course_name": course_name,
                "original_name": original_name,
                "upload_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "file_size": os.path.getsize(file_path),
            }
            self._save_upload_records()

            self.stats["uploaded"] += 1
            logger.info("✅ 上传成功: %s (%s)", original_name, material_id)
            return True

        except Exception as e:
            logger.error("上传失败: %s - %s", material_id, e)
            self.stats["failed"] += 1
            self.stats["errors"].append({
                "material_id": material_id,
                "reason": "upload_error",
                "error": str(e),
            })
            return False

    # ── 主流程 ──

    async def run(self) -> dict:
        """执行资料上传

        Returns:
            上传统计信息
        """
        logger.info("=" * 60)
        logger.info("资料上传开始 | 模式: %s | 试运行: %s", self.mode, self.dry_run)
        logger.info("资料总数: %d", len(self.materials))
        logger.info("=" * 60)

        # 筛选已审核的资料
        approved = [m for m in self.materials if m.get("status") == "approved"]
        logger.info("已审核资料: %d", len(approved))

        if not approved:
            logger.warning("没有已审核的资料需要上传")
            return self.stats

        # 按课程分组显示
        course_counts: Dict[str, int] = {}
        for m in approved:
            course_counts[m["course_name"]] = course_counts.get(m["course_name"], 0) + 1
        for course, count in sorted(course_counts.items()):
            logger.info("  %s: %d 份资料", course, count)

        # 初始化飞书服务
        if not self.dry_run:
            self.feishu = FeishuService()
            try:
                await self.feishu.get_tenant_access_token()
                logger.info("飞书认证成功")
            except Exception as e:
                logger.error("飞书认证失败: %s", e)
                raise

        # 逐个处理
        for i, material in enumerate(approved, 1):
            logger.info(
                "[%d/%d] 处理: %s (%s)",
                i, len(approved), material["material_id"], material["original_name"],
            )
            await self._process_material(material)

            # 间隔等待，避免频率限制
            if not self.dry_run and i < len(approved):
                await asyncio.sleep(self.batch_delay)

        # 关闭飞书服务
        if self.feishu:
            await self.feishu.close()

        # 输出统计
        logger.info("=" * 60)
        logger.info("上传完成 | 统计:")
        logger.info("  总计处理: %d", self.stats["total"])
        logger.info("  成功上传: %d", self.stats["uploaded"])
        logger.info("  跳过(已存在): %d", self.stats["skipped_exists"])
        logger.info("  跳过(无课程节点): %d", self.stats["skipped_no_node"])
        logger.info("  跳过(文件不存在): %d", self.stats["skipped_no_file"])
        logger.info("  上传失败: %d", self.stats["failed"])
        if self.stats["errors"]:
            logger.info("  错误详情:")
            for err in self.stats["errors"][:10]:
                logger.info("    - %s: %s", err["material_id"], err["reason"])
            if len(self.stats["errors"]) > 10:
                logger.info("    ... 还有 %d 条错误", len(self.stats["errors"]) - 10)
        logger.info("=" * 60)

        return self.stats


# ── CLI ──

def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="PPE资料上传到飞书知识库")
    parser.add_argument(
        "--mode", "-m",
        choices=["incremental", "full"],
        default="incremental",
        help="上传模式: incremental(增量,默认) | full(全量)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="试运行模式，只检查不上传",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细日志输出",
    )
    parser.add_argument(
        "--delay", "-d",
        type=float, default=1.0,
        help="上传间隔秒数 (默认1.0)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    uploader = MaterialUploader(
        mode=args.mode,
        dry_run=args.dry_run,
        batch_delay=args.delay,
    )

    stats = asyncio.run(uploader.run())

    # 输出摘要到文件
    summary_path = DATA_DIR / "upload_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n摘要已保存: {summary_path}")


if __name__ == "__main__":
    main()
