"""
King_photo - 插件管理器
负责插件的加载、注册、管理和执行
"""

import os
import sys
import logging
import importlib.util
import json
from typing import Optional, Dict, Any, List, Type

from .plugin_interfaces import (
    IFormatPlugin,
    IFunctionPlugin,
    IExtensionPlugin,
    PluginMetadata,
    PluginLoadError,
    PluginExecutionError,
    PluginDependencyError,
    PluginConfigError
)

# 获取日志记录器
logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_config_path: str = None):
        """
        初始化插件管理器
        
        Args:
            plugin_config_path: 插件配置文件路径
        """
        self._format_plugins = {}  # 格式插件：{格式名: 插件实例}
        self._function_plugins = {}  # 功能插件：{插件名: 插件实例}
        self._extension_plugins = {}  # 扩展插件：{扩展名: 插件实例}
        
        self._plugin_configs = {}  # 插件配置
        self._plugin_metadata = {}  # 插件元数据
        self._loaded_plugins = set()  # 已加载的插件
        
        # 插件配置文件路径
        self._config_path = plugin_config_path or "plugin_config.json"
        
        # 加载插件配置
        self._load_plugin_config()
        
        logger.info("插件管理器初始化完成")
    
    def _load_plugin_config(self):
        """加载插件配置"""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._plugin_configs = json.load(f)
                logger.info(f"插件配置加载完成: {self._config_path}")
            except Exception as e:
                logger.warning(f"加载插件配置失败: {str(e)}")
                self._plugin_configs = {}
    
    def _save_plugin_config(self):
        """保存插件配置"""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._plugin_configs, f, indent=2, ensure_ascii=False)
            logger.debug(f"插件配置保存完成: {self._config_path}")
        except Exception as e:
            logger.warning(f"保存插件配置失败: {str(e)}")
    
    def load_plugins(self, plugin_dir: str) -> None:
        """
        加载插件目录中的所有插件
        
        Args:
            plugin_dir: 插件目录路径
        """
        if not os.path.exists(plugin_dir):
            logger.warning(f"插件目录不存在: {plugin_dir}")
            return
        
        # 加载格式插件
        formats_dir = os.path.join(plugin_dir, "formats")
        if os.path.exists(formats_dir):
            self._load_plugins_from_dir(formats_dir, "format")
        
        # 加载功能插件
        functions_dir = os.path.join(plugin_dir, "functions")
        if os.path.exists(functions_dir):
            self._load_plugins_from_dir(functions_dir, "function")
        
        # 加载扩展插件
        extensions_dir = os.path.join(plugin_dir, "extensions")
        if os.path.exists(extensions_dir):
            self._load_plugins_from_dir(extensions_dir, "extension")
        
        logger.info(f"插件加载完成: 格式插件 {len(self._format_plugins)} 个, "
                   f"功能插件 {len(self._function_plugins)} 个, "
                   f"扩展插件 {len(self._extension_plugins)} 个")
    
    def _load_plugins_from_dir(self, directory: str, plugin_type: str) -> None:
        """
        从目录加载插件
        
        Args:
            directory: 目录路径
            plugin_type: 插件类型
        """
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_path = os.path.join(directory, filename)
                try:
                    self._load_plugin_file(plugin_path, plugin_type)
                except Exception as e:
                    logger.error(f"加载插件失败 {filename}: {str(e)}")
    
    def _load_plugin_file(self, plugin_path: str, plugin_type: str) -> None:
        """
        加载插件文件
        
        Args:
            plugin_path: 插件文件路径
            plugin_type: 插件类型
        """
        # 创建模块规范
        spec = importlib.util.spec_from_file_location(
            f"king_photo.plugins.{plugin_type}.{os.path.basename(plugin_path)}",
            plugin_path
        )
        
        if spec is None or spec.loader is None:
            raise PluginLoadError(plugin_path, "无法创建模块规范")
        
        # 加载模块
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        
        # 查找插件类
        plugin_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                attr.__name__ != 'ABC' and
                not attr_name.startswith('_')):
                
                # 检查是否是正确的插件类型
                if plugin_type == "format" and issubclass(attr, IFormatPlugin):
                    plugin_class = attr
                    break
                elif plugin_type == "function" and issubclass(attr, IFunctionPlugin):
                    plugin_class = attr
                    break
                elif plugin_type == "extension" and issubclass(attr, IExtensionPlugin):
                    plugin_class = attr
                    break
        
        if plugin_class is None:
            raise PluginLoadError(plugin_path, f"未找到 {plugin_type} 类型的插件类")
        
        # 创建插件实例
        plugin_instance = plugin_class()
        
        # 获取插件元数据
        metadata = self._extract_plugin_metadata(plugin_instance, plugin_type)
        
        # 检查是否启用
        plugin_name = metadata.name
        if not self._is_plugin_enabled(plugin_name):
            logger.info(f"插件已禁用: {plugin_name}")
            return
        
        # 注册插件
        self._register_plugin(plugin_instance, plugin_type, metadata)
        
        self._loaded_plugins.add(plugin_path)
        logger.info(f"插件加载成功: {plugin_name}")
    
    def _extract_plugin_metadata(self, plugin: Any, plugin_type: str) -> PluginMetadata:
        """
        提取插件元数据
        
        Args:
            plugin: 插件实例
            plugin_type: 插件类型
            
        Returns:
            插件元数据
        """
        if plugin_type == "format":
            return PluginMetadata(
                name=plugin.format_name,
                version=getattr(plugin, 'version', '1.0.0'),
                author=getattr(plugin, 'author', 'Unknown'),
                description=plugin.description,
                plugin_type="format"
            )
        elif plugin_type == "function":
            return PluginMetadata(
                name=plugin.plugin_name,
                version=plugin.version,
                author=getattr(plugin, 'author', 'Unknown'),
                description=plugin.description,
                plugin_type="function"
            )
        elif plugin_type == "extension":
            return PluginMetadata(
                name=plugin.extension_name,
                version=getattr(plugin, 'version', '1.0.0'),
                author=getattr(plugin, 'author', 'Unknown'),
                description=plugin.description,
                plugin_type="extension"
            )
        else:
            raise ValueError(f"未知的插件类型: {plugin_type}")
    
    def _is_plugin_enabled(self, plugin_name: str) -> bool:
        """
        检查插件是否启用
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否启用
        """
        # 默认启用
        return self._plugin_configs.get(plugin_name, {}).get("enabled", True)
    
    def _register_plugin(self, plugin: Any, plugin_type: str, metadata: PluginMetadata) -> None:
        """
        注册插件
        
        Args:
            plugin: 插件实例
            plugin_type: 插件类型
            metadata: 插件元数据
        """
        if plugin_type == "format":
            self._format_plugins[metadata.name] = plugin
        elif plugin_type == "function":
            self._function_plugins[metadata.name] = plugin
        elif plugin_type == "extension":
            self._extension_plugins[metadata.name] = plugin
        
        # 保存元数据
        self._plugin_metadata[metadata.name] = metadata
    
    def register_format_plugin(self, plugin: IFormatPlugin) -> None:
        """
        注册格式插件
        
        Args:
            plugin: 格式插件实例
        """
        metadata = PluginMetadata(
            name=plugin.format_name,
            version=getattr(plugin, 'version', '1.0.0'),
            author=getattr(plugin, 'author', 'Unknown'),
            description=plugin.description,
            plugin_type="format"
        )
        
        self._register_plugin(plugin, "format", metadata)
        logger.info(f"注册格式插件: {plugin.format_name}")
    
    def register_function_plugin(self, plugin: IFunctionPlugin) -> None:
        """
        注册功能插件
        
        Args:
            plugin: 功能插件实例
        """
        metadata = PluginMetadata(
            name=plugin.plugin_name,
            version=plugin.version,
            author=getattr(plugin, 'author', 'Unknown'),
            description=plugin.description,
            plugin_type="function"
        )
        
        self._register_plugin(plugin, "function", metadata)
        logger.info(f"注册功能插件: {plugin.plugin_name}")
    
    def register_extension_plugin(self, plugin: IExtensionPlugin) -> None:
        """
        注册扩展插件
        
        Args:
            plugin: 扩展插件实例
        """
        metadata = PluginMetadata(
            name=plugin.extension_name,
            version=getattr(plugin, 'version', '1.0.0'),
            author=getattr(plugin, 'author', 'Unknown'),
            description=plugin.description,
            plugin_type="extension"
        )
        
        self._register_plugin(plugin, "extension", metadata)
        logger.info(f"注册扩展插件: {plugin.extension_name}")
    
    def get_format_plugin(self, format_name: str) -> Optional[IFormatPlugin]:
        """
        获取格式插件
        
        Args:
            format_name: 格式名称
            
        Returns:
            格式插件实例
        """
        return self._format_plugins.get(format_name)
    
    def get_format_plugin_by_file(self, filepath: str) -> Optional[IFormatPlugin]:
        """
        根据文件获取格式插件
        
        Args:
            filepath: 文件路径
            
        Returns:
            格式插件实例
        """
        ext = os.path.splitext(filepath)[1].lower()
        
        for plugin in self._format_plugins.values():
            if ext in plugin.extensions:
                return plugin
        
        return None
    
    def get_function_plugin(self, plugin_name: str) -> Optional[IFunctionPlugin]:
        """
        获取功能插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            功能插件实例
        """
        return self._function_plugins.get(plugin_name)
    
    def get_extension_plugin(self, plugin_name: str) -> Optional[IExtensionPlugin]:
        """
        获取扩展插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            扩展插件实例
        """
        return self._extension_plugins.get(plugin_name)
    
    def get_format_plugins(self) -> List[IFormatPlugin]:
        """获取所有格式插件"""
        return list(self._format_plugins.values())
    
    def get_function_plugins(self) -> List[IFunctionPlugin]:
        """获取所有功能插件"""
        return list(self._function_plugins.values())
    
    def get_extension_plugins(self) -> List[IExtensionPlugin]:
        """获取所有扩展插件"""
        return list(self._extension_plugins.values())
    
    def get_all_plugins(self) -> List[Any]:
        """获取所有插件"""
        plugins = []
        plugins.extend(self._format_plugins.values())
        plugins.extend(self._function_plugins.values())
        plugins.extend(self._extension_plugins.values())
        return plugins
    
    def get_supported_formats(self) -> List[str]:
        """获取所有支持的格式"""
        formats = []
        for plugin in self._format_plugins.values():
            formats.extend(plugin.extensions)
        return list(set(formats))
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        if plugin_name not in self._plugin_configs:
            self._plugin_configs[plugin_name] = {}
        
        self._plugin_configs[plugin_name]["enabled"] = True
        self._save_plugin_config()
        
        logger.info(f"启用插件: {plugin_name}")
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功
        """
        if plugin_name not in self._plugin_configs:
            self._plugin_configs[plugin_name] = {}
        
        self._plugin_configs[plugin_name]["enabled"] = False
        self._save_plugin_config()
        
        # 从注册表中移除
        if plugin_name in self._format_plugins:
            del self._format_plugins[plugin_name]
        elif plugin_name in self._function_plugins:
            del self._function_plugins[plugin_name]
        elif plugin_name in self._extension_plugins:
            del self._extension_plugins[plugin_name]
        
        logger.info(f"禁用插件: {plugin_name}")
        return True
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """
        获取插件元数据
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件元数据
        """
        return self._plugin_metadata.get(plugin_name)
    
    def get_all_plugin_metadata(self) -> Dict[str, PluginMetadata]:
        """获取所有插件元数据"""
        return self._plugin_metadata.copy()
    
    def execute_function_plugin(self, plugin_name: str, file_list: List[str], 
                               **kwargs) -> Dict[str, Any]:
        """
        执行功能插件
        
        Args:
            plugin_name: 插件名称
            file_list: 文件列表
            **kwargs: 额外参数
            
        Returns:
            执行结果
        """
        plugin = self.get_function_plugin(plugin_name)
        if plugin is None:
            raise PluginExecutionError(plugin_name, "插件不存在")
        
        if not plugin.is_available():
            raise PluginExecutionError(plugin_name, "插件不可用")
        
        try:
            result = plugin.execute(file_list, **kwargs)
            logger.info(f"功能插件执行完成: {plugin_name}")
            return result
        except Exception as e:
            logger.error(f"功能插件执行失败: {plugin_name}, 错误: {str(e)}")
            raise PluginExecutionError(plugin_name, str(e))
    
    def get_extension_hooks(self, target_module: str) -> List[IExtensionPlugin]:
        """
        获取目标模块的扩展钩子
        
        Args:
            target_module: 目标模块名称
            
        Returns:
            扩展插件列表
        """
        hooks = []
        
        for plugin in self._extension_plugins.values():
            if plugin.target_module == target_module and plugin.is_enabled():
                hooks.append(plugin)
        
        # 按优先级排序
        hooks.sort(key=lambda x: x.priority)
        
        return hooks
    
    def clear_all_plugins(self) -> None:
        """清除所有插件"""
        self._format_plugins.clear()
        self._function_plugins.clear()
        self._extension_plugins.clear()
        self._plugin_metadata.clear()
        self._loaded_plugins.clear()
        
        logger.info("所有插件已清除")