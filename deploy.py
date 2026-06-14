# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 统一部署入口

用法:
    python deploy.py full              # 完整部署
    python deploy.py wiki              # 仅创建知识库
    python deploy.py tables            # 创建多维表格
    python deploy.py docs --limit 1    # 生成1份文档
    python deploy.py upload            # 上传资料
    python deploy.py link              # 关联文档链接
    python deploy.py sync              # 增量同步
"""

import asyncio
import sys
from typing import Optional

import typer

sys.stdout.reconfigure(encoding='utf-8')

from glue.deploy import DeployArgs, deploy_mode
from config.settings import Settings

app = typer.Typer(help="PPE云端智能大礼包 - 统一部署工具")


async def _run(mode: str, limit: Optional[int] = None, incremental: bool = False):
    settings = Settings()
    args = DeployArgs(mode=mode, limit=limit, incremental=incremental)
    return await deploy_mode(settings, args)


@app.command()
def full():
    """完整部署（知识库 + 表格 + 文档 + 资料 + 关联）"""
    asyncio.run(_run("full"))


@app.command()
def wiki():
    """仅创建知识库结构"""
    asyncio.run(_run("wiki"))


@app.command()
def tables(incremental: bool = typer.Option(False, "--incremental", help="增量更新模式")):
    """为每个学年创建多维表格"""
    asyncio.run(_run("tables", incremental=incremental))


@app.command()
def docs(limit: Optional[int] = typer.Option(None, "--limit", help="限制生成文档数量")):
    """生成并上传课程学习指南文档"""
    asyncio.run(_run("docs", limit=limit))


@app.command()
def upload():
    """上传课程资料到飞书云盘"""
    asyncio.run(_run("upload"))


@app.command()
def link():
    """关联表格与文档链接"""
    asyncio.run(_run("link"))


@app.command()
def sync():
    """增量同步课程记录"""
    asyncio.run(_run("sync"))


@app.command(name="sync-form")
def sync_form():
    """从飞书表单管理表同步已批准记录到 data/db/*.json"""
    asyncio.run(_run("sync-form"))


@app.command(name="init-bitable")
def init_bitable():
    """创建管理用 bitable（资料管理表 + 心得管理表），返回 app_token"""
    asyncio.run(_run("init-bitable"))


@app.command(name="grant-bitable")
def grant_bitable(
    member: str = typer.Argument(..., help="协作者 ID（默认按 email 处理）"),
    member_type: str = typer.Option("email", "--type", "-t",
                                    help="ID 类型：email / openid / userid / departmentid"),
    perm: str = typer.Option("full_access", "--perm", "-p",
                             help="权限：view / edit / full_access"),
):
    """给 bitable 添加协作者（解决应用是 owner 时人没法 UI 操作的问题）"""
    from glue.deploy import _deploy_grant_bitable
    settings = Settings()
    asyncio.run(_deploy_grant_bitable(settings, member_type, member, perm))


@app.command(name="open-bitable")
def open_bitable(
    entity: str = typer.Option(
        "anyone_editable", "--entity", "-e",
        help="链接分享范围：closed / tenant_readable / tenant_editable / anyone_readable / anyone_editable",
    ),
):
    """设置 bitable 链接分享权限（凭链接即可访问，不需要协作者 ID）"""
    from glue.deploy import _deploy_open_bitable
    settings = Settings()
    asyncio.run(_deploy_open_bitable(settings, entity))


@app.command(name="fix-bitable")
def fix_bitable():
    """给已存在 bitable 的单选字段补上选项（不删现有数据）"""
    asyncio.run(_run("fix-bitable"))


@app.command()
def logs(limit: int = typer.Option(50, "--limit", help="显示最近 N 条日志")):
    """显示操作日志摘要和最近记录"""
    from libs.operation_log import recent_operations, operation_summary

    summary = operation_summary()
    typer.echo(f"总操作: {summary['total']}  失败: {summary['failed_count']}")
    if summary["by_operation"]:
        typer.echo("\n按操作统计:")
        for op, counts in sorted(summary["by_operation"].items()):
            typer.echo(f"  {op}: {counts['total']} 次, {counts['failed']} 次失败")

    entries = recent_operations(limit)
    if entries:
        typer.echo(f"\n最近 {len(entries)} 条:")
        for e in entries:
            status_icon = "[OK]" if e.get("status") == "ok" else ("[FAIL]" if e.get("status") == "failed" else "[..]")
            elapsed = f" ({e.get('elapsed_s', '')}s)" if e.get("elapsed_s") else ""
            typer.echo(f"  {status_icon} {e.get('operation','?')}{elapsed} — {e.get('started_at','?')}")


if __name__ == "__main__":
    app()
