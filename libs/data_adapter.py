# -*- coding: utf-8 -*-
"""
数据结构适配器
封装 pandas/openpyxl，提供统一的文件读取接口
"""

import structlog
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from libs.exceptions import ConfigurationException

logger = structlog.get_logger()


def read_json(path: Path) -> Any:
    """读取 JSON 文件（UTF-8）。文件不存在返回 None。"""
    path = Path(path)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    """写入 JSON 文件（UTF-8, LF, 缩进2, 保留中文）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


_INDEX_FILE = "index.json"
_BACKUP_DIR = "backups"


def _safe_name(name: str) -> str:
    """课程名 → 安全文件名（Windows/Linux 兼容）。"""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "-")
    return name


def _index_path(db_dir: Path) -> Path:
    return Path(db_dir) / _INDEX_FILE


def _course_path(db_dir: Path, name: str) -> Path:
    return Path(db_dir) / f"{_safe_name(name)}.json"


def _backup_path(db_dir: Path, name: str) -> Path:
    return Path(db_dir) / _BACKUP_DIR / f"{_safe_name(name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def read_index(db_dir: Path) -> List[Dict[str, Any]]:
    """读取轻量课程清单 index.json。"""
    data = read_json(_index_path(db_dir))
    return data if isinstance(data, list) else []


def write_index(db_dir: Path, records: List[Dict[str, Any]]) -> None:
    """写入轻量课程清单（仅保留元数据字段）。"""
    light_fields = {"name", "teacher", "semester", "type", "exam", "year"}
    light = [{k: v for k, v in r.items() if k in light_fields} for r in records]
    write_json(_index_path(db_dir), light)


def read_course_db(db_dir: Path, year: str) -> List[Dict[str, Any]]:
    """读取某学年全部课程数据：查 index.json → 逐文件读取。"""
    index = read_index(db_dir)
    courses = []
    for meta in index:
        if meta.get("year") != year:
            continue
        path = _course_path(db_dir, meta["name"])
        if path.exists():
            courses.append(read_json(path))
        else:
            courses.append(meta)  # 回退：仅有元数据的轻量条目
    return courses


def write_course_db(db_dir: Path, year: str, records: List[Dict[str, Any]]) -> None:
    """逐课程写入独立 JSON 文件，同步更新 index.json。"""
    db = Path(db_dir)
    backup_dir = db / _BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)

    for r in records:
        name = r.get("name", "")
        if not name:
            continue
        path = _course_path(db, name)
        if path.exists():
            shutil.copy2(path, _backup_path(db, name))
        write_json(path, r)

    # 重建 index：收集所有现有课程文件的元数据
    all_meta = []
    for path in sorted(db.glob("*.json")):
        if path.name == _INDEX_FILE:
            continue
        data = read_json(path)
        if isinstance(data, dict):
            all_meta.append(data)
    write_index(db, all_meta)


class DataAdapter:
    """数据文件适配器"""

    @staticmethod
    def read_excel(file_path: str, sheet_name: str = None) -> pd.DataFrame:
        """读取 Excel 文件"""
        try:
            kwargs = {}
            if sheet_name:
                kwargs["sheet_name"] = sheet_name
            else:
                kwargs["engine"] = "openpyxl"
            df = pd.read_excel(file_path, **kwargs)
            logger.info("读取Excel成功", path=file_path, rows=len(df))
            return df
        except Exception as e:
            logger.error("读取Excel失败", path=file_path, error=str(e))
            raise ConfigurationException(f"读取Excel失败: {str(e)}")

    @staticmethod
    def read_csv(file_path: str, encoding: str = "utf-8") -> pd.DataFrame:
        """读取 CSV 文件"""
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            logger.info("读取CSV成功", path=file_path, rows=len(df))
            return df
        except Exception as e:
            logger.error("读取CSV失败", path=file_path, error=str(e))
            raise ConfigurationException(f"读取CSV失败: {str(e)}")

    @staticmethod
    def read_file(file_path: str) -> pd.DataFrame:
        """自动检测文件类型读取"""
        ext = file_path.lower()
        if ext.endswith(".xlsx") or ext.endswith(".xls"):
            return DataAdapter.read_excel(file_path)
        elif ext.endswith(".csv"):
            return DataAdapter.read_csv(file_path)
        else:
            raise ConfigurationException(f"不支持的文件格式: {file_path}")
