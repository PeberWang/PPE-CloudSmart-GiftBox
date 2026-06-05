# -*- coding: utf-8 -*-
"""飞书 docx 块构建器 —— 纯函数，返回 lark-oapi Block 对象（无副作用、不调 API）。

block_type 编号（飞书 docx）：2 正文 / 3-5 标题h1-h3 / 12 无序列表 / 22 分割线 / 18 内嵌多维表格。
"""

from lark_oapi.api.docx.v1 import (
    Block, Text, TextElement, TextRun, Divider, Bitable,
)

_HEADING_BUILDER = {1: ("heading1", 3), 2: ("heading2", 4), 3: ("heading3", 5)}


def _text_model(content: str) -> Text:
    """单 run 的 Text 内容模型，供正文 / 标题 / 列表复用。"""
    return (Text.builder()
            .elements([TextElement.builder()
                       .text_run(TextRun.builder().content(content).build())
                       .build()])
            .build())


def text(content: str) -> Block:
    """正文段落。"""
    return Block.builder().block_type(2).text(_text_model(content)).build()


def heading(content: str, level: int = 1) -> Block:
    """标题（level 1/2/3 → h1/h2/h3）。"""
    field, block_type = _HEADING_BUILDER.get(level, _HEADING_BUILDER[1])
    builder = Block.builder().block_type(block_type)
    builder = getattr(builder, field)(_text_model(content))
    return builder.build()


def bullet(content: str) -> Block:
    """无序列表项。"""
    return Block.builder().block_type(12).bullet(_text_model(content)).build()


def divider() -> Block:
    """分割线。"""
    return Block.builder().block_type(22).divider(Divider.builder().build()).build()


def bitable_embed(app_token: str, table_id: str, view_type: int = 1) -> Block:
    """内嵌多维表格块（block_type=18）。token 格式 {app_token}_{table_id}；view_type 1=表格视图。"""
    return (Block.builder()
            .block_type(18)
            .bitable(Bitable.builder()
                     .token(f"{app_token}_{table_id}")
                     .view_type(view_type)
                     .build())
            .build())
