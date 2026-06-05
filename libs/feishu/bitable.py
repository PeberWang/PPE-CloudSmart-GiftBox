# -*- coding: utf-8 -*-
"""飞书多维表格(Bitable)模块 - 基于 lark-oapi SDK"""

from typing import Dict, Any, List, Optional
from lark_oapi.api.bitable.v1 import (
    CreateAppRequest, ReqApp,
    CreateAppTableRequest, CreateAppTableRequestBody, AppTable,
    CreateAppTableRecordRequest, AppTableRecord,
    UpdateAppTableRecordRequest,
    DeleteAppTableRequest,
    ListAppTableRecordRequest,
    BatchDeleteAppTableRecordRequest, BatchDeleteAppTableRecordRequestBody,
    CreateAppTableFieldRequest, AppTableField,
    ListAppTableFieldRequest,
    ListAppTableRequest,
    SearchAppTableRecordRequest, SearchAppTableRecordRequestBody,
    FilterInfo, Condition,
)
from libs.exceptions import FeishuAPIException


class BitableMixin:
    """多维表格操作"""

    async def create_bitable_app(self, name: str) -> Dict[str, str]:
        """创建多维表格应用(Base)，返回 app_token。API 创建的应用自动拥有完整权限。"""
        request = (CreateAppRequest.builder()
                   .request_body(ReqApp.builder().name(name).build())
                   .build())
        resp = await self.client.bitable.v1.app.acreate(request)
        if not resp.success():
            raise FeishuAPIException(f"创建多维表格应用[{name}]失败: {resp.msg}", error_code=str(resp.code))
        app_token = resp.data.app.app_token
        self.logger.info("多维表格应用创建成功", name=name, app_token=app_token)
        return {"app_token": app_token, "name": name, "url": resp.data.app.url}

    async def create_bitable_table(self, app_token: str, table_name: str) -> Dict[str, str]:
        body = (CreateAppTableRequestBody.builder()
                .table(AppTable.builder().name(table_name).build())
                .build())
        request = (CreateAppTableRequest.builder()
                   .app_token(app_token)
                   .request_body(body)
                   .build())
        resp = await self.client.bitable.v1.app_table.acreate(request)
        if not resp.success():
            raise FeishuAPIException(f"创建多维表格[{table_name}]失败: {resp.msg}", error_code=str(resp.code))
        table_id = resp.data.table_id
        await self._clear_default_rows(app_token, table_id)
        return {"table_id": table_id, "table_name": table_name, "url": ""}

    async def _clear_default_rows(self, app_token: str, table_id: str) -> None:
        """清除新建表格的默认空行（Fix Bug 2：数据写入位置不对）"""
        list_req = (ListAppTableRecordRequest.builder()
                    .app_token(app_token).table_id(table_id).page_size(50)
                    .build())
        list_resp = await self.client.bitable.v1.app_table_record.alist(list_req)
        if not list_resp.success() or not list_resp.data.items:
            return
        record_ids = [r.record_id for r in list_resp.data.items if r.record_id]
        if not record_ids:
            return
        del_req = (BatchDeleteAppTableRecordRequest.builder()
                   .app_token(app_token).table_id(table_id)
                   .request_body(BatchDeleteAppTableRecordRequestBody.builder()
                                 .records(record_ids).build())
                   .build())
        await self.client.bitable.v1.app_table_record.abatch_delete(del_req)

    async def add_bitable_record(self, app_token: str, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        record = AppTableRecord.builder().fields(fields).build()
        request = (CreateAppTableRecordRequest.builder()
                   .app_token(app_token).table_id(table_id)
                   .request_body(record).build())
        resp = await self.client.bitable.v1.app_table_record.acreate(request)
        if not resp.success():
            raise FeishuAPIException(f"添加表格记录失败: {resp.msg}", error_code=str(resp.code))
        return {"record_id": resp.data.record.record_id}

    async def update_bitable_record(self, app_token: str, table_id: str, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        record = AppTableRecord.builder().fields(fields).build()
        request = (UpdateAppTableRecordRequest.builder()
                   .app_token(app_token).table_id(table_id).record_id(record_id)
                   .request_body(record).build())
        resp = await self.client.bitable.v1.app_table_record.aupdate(request)
        if not resp.success():
            raise FeishuAPIException(f"更新表格记录失败: {resp.msg}", error_code=str(resp.code))
        return {"record_id": record_id}

    async def search_bitable_record(self, app_token: str, table_id: str, field_name: str, value: str) -> Optional[Dict[str, Any]]:
        body = (SearchAppTableRecordRequestBody.builder()
                .filter(FilterInfo.builder()
                        .conjunction("and")
                        .conditions([Condition.builder().field_name(field_name).operator("is").value([value]).build()])
                        .build())
                .build())
        request = (SearchAppTableRecordRequest.builder()
                   .app_token(app_token).table_id(table_id).page_size(1)
                   .request_body(body).build())
        resp = await self.client.bitable.v1.app_table_record.asearch(request)
        if not resp.success():
            raise FeishuAPIException(f"搜索表格记录失败: {resp.msg}", error_code=str(resp.code))
        items = resp.data.items or []
        return {"record_id": items[0].record_id, "fields": items[0].fields} if items else None

    async def create_bitable_fields(self, app_token: str, table_id: str, fields: list) -> List[Dict[str, Any]]:
        """逐字段创建（Bitable API 每次只支持一个字段）"""
        results = []
        for field_def in fields:
            f = (AppTableField.builder()
                 .field_name(field_def["field_name"])
                 .type(field_def["type"])
                 .build())
            request = (CreateAppTableFieldRequest.builder()
                       .app_token(app_token).table_id(table_id)
                       .request_body(f).build())
            resp = await self.client.bitable.v1.app_table_field.acreate(request)
            if resp.success():
                results.append({"field_name": field_def["field_name"]})
        return results

    async def list_bitable_fields(self, app_token: str, table_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        all_fields, page_token = [], None
        while True:
            builder = (ListAppTableFieldRequest.builder()
                       .app_token(app_token).table_id(table_id).page_size(page_size))
            if page_token:
                builder = builder.page_token(page_token)
            resp = await self.client.bitable.v1.app_table_field.alist(builder.build())
            if not resp.success():
                raise FeishuAPIException(f"列出表格字段失败: {resp.msg}", error_code=str(resp.code))
            for f in (resp.data.items or []):
                all_fields.append({"field_name": f.field_name, "type": f.type, "field_id": f.field_id})
            if not resp.data.has_more:
                break
            page_token = resp.data.page_token
        return all_fields

    async def get_bitable_tables(self, app_token: str) -> List[Dict[str, Any]]:
        request = ListAppTableRequest.builder().app_token(app_token).page_size(100).build()
        resp = await self.client.bitable.v1.app_table.alist(request)
        if not resp.success():
            raise FeishuAPIException(f"获取表格列表失败: {resp.msg}", error_code=str(resp.code))
        return [{"table_id": t.table_id, "name": t.name} for t in (resp.data.items or [])]

    async def delete_bitable_table(self, app_token: str, table_id: str) -> bool:
        request = DeleteAppTableRequest.builder().app_token(app_token).table_id(table_id).build()
        resp = await self.client.bitable.v1.app_table.adelete(request)
        if not resp.success():
            self.logger.error("删除表格失败", error=resp.msg)
            return False
        return True

    async def list_bitable_records(self, app_token: str, table_id: str,
                                    page_size: int = 100) -> List[Dict[str, Any]]:
        """分页列出表中所有记录，每行返回 {"record_id", "fields"}。"""
        all_records: List[Dict[str, Any]] = []
        page_token: Optional[str] = None
        while True:
            builder = (ListAppTableRecordRequest.builder()
                       .app_token(app_token).table_id(table_id).page_size(page_size))
            if page_token:
                builder = builder.page_token(page_token)
            resp = await self.client.bitable.v1.app_table_record.alist(builder.build())
            if not resp.success():
                raise FeishuAPIException(f"列出表格记录失败: {resp.msg}", error_code=str(resp.code))
            for r in (resp.data.items or []):
                all_records.append({"record_id": r.record_id, "fields": r.fields})
            if not resp.data.has_more:
                break
            page_token = resp.data.page_token
        return all_records
