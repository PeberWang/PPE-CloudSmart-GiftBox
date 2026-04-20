# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 配置文件
所有敏感信息通过环境变量或 .env 文件读取

路径解析优先级：
  1. 环境变量（MATERIALS_BASE / COURSE_REFORM_NOTES_DIR）
  2. .env 文件中的值
  3. 自动检测：先尝试绝对路径，再尝试相对于项目根目录的路径
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── 路径常量 ──
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent  # PPE-CloudSmart-GiftBox/
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"

# 部署产物目录（运行时生成的配置文件）
DEPLOY_OUTPUT_DIR = PROJECT_ROOT / "output"

# 加载 .env 文件（从项目根目录）
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def _resolve_path(env_key: str, absolute_default: str, relative_default: str) -> Path:
    """解析路径，支持绝对路径和相对路径"""
    env_val = os.getenv(env_key, "").strip()

    if env_val:
        p = Path(env_val)
        if p.is_absolute():
            return p
        return (PROJECT_ROOT / p).resolve()

    abs_path = Path(absolute_default)
    if abs_path.exists():
        return abs_path

    rel_path = PROJECT_ROOT / relative_default
    if rel_path.exists():
        return rel_path.resolve()

    return abs_path


# 原始材料包路径
MATERIALS_BASE = _resolve_path(
    env_key="MATERIALS_BASE",
    absolute_default=r"D:\c盘转移\Desktop\Claw工作文件夹\灵感实施附件\PPE云端智能大礼包\PPE大二上资料包",
    relative_default="materials",
)

# 课程教改笔记路径
COURSE_REFORM_NOTES_DIR = _resolve_path(
    env_key="COURSE_REFORM_NOTES_DIR",
    absolute_default=r"D:\c盘转移\Desktop\Claw工作文件夹\灵感实施附件\PPE云端智能大礼包\PPE课程教改笔记",
    relative_default="course_reform_notes",
)

# 智谱AI配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4-flash")

# 飞书配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_BASE_URL = os.getenv("FEISHU_BASE_URL", "https://open.feishu.cn/open-apis")

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "course_docs").mkdir(exist_ok=True)
DEPLOY_OUTPUT_DIR.mkdir(exist_ok=True)
