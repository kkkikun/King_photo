"""
King_photo - 统一错误处理模块
提供错误类、错误处理器和错误报告功能
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Type
from enum import Enum


class ErrorCode(Enum):
    """错误代码枚举"""
    # 格式错误
    FORMAT_UNKNOWN = "FORMAT_UNKNOWN"
    FORMAT_UNSUPPORTED = "FORMAT_UNSUPPORTED"
    FORMAT_CORRUPTED = "FORMAT_CORRUPTED"
    FORMAT_MISMATCH = "FORMAT_MISMATCH"
    
    # 元数据错误
    METADATA_READ_FAILED = "METADATA_READ_FAILED"
    METADATA_WRITE_FAILED = "METADATA_WRITE_FAILED"
    METADATA_INVALID = "METADATA_INVALID"
    
    # 文件错误
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_ACCESS_DENIED = "FILE_ACCESS_DENIED"
    FILE_CORRUPTED = "FILE_CORRUPTED"
    FILE_ALREADY_EXISTS = "FILE_ALREADY_EXISTS"
    
    # 修复错误
    REPAIR_FAILED = "REPAIR_FAILED"
    REPAIR_EXTENSION_FAILED = "REPAIR_EXTENSION_FAILED"
    REPAIR_TIME_FAILED = "REPAIR_TIME_FAILED"
    
    # 插件错误
    PLUGIN_LOAD_FAILED = "PLUGIN_LOAD_FAILED"
    PLUGIN_INIT_FAILED = "PLUGIN_INIT_FAILED"
    PLUGIN_EXEC_FAILED = "PLUGIN_EXEC_FAILED"
    
    # 配置错误
    CONFIG_LOAD_FAILED = "CONFIG_LOAD_FAILED"
    CONFIG_SAVE_FAILED = "CONFIG_SAVE_FAILED"
    CONFIG_INVALID = "CONFIG_INVALID"
    
    # 工具错误
    EXIFTOOL_NOT_FOUND = "EXIFTOOL_NOT_FOUND"
    EXIFTOOL_EXEC_FAILED = "EXIFTOOL_EXEC_FAILED"
    
    # 系统错误
    SYSTEM_ERROR = "SYSTEM_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class KingPhotoError(Exception):
    """King_photo 基础错误类"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
                 details: Dict[str, Any] = None, cause: Exception = None):
        """
        初始化错误
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 详细信息
            cause: 原始异常
        """
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc() if cause else None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "error_code": self.error_code.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }
        
        if self.cause:
            result["cause"] = str(self.cause)
        
        if self.traceback:
            result["traceback"] = self.traceback
        
        return result
    
    def __str__(self) -> str:
        """字符串表示"""
        base_msg = f"[{self.error_code.value}] {super().__str__()}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base_msg += f" ({details_str})"
        return base_msg


# 具体错误类
class FormatError(KingPhotoError):
    """格式错误"""
    def __init__(self, message: str, details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message, ErrorCode.FORMAT_UNKNOWN, details, cause)


class MetadataError(KingPhotoError):
    """元数据错误"""
    def __init__(self, message: str, details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message, ErrorCode.METADATA_READ_FAILED, details, cause)


class FileError(KingPhotoError):
    """文件错误"""
    def __init__(self, message: str, details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message, ErrorCode.FILE_NOT_FOUND, details, cause)


class RepairError(KingPhotoError):
    """修复错误"""
    def __init__(self, message: str, details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message, ErrorCode.REPAIR_FAILED, details, cause)


class PluginError(KingPhotoError):
    """插件错误"""
    def __init__(self, message: str, details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message, ErrorCode.PLUGIN_LOAD_FAILED, details, cause)


class ConfigError(KingPhotoError):
    """配置错误"""
    def __init__(self, message: str, details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message, ErrorCode.CONFIG_LOAD_FAILED, details, cause)


