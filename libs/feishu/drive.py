# -*- coding: utf-8 -*-
"""飞书云盘(Drive)模块 - 基于 lark-oapi SDK"""

import os
from typing import Dict, Optional
from lark_oapi.api.drive.v1 import (
    UploadAllMediaRequest, UploadAllMediaRequestBody,
    DeleteFileRequest,
)
from libs.exceptions import FeishuAPIException


class DriveMixin:
    """云盘文件操作"""

    async def upload_file(self, file_path: str, file_name: Optional[str] = None) -> Dict[str, str]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if file_name is None:
            file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            body = (UploadAllMediaRequestBody.builder()
                    .file_name(file_name)
                    .parent_type("drive_file")
                    .parent_node("root")
                    .size(file_size)
                    .file(f)
                    .build())
            request = UploadAllMediaRequest.builder().request_body(body).build()
            resp = await self.client.drive.v1.media.aupload_all(request)
        if not resp.success():
            raise FeishuAPIException(f"上传文件[{file_name}]失败: {resp.msg}", error_code=str(resp.code))
        return {"file_key": resp.data.file_token, "url": resp.data.file_token}

    async def delete_file(self, file_token: str) -> bool:
        request = DeleteFileRequest.builder().file_token(file_token).type("file").build()
        resp = await self.client.drive.v1.file.adelete(request)
        if not resp.success():
            self.logger.error("删除文件失败", error=resp.msg)
            return False
        return True
