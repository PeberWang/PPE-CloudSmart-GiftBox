# -*- coding: utf-8 -*-
"""LocalStubDrive — 本地目录占位实现，供开发期热插拔。文件落地 cloud_stub/。"""

import shutil
from pathlib import Path

from libs.cloud.base import CloudDriveAdapter


class LocalStubDrive(CloudDriveAdapter):
    """把文件复制到本地 stub_dir，key 格式 stub:{filename}。"""

    def __init__(self, stub_dir: Path):
        self.stub_dir = Path(stub_dir)
        self.stub_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, src_path: str, dest_name: str = "") -> str:
        name = dest_name or Path(src_path).name
        shutil.copy2(src_path, self.stub_dir / name)
        return f"stub:{name}"

    async def download_url(self, key: str) -> str:
        name = key.removeprefix("stub:")
        return str((self.stub_dir / name).resolve())
