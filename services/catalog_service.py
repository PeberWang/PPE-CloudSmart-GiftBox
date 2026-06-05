# -*- coding: utf-8 -*-
"""PPE云端智能大礼包 - 目录服务（聚合摘要，供知识助手检索）"""

import structlog
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from libs.feishu import FeishuAdapter
from config.settings import Settings

logger = structlog.get_logger()

_CATALOG_PATH = "data/catalog.md"


class CatalogService:
    """读取 summary_dir 下所有摘要，生成「工具目录式」索引并上载到飞书云盘。"""

    def __init__(self, feishu: FeishuAdapter, settings: Settings):
        self.feishu = feishu
        self.settings = settings

    def build_catalog_text(self) -> str:
        summary_dir = Path(self.settings.summary_dir)
        entries = sorted(summary_dir.glob("*.md")) if summary_dir.exists() else []
        if not entries:
            return (
                "# PPE大礼包资料目录\n\n"
                "暂无摘要，请先运行 `--mode ocr` 生成摘要。\n"
            )

        lines = [
            "# PPE大礼包资料目录\n\n",
            f"> 自动生成，时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n",
        ]
        for path in entries:
            content = path.read_text(encoding="utf-8")
            snippet = next(
                (line for line in content.splitlines()[1:] if line.strip()), ""
            )
            lines.append(f"## {path.stem}\n\n{snippet}\n\n---\n\n")
        return "".join(lines)

    async def build_and_upload(self) -> Dict[str, Any]:
        """写本地 catalog.md，上传到飞书云盘，返回路径和 feishu_key。"""
        catalog_text = self.build_catalog_text()
        catalog_path = Path(_CATALOG_PATH)
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(catalog_text, encoding="utf-8")
        logger.info("目录已写入本地", path=str(catalog_path), chars=len(catalog_text))

        upload_result = await self.feishu.upload_file(str(catalog_path))
        logger.info("目录已上传到飞书", file_key=upload_result.get("file_key"))

        return {
            "catalog_path": str(catalog_path),
            "chars": len(catalog_text),
            "feishu_key": upload_result.get("file_key"),
        }
