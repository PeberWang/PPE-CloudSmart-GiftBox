# -*- coding: utf-8 -*-
"""操作日志 — 记录部署步骤的开始/结束/错误，输出到 data/operation_log.jsonl。"""

import json
import structlog
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps
from typing import Dict, Any

logger = structlog.get_logger()

_LOG_PATH = Path("data/operation_log.jsonl")


def _ensure_dir() -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_operation(name: str, **extra_params):
    """异步函数装饰器：自动记录开始、成功（含耗时）、失败。"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            started = datetime.now(timezone.utc)
            entry = {
                "operation": name,
                "started_at": started.isoformat(),
                "status": "started",
                "params": extra_params or None,
            }
            _append(entry)
            try:
                result = await func(*args, **kwargs)
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                entry = {**entry, "status": "ok", "elapsed_s": round(elapsed, 3)}
                _append(entry)
                return result
            except Exception as exc:
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                entry = {**entry, "status": "failed", "elapsed_s": round(elapsed, 3), "error": str(exc)}
                _append(entry)
                raise
        return wrapper
    return decorator


def _append(entry: Dict[str, Any]) -> None:
    _ensure_dir()
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def recent_operations(limit: int = 50) -> list:
    """读取最近 N 条操作日志。"""
    if not _LOG_PATH.exists():
        return []
    entries: list = []
    with open(_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                entries.append(json.loads(s))
    return entries[-limit:]


def operation_summary() -> Dict[str, Any]:
    """统计操作日志：总数、失败数、按操作分组。"""
    entries = recent_operations(1000)
    failed = [e for e in entries if e.get("status") == "failed"]
    by_op: Dict[str, Dict[str, int]] = {}
    for e in entries:
        op = e.get("operation", "unknown")
        by_op.setdefault(op, {"total": 0, "failed": 0})
        by_op[op]["total"] += 1
        if e.get("status") == "failed":
            by_op[op]["failed"] += 1
    return {"total": len(entries), "failed_count": len(failed), "by_operation": by_op}
