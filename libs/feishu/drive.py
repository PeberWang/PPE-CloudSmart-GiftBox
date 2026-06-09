# -*- coding: utf-8 -*-
"""飞书云盘(Drive)模块 - 基于 lark-oapi SDK"""
import os
from typing import Dict, List, Optional
from lark_oapi.api.drive.v1 import (
    UploadAllFileRequest,
    UploadAllFileRequestBody,
    DownloadFileRequest,
    DeleteFileRequest,
    CreateFolderFileRequest,
    CreateFolderFileRequestBody,
    ListFileRequest,
    MoveFileRequest,
    MoveFileRequestBody,
    BatchGetTmpDownloadUrlMediaRequest,
)
from libs.exceptions import FeishuAPIException

class DriveMixin:
    """云盘文件操作 — 统一使用 file/upload_all，异常时抛出 FeishuAPIException。"""
    async def upload_file(self, file_path: str, file_name: Optional[str] = None) -> Dict[str, str]:
        """上传文件到飞书云盘根目录，返回 {"file_key": token, "url": url}。"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if file_name is None:
            file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            body = (UploadAllFileRequestBody.builder()
                    .file_name(file_name)
                    .parent_type("explorer")
                    .parent_node("root")
                    .size(file_size)
                    .file(f)
                    .build())
            req = UploadAllFileRequest.builder().request_body(body).build()
            resp = await self.client.drive.v1.file.aupload_all(req)
        if not resp.success():
            raise FeishuAPIException(f"上传文件[{file_name}]失败: {resp.msg}", error_code=str(resp.code))
        file_token = resp.data.file_token
        url = f"https://{self.settings.feishu_doc_host}/drive/f/{file_token}"
        return {"file_key": file_token, "url": url}

    async def download_file(self, file_token: str) -> bytes:
        """下载文件内容，返回 bytes。"""
        req = DownloadFileRequest.builder().file_token(file_token).build()
        resp = await self.client.drive.v1.file.adownload(req)
        if not resp.success():
            raise FeishuAPIException(f"下载文件失败: {resp.msg}", error_code=str(resp.code))
        if resp.file is None:
            raise FeishuAPIException(f"下载文件为空: {file_token}")
        return resp.file.read()

    async def delete_file(self, file_token: str) -> None:
        """删除文件，失败抛出 FeishuAPIException。"""
        req = DeleteFileRequest.builder().file_token(file_token).type("file").build()
        resp = await self.client.drive.v1.file.adelete(req)
        if not resp.success():
            raise FeishuAPIException(f"删除文件失败: {resp.msg}", error_code=str(resp.code))

    async def create_folder(self, name: str, folder_token: str = "root") -> str:
        """创建文件夹，返回 folder_token。"""
        body = (CreateFolderFileRequestBody.builder()
                .name(name).folder_token(folder_token).build())
        req = CreateFolderFileRequest.builder().request_body(body).build()
        resp = await self.client.drive.v1.file.acreate_folder(req)
        if not resp.success():
            raise FeishuAPIException(f"创建文件夹失败: {resp.msg}", error_code=str(resp.code))
        return resp.data.token
    async def list_folder(self, folder_token: str = "root", page_size: int = 50) -> List[Dict]:
        """列出文件夹内容，返回 [{token, name, type, parent_token, url}, ...]。"""
        req = ListFileRequest.builder().folder_token(folder_token).page_size(page_size).build()
        resp = await self.client.drive.v1.file.alist(req)
        if not resp.success():
            raise FeishuAPIException(f"列出文件夹失败: {resp.msg}", error_code=str(resp.code))
        files = resp.data.files or []
        return [{"token": f.token, "name": f.name, "type": f.type,
                 "parent_token": f.parent_token, "url": f.url} for f in files]

    async def move_file(self, file_token: str, target_folder: str) -> str:
        """移动文件到目标文件夹，返回 task_id。"""
        body = (MoveFileRequestBody.builder()
                .folder_token(target_folder).type("file").build())
        req = MoveFileRequest.builder().file_token(file_token).request_body(body).build()
        resp = await self.client.drive.v1.file.amove(req)
        if not resp.success():
            raise FeishuAPIException(f"移动文件失败: {resp.msg}", error_code=str(resp.code))
        return resp.data.task_id

    async def get_download_url(self, file_token: str) -> str:
        """获取文件临时下载链接（media API，与 cloud download_url 对应）。"""
        req = (BatchGetTmpDownloadUrlMediaRequest.builder()
               .file_tokens([file_token]).build())
        resp = await self.client.drive.v1.media.abatch_get_tmp_download_url(req)
        if not resp.success():
            raise FeishuAPIException(f"获取下载链接失败: {resp.msg}", error_code=str(resp.code))
        urls = resp.data.tmp_download_urls or []
        if not urls:
            raise FeishuAPIException(f"未获取到下载链接: {file_token}")
        return urls[0].tmp_download_url
