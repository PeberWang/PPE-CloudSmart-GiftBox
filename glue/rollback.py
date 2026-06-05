# -*- coding: utf-8 -*-
"""
回滚逻辑
当部署失败时，清理已创建的资源
"""

import structlog
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = structlog.get_logger()


class ResourceType(Enum):
    """资源类型枚举"""
    WIKI_SPACE = "wiki_space"      # 知识空间
    WIKI_NODE = "wiki_node"        # 知识库节点
    DOCUMENT = "document"          # 文档
    TABLE = "table"                # 多维表格
    FILE = "file"                  # 上传的文件


@dataclass
class Resource:
    """资源记录"""
    type: ResourceType
    id: str                        # 资源唯一标识
    name: Optional[str] = None      # 资源名称（用于日志）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外信息


class RollbackManager:
    """回滚管理器"""

    def __init__(self):
        """初始化回滚管理器"""
        self.created_resources: List[Resource] = []
        self.failed_operations: List[Dict[str, Any]] = []
        self._is_rollback = False

    def record_wiki_space(self, space_id: str, space_name: str = None):
        """记录创建的知识空间"""
        resource = Resource(
            type=ResourceType.WIKI_SPACE,
            id=space_id,
            name=space_name or f"space_{space_id}"
        )
        self.created_resources.append(resource)
        logger.info("记录知识空间", space_id=space_id, space_name=space_name)

    def record_wiki_node(self, node_id: str, node_title: str, space_id: str = None):
        """记录创建的知识库节点（space_id 用于回滚时定位和删除节点）"""
        metadata = {}
        if space_id:
            metadata["space_id"] = space_id
        resource = Resource(
            type=ResourceType.WIKI_NODE,
            id=node_id,
            name=node_title,
            metadata=metadata
        )
        self.created_resources.append(resource)
        logger.info("记录知识库节点", node_id=node_id, node_title=node_title, space_id=space_id)

    def record_document(self, doc_id: str, doc_title: str = None):
        """记录创建的文档"""
        resource = Resource(
            type=ResourceType.DOCUMENT,
            id=doc_id,
            name=doc_title or f"doc_{doc_id}"
        )
        self.created_resources.append(resource)
        logger.info("记录文档", doc_id=doc_id, doc_title=doc_title)

    def record_table(self, app_token: str, table_id: str, table_name: str = None):
        """记录创建的表格"""
        resource = Resource(
            type=ResourceType.TABLE,
            id=table_id,
            name=table_name or f"table_{table_id}",
            metadata={"app_token": app_token}
        )
        self.created_resources.append(resource)
        logger.info("记录表格", app_token=app_token, table_id=table_id, table_name=table_name)

    def record_file(self, file_token: str, file_name: str):
        """记录上传的文件"""
        resource = Resource(
            type=ResourceType.FILE,
            id=file_token,
            name=file_name
        )
        self.created_resources.append(resource)
        logger.info("记录文件", file_token=file_token, file_name=file_name)

    def record_operation_failure(self, operation: str, error: str, context: Dict[str, Any] = None):
        """记录操作失败"""
        self.failed_operations.append({
            "operation": operation,
            "error": error,
            "context": context or {}
        })
        logger.error("操作失败", operation=operation, error=error, context=context)

    def get_resources_by_type(self, resource_type: ResourceType) -> List[Resource]:
        """获取指定类型的资源"""
        return [r for r in self.created_resources if r.type == resource_type]

    def get_space_nodes(self, space_id: str) -> List[Resource]:
        """获取指定空间的所有节点"""
        return [
            r for r in self.created_resources
            if r.type == ResourceType.WIKI_NODE and r.metadata.get("space_id") == space_id
        ]

    async def rollback_all(self, feishu_adapter) -> Dict[str, Any]:
        """
        回滚所有已创建的资源
        按照创建的逆序删除，避免依赖问题
        """
        if self._is_rollback:
            logger.warning("回滚已在进行中，跳过")
            return {"status": "skipped", "reason": "rollback already in progress"}

        self._is_rollback = True
        rollback_results = {
            "total_resources": len(self.created_resources),
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "skipped": 0,
            "manual_actions": []
        }

        logger.info("开始回滚所有资源", total=len(self.created_resources))

        # 按照创建的逆序处理
        for resource in reversed(self.created_resources):
            try:
                manual = await self._rollback_resource(resource, feishu_adapter)
                if manual:
                    rollback_results["manual_actions"].append(manual)
                    rollback_results["skipped"] += 1
                else:
                    rollback_results["success_count"] += 1
                    logger.info("资源回滚成功", resource_type=resource.type.value, resource_id=resource.id)
            except Exception as e:
                rollback_results["error_count"] += 1
                error_msg = f"回滚失败: {str(e)}"
                rollback_results["errors"].append({
                    "resource": {
                        "type": resource.type.value,
                        "id": resource.id,
                        "name": resource.name
                    },
                    "error": error_msg
                })
                logger.error("资源回滚失败",
                           resource_type=resource.type.value,
                           resource_id=resource.id,
                           error=error_msg)

        # 清空记录
        self.created_resources.clear()
        self.failed_operations.clear()
        self._is_rollback = False

        logger.info("回滚完成",
                  success=rollback_results["success_count"],
                  errors=rollback_results["error_count"],
                  skipped=rollback_results["skipped"])

        return rollback_results

    async def _rollback_resource(self, resource: Resource, feishu_adapter):
        """回滚单个资源，返回 None 表示自动删除成功，返回 dict 表示需要手动操作"""
        if resource.type == ResourceType.WIKI_SPACE:
            return await self._delete_wiki_space(resource, feishu_adapter)
        elif resource.type == ResourceType.WIKI_NODE:
            await self._delete_wiki_node(resource, feishu_adapter)
        elif resource.type == ResourceType.DOCUMENT:
            return await self._delete_document(resource, feishu_adapter)
        elif resource.type == ResourceType.TABLE:
            await self._delete_table(resource, feishu_adapter)
        elif resource.type == ResourceType.FILE:
            await self._delete_file(resource, feishu_adapter)
        else:
            logger.warning("不支持回滚的资源类型", resource_type=resource.type.value)

    async def _delete_wiki_space(self, resource: Resource, feishu_adapter):
        """飞书API不支持通过API删除知识空间，返回手动操作指引"""
        logger.warning("知识空间须手动删除", space_id=resource.id, space_name=resource.name)
        return {
            "type": "delete_wiki_space",
            "description": f"手动删除知识空间: {resource.name} (ID: {resource.id})",
            "instructions": "→ 飞书开放平台后台 > 知识空间 > 删除该空间"
        }

    async def _delete_wiki_node(self, resource: Resource, feishu_adapter) -> None:
        """删除知识库节点"""
        try:
            metadata = resource.metadata
            if "space_id" in metadata:
                # 调用API删除节点
                await feishu_adapter.delete_wiki_node(
                    space_id=metadata["space_id"],
                    node_id=resource.id
                )
            else:
                raise Exception("节点缺少space_id信息")
        except Exception as e:
            raise Exception(f"删除知识库节点失败: {str(e)}")

    async def _delete_document(self, resource: Resource, feishu_adapter):
        """飞书 docx API 不支持直接删除文档，返回手动操作指引"""
        logger.warning("文档须手动删除", doc_id=resource.id, doc_name=resource.name)
        return {
            "type": "delete_document",
            "description": f"手动删除文档: {resource.name} (ID: {resource.id})",
            "instructions": "→ 飞书文档页面 > 右键 > 删除文档"
        }

    async def _delete_table(self, resource: Resource, feishu_adapter) -> None:
        """删除多维表格"""
        try:
            metadata = resource.metadata
            if "app_token" in metadata:
                # 调用API删除表格
                await feishu_adapter.delete_bitable_table(
                    app_token=metadata["app_token"],
                    table_id=resource.id
                )
            else:
                raise Exception("表格缺少app_token信息")
        except Exception as e:
            raise Exception(f"删除表格失败: {str(e)}")

    async def _delete_file(self, resource: Resource, feishu_adapter) -> None:
        """删除文件"""
        try:
            # 调用API删除文件
            await feishu_adapter.delete_file(file_token=resource.id)
        except Exception as e:
            raise Exception(f"删除文件失败: {str(e)}")

    def get_rollback_summary(self) -> Dict[str, Any]:
        """获取回滚摘要信息"""
        type_counts = {}
        for resource in self.created_resources:
            type_counts[resource.type.value] = type_counts.get(resource.type.value, 0) + 1

        return {
            "total_resources": len(self.created_resources),
            "total_failures": len(self.failed_operations),
            "resource_counts": type_counts,
            "types": list(type_counts.keys()),
            "last_operation": self.failed_operations[-1] if self.failed_operations else None
        }

    def export_rollback_plan(self) -> Dict[str, Any]:
        """导出回滚计划（用于手动执行）"""
        rollback_plan = {
            "created_resources": [
                {
                    "type": r.type.value,
                    "id": r.id,
                    "name": r.name,
                    "metadata": r.metadata
                }
                for r in self.created_resources
            ],
            "failed_operations": self.failed_operations,
            "manual_actions": []
        }

        # 生成需要手动操作的项目
        for resource in self.created_resources:
            if resource.type == ResourceType.WIKI_SPACE:
                rollback_plan["manual_actions"].append({
                    "type": "delete_wiki_space",
                    "description": f"手动删除知识空间: {resource.name} (ID: {resource.id})",
                    "instructions": "请到飞书开放平台后台删除该空间"
                })
            elif resource.type == ResourceType.DOCUMENT:
                rollback_plan["manual_actions"].append({
                    "type": "delete_document",
                    "description": f"手动删除文档: {resource.name} (ID: {resource.id})",
                    "instructions": "请到飞书文档后台删除该文档"
                })

        return rollback_plan