class ExifToolError(KingPhotoError):
    """ExifTool错误"""
    def __init__(self, message: str, details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message, ErrorCode.EXIFTOOL_NOT_FOUND, details, cause)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self._handlers: Dict[Type[KingPhotoError], Callable[[KingPhotoError], Any]] = {}
        self._error_log: List[KingPhotoError] = []
        self._log_to_file = True
        self._log_file_path = "logs/error.log"
        
        # 注册默认处理器
        self.register_handler(KingPhotoError, self._default_handler)
    
    def register_handler(self, error_type: Type[KingPhotoError], 
                        handler: Callable[[KingPhotoError], Any]) -> None:
        """
        注册错误处理器
        
        Args:
            error_type: 错误类型
            handler: 处理函数
        """
        self._handlers[error_type] = handler
    
    def handle(self, error: KingPhotoError) -> Any:
        """
        处理错误
        
        Args:
            error: 错误对象
            
        Returns:
            处理结果
        """
        # 记录错误
        self._log_error(error)
        
        # 查找匹配的处理器
        handler = self._find_handler(type(error))
        if handler:
            try:
                return handler(error)
            except Exception as e:
                logger.error(f"错误处理器执行失败: {str(e)}")
        
        return None
    
    def _find_handler(self, error_type: Type[KingPhotoError]) -> Optional[Callable]:
        """查找匹配的错误处理器"""
        # 精确匹配
        if error_type in self._handlers:
            return self._handlers[error_type]
        
        # 查找父类处理器
        for registered_type, handler in self._handlers.items():
            if issubclass(error_type, registered_type):
                return handler
        
        return None
    
    def _log_error(self, error: KingPhotoError) -> None:
        """记录错误"""
        # 添加到错误日志
        self._error_log.append(error)
        
        # 使用logging记录
        if isinstance(error, (FileError, FormatError, MetadataError)):
            logger.warning(str(error))
        elif isinstance(error, (RepairError, PluginError, ConfigError)):
            logger.error(str(error))
        else:
            logger.error(str(error))
        
        # 写入文件
        if self._log_to_file:
            self._write_error_to_file(error)
    
    def _write_error_to_file(self, error: KingPhotoError) -> None:
        """将错误写入文件"""
        try:
            import os
            os.makedirs(os.path.dirname(self._log_file_path), exist_ok=True)
            
            with open(self._log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"时间: {error.timestamp.isoformat()}\n")
                f.write(f"错误类型: {error.__class__.__name__}\n")
                f.write(f"错误代码: {error.error_code.value}\n")
                f.write(f"错误消息: {str(error)}\n")
                
                if error.details:
                    f.write(f"详细信息: {error.details}\n")
                
                if error.cause:
                    f.write(f"原始异常: {str(error.cause)}\n")
                
                if error.traceback:
                    f.write(f"堆栈跟踪:\n{error.traceback}\n")
                
                f.write(f"{'='*80}\n")
        except Exception as e:
            logger.error(f"写入错误文件失败: {str(e)}")
    
    def _default_handler(self, error: KingPhotoError) -> None:
        """默认错误处理器"""
        logger.error(f"未处理的错误: {str(error)}")
    
    def get_error_log(self) -> List[KingPhotoError]:
        """获取错误日志"""
        return self._error_log.copy()
    
    def clear_error_log(self) -> None:
        """清空错误日志"""
        self._error_log.clear()
    
    def set_log_file(self, log_file: str) -> None:
        """设置错误日志文件路径"""
        self._log_file_path = log_file
    
    def enable_file_logging(self, enable: bool) -> None:
        """启用/禁用文件日志"""
        self._log_to_file = enable
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        summary = {
            "total_errors": len(self._error_log),
            "error_types": {},
            "recent_errors": []
        }
        
        # 统计错误类型
        for error in self._error_log:
            error_type = error.__class__.__name__
            if error_type not in summary["error_types"]:
                summary["error_types"][error_type] = 0
            summary["error_types"][error_type] += 1
        
        # 获取最近5个错误
        summary["recent_errors"] = [
            error.to_dict() for error in self._error_log[-5:]
        ]
        
        return summary


# 全局错误处理器实例
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: KingPhotoError) -> Any:
    """
    处理错误的快捷方法
    
    Args:
        error: 错误对象
        
    Returns:
        处理结果
    """
    return get_error_handler().handle(error)


def create_error(error_code: ErrorCode, message: str, 
                details: Dict[str, Any] = None, cause: Exception = None) -> KingPhotoError:
    """
    创建错误对象的工厂方法
    
    Args:
        error_code: 错误代码
        message: 错误消息
        details: 详细信息
        cause: 原始异常
        
    Returns:
        错误对象
    """
    error_class_map = {
        ErrorCode.FORMAT_UNKNOWN: FormatError,
        ErrorCode.FORMAT_UNSUPPORTED: FormatError,
        ErrorCode.FORMAT_CORRUPTED: FormatError,
        ErrorCode.FORMAT_MISMATCH: FormatError,
        
        ErrorCode.METADATA_READ_FAILED: MetadataError,
        ErrorCode.METADATA_WRITE_FAILED: MetadataError,
        ErrorCode.METADATA_INVALID: MetadataError,
        
        ErrorCode.FILE_NOT_FOUND: FileError,
        ErrorCode.FILE_ACCESS_DENIED: FileError,
        ErrorCode.FILE_CORRUPTED: FileError,
        ErrorCode.FILE_ALREADY_EXISTS: FileError,
        
        ErrorCode.REPAIR_FAILED: RepairError,
        ErrorCode.REPAIR_EXTENSION_FAILED: RepairError,
        ErrorCode.REPAIR_TIME_FAILED: RepairError,
        
        ErrorCode.PLUGIN_LOAD_FAILED: PluginError,
        ErrorCode.PLUGIN_INIT_FAILED: PluginError,
        ErrorCode.PLUGIN_EXEC_FAILED: PluginError,
        
        ErrorCode.CONFIG_LOAD_FAILED: ConfigError,
        ErrorCode.CONFIG_SAVE_FAILED: ConfigError,
        ErrorCode.CONFIG_INVALID: ConfigError,
        
        ErrorCode.EXIFTOOL_NOT_FOUND: ExifToolError,
        ErrorCode.EXIFTOOL_EXEC_FAILED: ExifToolError,
        
        ErrorCode.SYSTEM_ERROR: KingPhotoError,
        ErrorCode.UNKNOWN_ERROR: KingPhotoError,
    }
    
    error_class = error_class_map.get(error_code, KingPhotoError)
    return error_class(message, details=details, cause=cause)