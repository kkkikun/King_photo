# King_photo API 模块
# 提供统一的API接口和插件系统

from .interfaces import (
    IFormatDetector,
    IMetadataReader,
    IMetadataWriter,
    IRepairEngine,
    IFileProcessor
)

from .plugin_interfaces import (
    IFormatPlugin,
    IFunctionPlugin,
    IExtensionPlugin
)

from .unified_api import KingPhotoAPI, get_api, reset_api
from .plugin_manager import PluginManager

__version__ = "1.0.0"
__all__ = [
    # 核心接口
    "IFormatDetector",
    "IMetadataReader", 
    "IMetadataWriter",
    "IRepairEngine",
    "IFileProcessor",
    
    # 插件接口
    "IFormatPlugin",
    "IFunctionPlugin",
    "IExtensionPlugin",
    
    # API类
    "KingPhotoAPI",
    "PluginManager",
    
    # API辅助函数
    "get_api",
    "reset_api",
]