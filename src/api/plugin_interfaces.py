"""
King_photo - 插件接口定义
定义所有插件类型的抽象接口，支持动态扩展
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List, Union


class IFormatPlugin(ABC):
    """格式插件接口"""
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """格式名称，如 'JPEG', 'PNG', 'HEIC'"""
        pass
    
    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """支持的扩展名列表，如 ['.jpg', '.jpeg']"""
        pass
    
    @property
    @abstractmethod
    def magic_numbers(self) -> List[bytes]:
        """文件头魔数列表"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """格式描述"""
        pass
    
    @abstractmethod
    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        """
        读取元数据
        
        Args:
            filepath: 文件路径
            
        Returns:
            元数据字典
        """
        pass
    
    @abstractmethod
    def write_metadata(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入元数据
        
        Args:
            filepath: 文件路径
            metadata: 元数据字典
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def get_datetime(self, filepath: str) -> Optional[datetime]:
        """
        获取拍摄时间
        
        Args:
            filepath: 文件路径
            
        Returns:
            拍摄时间，如果无法获取则返回 None
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查插件是否可用
        
        Returns:
            是否可用
        """
        return True
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        获取插件能力
        
        Returns:
            能力字典，包含：
            - exif_support: 是否支持EXIF
            - xmp_support: 是否支持XMP
            - iptc_support: 是否支持IPTC
            - write_support: 是否支持写入
            - batch_support: 是否支持批量操作
        """
        return {
            "exif_support": False,
            "xmp_support": False,
            "iptc_support": False,
            "write_support": False,
            "batch_support": False
        }


class IFunctionPlugin(ABC):
    """功能插件接口"""
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """插件类型 ('batch', 'export', 'convert' 等)"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
    
    @abstractmethod
    def execute(self, file_list: List[str], **kwargs) -> Dict[str, Any]:
        """
        执行插件功能
        
        Args:
            file_list: 文件列表
            **kwargs: 额外参数
            
        Returns:
            执行结果字典
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        获取插件参数定义
        
        Returns:
            参数字典，键为参数名，值为参数定义，包含：
            - type: 参数类型
            - default: 默认值
            - required: 是否必填
            - description: 参数描述
        """
        pass
    
    def is_available(self) -> bool:
        """检查插件是否可用"""
        return True
    
    def get_progress_callback(self):
        """获取进度回调函数"""
        return None


class IExtensionPlugin(ABC):
    """扩展插件接口"""
    
    @property
    @abstractmethod
    def extension_name(self) -> str:
        """扩展名称"""
        pass
    
    @property
    @abstractmethod
    def target_module(self) -> str:
        """目标模块 ('format_detector', 'metadata_reader', 'metadata_writer', 'repair_engine')"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """扩展描述"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """扩展优先级（数字越小优先级越高）"""
        pass
    
    @abstractmethod
    def before_execute(self, *args, **kwargs) -> Any:
        """
        执行前钩子
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            处理后的参数
        """
        pass
    
    @abstractmethod
    def after_execute(self, result: Any, *args, **kwargs) -> Any:
        """
        执行后钩子
        
        Args:
            result: 执行结果
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            处理后的结果
        """
        pass
    
    @abstractmethod
    def on_error(self, error: Exception, *args, **kwargs) -> Any:
        """
        错误处理钩子
        
        Args:
            error: 异常对象
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            处理结果
        """
        pass
    
    def is_enabled(self) -> bool:
        """检查扩展是否启用"""
        return True
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的插件列表"""
        return []


class PluginMetadata:
    """插件元数据"""
    
    def __init__(self, name: str, version: str, author: str, description: str,
                 plugin_type: str, dependencies: List[str] = None,
                 min_version: str = None, **kwargs):
        """
        初始化插件元数据
        
        Args:
            name: 插件名称
            version: 版本号
            author: 作者
            description: 描述
            plugin_type: 插件类型
            dependencies: 依赖的插件列表
            min_version: 最低支持的King_photo版本
            **kwargs: 额外元数据
        """
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.plugin_type = plugin_type
        self.dependencies = dependencies or []
        self.min_version = min_version
        self.extra = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "plugin_type": self.plugin_type,
            "dependencies": self.dependencies,
            "min_version": self.min_version,
            **self.extra
        }


class PluginError(Exception):
    """插件错误"""
    
    def __init__(self, plugin_name: str, message: str, error_code: str = None):
        """
        初始化插件错误
        
        Args:
            plugin_name: 插件名称
            message: 错误消息
            error_code: 错误代码
        """
        self.plugin_name = plugin_name
        self.error_code = error_code
        super().__init__(f"插件 {plugin_name} 错误: {message}")


class PluginLoadError(PluginError):
    """插件加载错误"""
    pass


class PluginExecutionError(PluginError):
    """插件执行错误"""
    pass


class PluginDependencyError(PluginError):
    """插件依赖错误"""
    pass


class PluginConfigError(PluginError):
    """插件配置错误"""
    pass