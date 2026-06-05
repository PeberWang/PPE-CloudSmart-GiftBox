# -*- coding: utf-8 -*-
"""
PPE云端智能大礼包 - 自定义异常类
"""


class PPECloudSmartException(Exception):
    """基础异常类"""
    pass


class FeishuAPIException(PPECloudSmartException):
    """飞书API异常"""
    def __init__(self, message: str, error_code: str = None, request_id: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.request_id = request_id


class LLMServiceException(PPECloudSmartException):
    """LLM服务异常"""
    pass


class ConfigurationException(PPECloudSmartException):
    """配置异常"""
    pass


class FileUploadException(PPECloudSmartException):
    """文件上传异常"""
    pass