# -*- coding: utf-8 -*-
"""GLM-OCR 适配器：split → batch OCR → assemble markdown（asyncio + httpx）。"""

import asyncio
import base64
import io
import json
from typing import List

import httpx
from pypdf import PdfReader, PdfWriter


def _split_pdf_bytes(pdf_path: str, pages_per_batch: int = 84) -> List[bytes]:
    """把 PDF 按页数切成多个字节批次。"""
    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    batches = []
    for start in range(0, total, pages_per_batch):
        writer = PdfWriter()
        for i in range(start, min(start + pages_per_batch, total)):
            writer.add_page(reader.pages[i])
        buf = io.BytesIO()
        writer.write(buf)
        batches.append(buf.getvalue())
    return batches


async def _call_glm_ocr(pdf_bytes: bytes, api_key: str, ocr_url: str) -> str:
    """发单批 PDF 给 GLM-OCR，返回 markdown 文本。"""
    b64 = base64.b64encode(pdf_bytes).decode()
    payload = {"model": "glm-ocr", "file": f"data:application/pdf;base64,{b64}"}
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(ocr_url, json=payload, headers=headers)
        resp.raise_for_status()
    data = resp.json()
    return data.get("md_results") or json.dumps(data, ensure_ascii=False)


async def run_ocr(
    pdf_path: str,
    api_key: str,
    ocr_url: str,
    pages_per_batch: int = 84,
    sleep_s: float = 3.0,
) -> str:
    """PDF → GLM-OCR 全量 markdown（按批次，批次间休眠 sleep_s 秒）。"""
    batches = _split_pdf_bytes(pdf_path, pages_per_batch)
    parts = []
    for i, batch_bytes in enumerate(batches):
        parts.append(await _call_glm_ocr(batch_bytes, api_key, ocr_url))
        if i < len(batches) - 1:
            await asyncio.sleep(sleep_s)
    return "\n\n".join(parts)
