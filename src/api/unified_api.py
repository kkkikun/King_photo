"""
King_photo - 统一API入口
提供所有功能的统一访问接口，支持插件扩展
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

from .interfaces import (
    IFormatDetector,
    IMetadataReader,
    IMetadataWriter,
    IRepairEngine,
    IFileProcessor
)
from .plugin_interfaces import IFormatPlugin, IFunctionPlugin, IExtensionPlugin
from .plugin_manager import PluginManager

# 获取日志记录器
logger = logging.getLogger(__name__)


class KingPhotoAPI:
    """King_photo 统一API入口"""
    
    def __init__(self, config_path: str = None, plugin_dir: str = None):
        """
        初始化API
        
        Args:
            config_path: 配置文件路径，可选
            plugin_dir: 插件目录，可选
        """
        self._config_path = config_path
        self._plugin_dir = plugin_dir or "plugins"
        
        # 初始化核心模块（延迟导入，避免循环依赖）
        self._format_detector = None
        self._metadata_reader = None
        self._metadata_writer = None
        self._repair_engine = None
        self._file_processor = None
        
        # 插件管理器
        self._plugin_manager = PluginManager()
        
        # 配置管理
        self._config = None
        
        logger.info("King_photo API 初始化完成")
    
    def _ensure_initialized(self):
        """确保核心模块已初始化"""
        if self._format_detector is None:
            self._init_core_modules()
    
    def _init_core_modules(self):
        """初始化核心模块"""
        try:
            # 延迟导入核心模块
            from ..core.format_detector import FormatDetector
            from ..core.metadata_reader import MetadataReader
            from ..core.metadata_writer import MetadataWriter
            from ..core.repair_engine import RepairEngine
            from ..core.file_processor import FileProcessor
            from ..utils.config_manager import ConfigManager
            
            # 创建实例
            self._format_detector = FormatDetector()
            self._metadata_reader = MetadataReader()
            self._metadata_writer = MetadataWriter()
            self._repair_engine = RepairEngine()
            self._file_processor = FileProcessor()
            
            # 初始化配置管理器
            if self._config_path:
                self._config = ConfigManager(self._config_path)
            else:
                self._config = ConfigManager()
            
            # 加载插件
            self._load_plugins()
            
            logger.info("核心模块初始化完成")
            
        except Exception as e:
            logger.error(f"初始化核心模块失败: {str(e)}")
            raise
    
    def _load_plugins(self):
        """加载插件"""
        try:
            if os.path.exists(self._plugin_dir):
                self._plugin_manager.load_plugins(self._plugin_dir)
                logger.info(f"插件加载完成: {len(self._plugin_manager.get_all_plugins())} 个插件")
        except Exception as e:
            logger.warning(f"加载插件失败: {str(e)}")
    
    # ========== 格式检测API ==========
    
    def detect_format(self, filepath: str) -> Dict[str, Any]:
        """
        检测文件格式
        
        Args:
            filepath: 文件路径
            
        Returns:
            格式信息字典
        """
        self._ensure_initialized()
        
        # 先尝试使用插件检测
        format_plugin = self._plugin_manager.get_format_plugin_by_file(filepath)
        if format_plugin:
            return {
                "format": format_plugin.format_name,
                "extensions": format_plugin.extensions,
                "plugin": format_plugin.__class__.__name__
            }
        
        # 使用默认格式检测器
        return self._format_detector.get_format_info(filepath)
    
    def is_supported(self, filepath: str) -> bool:
        """
        检查文件是否支持
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否支持
        """
        self._ensure_initialized()
        
        # 先尝试使用插件检测
        format_plugin = self._plugin_manager.get_format_plugin_by_file(filepath)
        if format_plugin:
            return True
        
        # 使用默认格式检测器
        format_info = self._format_detector.get_format_info(filepath)
        return format_info.get("is_image", False) or format_info.get("is_video", False)
    
    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有支持的格式
        
        Returns:
            格式字典
        """
        self._ensure_initialized()
        
        formats = self._format_detector.get_supported_formats()
        
        # 添加插件支持的格式
        for plugin in self._plugin_manager.get_format_plugins():
            formats[plugin.format_name] = {
                "extensions": plugin.extensions,
                "magic_numbers": plugin.magic_numbers,
                "description": plugin.description,
                "plugin": plugin.__class__.__name__
            }
        
        return formats
    
    # ========== 元数据读取API ==========
    
    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        """
        读取图片元数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            元数据字典
        """
        self._ensure_initialized()
        
        # 先尝试使用插件读取
        format_plugin = self._plugin_manager.get_format_plugin_by_file(filepath)
        if format_plugin and format_plugin.is_available():
            try:
                metadata = format_plugin.read_metadata(filepath)
                metadata["plugin"] = format_plugin.__class__.__name__
                return metadata
            except Exception as e:
                logger.warning(f"插件读取元数据失败，使用默认读取器: {str(e)}")
        
        # 使用默认元数据读取器
        return self._metadata_reader.read_metadata(filepath)
    
    def get_datetime(self, filepath: str) -> Optional[datetime]:
        """
        获取拍摄时间
        
        Args:
            filepath: 图片路径
            
        Returns:
            拍摄时间
        """
        self._ensure_initialized()
        
        # 先尝试使用插件获取
        format_plugin = self._plugin_manager.get_format_plugin_by_file(filepath)
        if format_plugin and format_plugin.is_available():
            try:
                return format_plugin.get_datetime(filepath)
            except Exception as e:
                logger.warning(f"插件获取时间失败，使用默认读取器: {str(e)}")
        
        # 使用默认元数据读取器
        return self._metadata_reader.get_datetime(filepath)
    
    def get_metadata_summary(self, filepath: str) -> Dict[str, Any]:
        """
        获取元数据摘要
        
        Args:
            filepath: 图片路径
            
        Returns:
            摘要字典
        """
        self._ensure_initialized()
        return self._metadata_reader.get_summary(filepath)
    
    def get_editable_fields(self, filepath: str) -> Dict[str, Any]:
        """
        获取可编辑字段
        
        Args:
            filepath: 图片路径
            
        Returns:
            可编辑字段字典
        """
        self._ensure_initialized()
        return self._metadata_reader.get_editable_fields(filepath)
    
    def read_exif(self, filepath: str) -> Dict[str, Any]:
        """
        读取EXIF数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            EXIF数据字典
        """
        self._ensure_initialized()
        return self._metadata_reader.read_exif(filepath)
    
    def read_xmp(self, filepath: str) -> Dict[str, Any]:
        """
        读取XMP数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            XMP数据字典
        """
        self._ensure_initialized()
        return self._metadata_reader.read_xmp(filepath)
    
    # ========== 元数据写入API ==========
    
    def write_metadata(self, filepath: str, metadata: Dict[str, Any], 
                      copy_mode: bool = False, output_dir: str = None) -> Dict[str, Any]:
        """
        写入元数据
        
        Args:
            filepath: 图片路径
            metadata: 元数据字典
            copy_mode: 是否复制模式
            output_dir: 输出目录
            
        Returns:
            操作结果字典
        """
        self._ensure_initialized()
        return self._metadata_writer.write_metadata(filepath, metadata, copy_mode, output_dir)
    
    def write_metadata_from_filetime(self, filepath: str, 
                                   copy_mode: bool = False, output_dir: str = None) -> Dict[str, Any]:
        """
        将文件时间复制到EXIF
        
        Args:
            filepath: 图片路径
            copy_mode: 是否复制模式
            output_dir: 输出目录
            
        Returns:
            操作结果字典
        """
        self._ensure_initialized()
        return self._metadata_writer.write_metadata_from_filetime(filepath, copy_mode, output_dir)
    
    def batch_write_metadata(self, file_list: List[str], metadata: Dict[str, Any],
                           copy_mode: bool = False, output_dir: str = None,
                           progress_callback=None) -> Dict[str, Any]:
        """
        批量写入元数据
        
        Args:
            file_list: 文件列表
            metadata: 元数据字典
            copy_mode: 是否复制模式
            output_dir: 输出目录
            progress_callback: 进度回调函数
            
        Returns:
            批量操作结果字典
        """
        self._ensure_initialized()
        return self._metadata_writer.batch_write_metadata(
            file_list, metadata, copy_mode, output_dir, progress_callback
        )
    
    def write_exif(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入EXIF数据
        
        Args:
            filepath: 图片路径
            metadata: EXIF数据字典
            
        Returns:
            是否成功
        """
        self._ensure_initialized()
        return self._metadata_writer.write_exif(filepath, metadata)
    
    def write_xmp(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入XMP数据
        
        Args:
            filepath: 图片路径
            metadata: XMP数据字典
            
        Returns:
            是否成功
        """
        self._ensure_initialized()
        return self._metadata_writer.write_xmp(filepath, metadata)
    
    def copy_filetime_to_exif(self, filepath: str) -> bool:
        """
        复制文件时间到EXIF
        
        Args:
            filepath: 图片路径
            
        Returns:
            是否成功
        """
        self._ensure_initialized()
        return self._metadata_writer.copy_filetime_to_exif(filepath)
    
    # ========== 修复API ==========
    
    def check_file_extension(self, filepath: str) -> Dict[str, Any]:
        """
        检查文件后缀
        
        Args:
            filepath: 文件路径
            
        Returns:
            检查结果字典
        """
        self._ensure_initialized()
        return self._repair_engine.check_file_extension(filepath)
    
    def fix_extension(self, filepath: str, output_dir: str = None) -> Dict[str, Any]:
        """
        修复文件后缀
        
        Args:
            filepath: 文件路径
            output_dir: 输出目录
            
        Returns:
            修复结果字典
        """
        self._ensure_initialized()
        return self._repair_engine.fix_extension(filepath, output_dir)
    
    def extract_time_info(self, filepath: str, time_source: str = 'auto') -> Dict[str, Any]:
        """
        提取时间信息
        
        Args:
            filepath: 文件路径
            time_source: 时间来源
            
        Returns:
            时间信息字典
        """
        self._ensure_initialized()
        return self._repair_engine.extract_time_info(filepath, time_source)
    
    def repair_file(self, filepath: str, output_dir: str = None,
                   fix_extension: bool = True, fix_time: bool = True,
                   time_source: str = 'auto', rename_format: str = None) -> Dict[str, Any]:
        """
        修复文件
        
        Args:
            filepath: 文件路径
            output_dir: 输出目录
            fix_extension: 是否修复扩展名
            fix_time: 是否修复时间
            time_source: 时间来源
            rename_format: 重命名格式
            
        Returns:
            修复结果字典
        """
        self._ensure_initialized()
        return self._repair_engine.repair(
            filepath, output_dir, fix_extension, fix_time, time_source, rename_format
        )
    
    def batch_repair(self, file_list: List[str], output_dir: str = None,
                    fix_extension: bool = True, fix_time: bool = True,
                    time_source: str = 'auto', rename_format: str = None,
                    progress_callback=None) -> Dict[str, Any]:
        """
        批量修复文件
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            fix_extension: 是否修复扩展名
            fix_time: 是否修复时间
            time_source: 时间来源
            rename_format: 重命名格式
            progress_callback: 进度回调函数
            
        Returns:
            批量修复结果字典
        """
        self._ensure_initialized()
        return self._repair_engine.batch_repair(
            file_list, output_dir, fix_extension, fix_time, 
            time_source, rename_format, progress_callback
        )
    
    def batch_repair_extension(self, file_list: List[str], output_dir: str = None,
                             progress_callback=None) -> Dict[str, Any]:
        """
        批量修复后缀
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            progress_callback: 进度回调函数
            
        Returns:
            批量修复结果字典
        """
        self._ensure_initialized()
        return self._repair_engine.batch_repair_extension(file_list, output_dir, progress_callback)
    
    # ========== 文件处理API ==========
    
    def get_image_files(self, folder_path: str, recursive: bool = False) -> List[str]:
        """
        获取文件夹中的图片文件
        
        Args:
            folder_path: 文件夹路径
            recursive: 是否递归查找
            
        Returns:
            图片文件路径列表
        """
        self._ensure_initialized()
        return self._file_processor.get_image_files(folder_path, recursive)
    
    def rename_files(self, file_list: List[str], pattern: str, 
                    output_dir: str = None, **kwargs) -> Dict[str, Any]:
        """
        批量重命名文件
        
        Args:
            file_list: 文件列表
            pattern: 重命名模式
            output_dir: 输出目录
            **kwargs: 额外参数
            
        Returns:
            重命名结果字典
        """
        self._ensure_initialized()
        return self._file_processor.rename_files(file_list, pattern, output_dir, **kwargs)
    
    def copy_files(self, file_list: List[str], output_dir: str, 
                  preserve_structure: bool = True) -> Dict[str, Any]:
        """
        批量复制文件
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            preserve_structure: 是否保持目录结构
            
        Returns:
            复制结果字典
        """
        self._ensure_initialized()
        return self._file_processor.copy_files(file_list, output_dir, preserve_structure)
    
    def move_files(self, file_list: List[str], output_dir: str,
                  preserve_structure: bool = True) -> Dict[str, Any]:
        """
        批量移动文件
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            preserve_structure: 是否保持目录结构
            
        Returns:
            移动结果字典
        """
        self._ensure_initialized()
        return self._file_processor.move_files(file_list, output_dir, preserve_structure)
    
    def delete_files(self, file_list: List[str], 
                    backup: bool = False, backup_dir: str = None) -> Dict[str, Any]:
        """
        批量删除文件
        
        Args:
            file_list: 文件列表
            backup: 是否备份
            backup_dir: 备份目录
            
        Returns:
            删除结果字典
        """
        self._ensure_initialized()
        return self._file_processor.delete_files(file_list, backup, backup_dir)
    
    # ========== 插件API ==========
    
    def register_plugin(self, plugin: Any) -> None:
        """
        注册插件
        
        Args:
            plugin: 插件实例
        """
        self._ensure_initialized()
        
        if isinstance(plugin, IFormatPlugin):
            self._plugin_manager.register_format_plugin(plugin)
            logger.info(f"注册格式插件: {plugin.format_name}")
        elif isinstance(plugin, IFunctionPlugin):
            self._plugin_manager.register_function_plugin(plugin)
            logger.info(f"注册功能插件: {plugin.plugin_name}")
        elif isinstance(plugin, IExtensionPlugin):
            self._plugin_manager.register_extension_plugin(plugin)
            logger.info(f"注册扩展插件: {plugin.extension_name}")
        else:
            raise ValueError(f"不支持的插件类型: {type(plugin)}")
    
    def get_plugins(self) -> List[Dict[str, Any]]:
        """
        获取所有已注册插件
        
        Returns:
            插件信息列表
        """
        self._ensure_initialized()
        
        plugins = []
        
        # 格式插件
        for plugin in self._plugin_manager.get_format_plugins():
            plugins.append({
                "type": "format",
                "name": plugin.format_name,
                "description": plugin.description,
                "class": plugin.__class__.__name__
            })
        
        # 功能插件
        for plugin in self._plugin_manager.get_function_plugins():
            plugins.append({
                "type": "function",
                "name": plugin.plugin_name,
                "description": plugin.description,
                "class": plugin.__class__.__name__
            })
        
        # 扩展插件
        for plugin in self._plugin_manager.get_extension_plugins():
            plugins.append({
                "type": "extension",
                "name": plugin.extension_name,
                "description": plugin.description,
                "class": plugin.__class__.__name__
            })
        
        return plugins
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        self._ensure_initialized()
        return self._plugin_manager.enable_plugin(plugin_name)
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        self._ensure_initialized()
        return self._plugin_manager.disable_plugin(plugin_name)
    
    # ========== 配置API ==========
    
    def get_config(self, key: str, default=None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        self._ensure_initialized()
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
        """
        self._ensure_initialized()
        self._config.set(key, value)
    
    def save_config(self) -> None:
        """保存配置"""
        self._ensure_initialized()
        self._config.save()
    
    def load_config(self) -> None:
        """加载配置"""
        self._ensure_initialized()
        self._config.load()
    
    # ========== 工具API ==========
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            格式化后的文件大小字符串
        """
        from ..utils.helpers import format_file_size
        return format_file_size(size_bytes)
    
    def format_datetime(self, dt: datetime, format_str: str = None) -> str:
        """
        格式化日期时间
        
        Args:
            dt: 日期时间对象
            format_str: 格式字符串
            
        Returns:
            格式化后的日期时间字符串
        """
        from ..utils.helpers import format_datetime
        if format_str:
            return dt.strftime(format_str)
        return format_datetime(dt)
    
    def parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """
        解析日期时间字符串
        
        Args:
            dt_str: 日期时间字符串
            
        Returns:
            日期时间对象
        """
        from ..utils.helpers import parse_datetime
        return parse_datetime(dt_str)
    
    def get_unique_filename(self, filepath: str) -> str:
        """
        获取唯一文件名
        
        Args:
            filepath: 文件路径
            
        Returns:
            唯一文件名
        """
        from ..utils.helpers import get_unique_filename
        return get_unique_filename(filepath)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名非法字符
        
        Args:
            filename: 文件名
            
        Returns:
            清理后的文件名
        """
        from ..utils.helpers import sanitize_filename
        return sanitize_filename(filename)


# 全局API实例
_api_instance = None


def get_api(config_path: str = None, plugin_dir: str = None) -> KingPhotoAPI:
    """
    获取API单例实例
    
    Args:
        config_path: 配置文件路径
        plugin_dir: 插件目录
        
    Returns:
        KingPhotoAPI实例
    """
    global _api_instance
    
    if _api_instance is None:
        _api_instance = KingPhotoAPI(config_path, plugin_dir)
    
    return _api_instance


def reset_api():
    """重置API单例实例"""
    global _api_instance
    _api_instance = None