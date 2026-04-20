# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 统一部署入口
一键部署知识库、多维表格、云文档、资料上传

用法：
    python deploy.py --mode full          # 完整部署（知识库+表格+文档+资料）
    python deploy.py --mode wiki          # 仅创建知识库结构
    python deploy.py --mode tables        # 仅创建多维表格
    python deploy.py --mode docs          # 仅生成并上传文档
    python deploy.py --mode upload        # 仅上传资料
    python deploy.py --mode link          # 仅关联表格与文档链接
    python deploy.py --mode cleanup      # 清理空记录、冗余字段、空节点
    python deploy.py --mode sync          # 增量同步课程记录（不覆盖用户修改）

    环境变量：
        MATERIALS_BASE           资料包路径（绝对或相对于项目根目录）
        COURSE_REFORM_NOTES_DIR  课程教改笔记路径
"""

import argparse
import asyncio

from ppe_giftbox.services.orchestrator import deploy_mode


def main():
    parser = argparse.ArgumentParser(
        description="PPE云端智能大礼包 - 统一部署工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python deploy.py --mode full          # 完整部署
    python deploy.py --mode wiki          # 仅创建知识库
    python deploy.py --mode docs          # 仅生成文档（需要先创建wiki）
    python deploy.py --mode link          # 仅关联链接（需要先创建wiki和tables）
        """
    )
    parser.add_argument(
        "--mode",
        choices=["full", "wiki", "tables", "docs", "upload", "link", "cleanup", "sync"],
        default="full",
        help="部署模式"
    )
    args = parser.parse_args()
    asyncio.run(deploy_mode(args.mode))


if __name__ == "__main__":
    main()
