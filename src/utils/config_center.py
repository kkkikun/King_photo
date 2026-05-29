"""
King_photo - 统一配置中心
提供配置管理、观察者模式和配置验证功能
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
from copy import deepcopy

# 获取日志记录器
logger = logging.getLogger(__name__)


class ConfigCategories:
    """配置分类常量"""
    
    # 窗口配置
    WINDOW = "window"
    WINDOW_WIDTH = "window.width"
    WINDOW_HEIGHT = "window.height"
    WINDOW_X = "window.x"
    WINDOW_Y = "window.y"
    WINDOW_MAXIMIZED = "window.maximized"
    
    # 路径配置
    PATHS = "paths"
    PATHS_LAST_FOLDER = "paths.last_folder"
    PATHS_OUTPUT_DIR = "paths.output_dir"
    
    # 重命名配置
    RENAME = "rename"
    RENAME_DEFAULT_FORMAT = "rename.default_format"
    RENAME_COPY_MODE = "rename.copy_mode"
    
    # 修复配置
    REPAIR = "repair"
    REPAIR_TIME_SOURCE = "repair.time_source"
    REPAIR_FIX_EXTENSION = "repair.fix_extension"
    REPAIR_FIX_TIME = "repair.fix_time"
    REPAIR_RENAME_FORMAT = "repair.rename_format"
    
    # 插件配置
    PLUGIN = "plugin"
    PLUGIN_DIR = "plugin.dir"
    PLUGIN_ENABLED = "plugin.enabled"
    
    # 日志配置
    LOGGING = "logging"
    LOGGING_LEVEL = "logging.level"
    LOGGING_FILE = "logging.file"
    
    # UI配置
    UI = "ui"
    UI_THUMBNAIL_SIZE = "ui.thumbnail_size"
    UI_COLUMNS = "ui.columns"
    UI_ASYNC_THRESHOLD = "ui.async_threshold"


class ConfigObserver:
    """配置观察者接口"""
    
    def on_config_changed(self, key: str, value: Any, old_value: Any) -> None:
        """
        配置变更回调
        
        Args:
            key: 配置键
            value: 新值
            old_value: 旧值
        """
        pass


class ConfigCenter:
    """统一配置中心"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置中心
        
        Args:
            config_path: 配置文件路径，可选
        """
        if config_path is None:
            # 使用程序运行目录下的config文件夹
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'config',
                'settings.json'
            )
        
        self._config_path = config_path
        self._config = {}
        self._observers: List[ConfigObserver] = []
        self._validators: Dict[str, Callable] = {}
        
        # 加载配置
        self._load_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点号分隔的层级（如'window.width'）
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any, notify: bool = True) -> bool:
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
            notify: 是否通知观察者
            
        Returns:
            是否设置成功
        """
        try:
            # 验证值
            if key in self._validators:
                if not self._validators[key](value):
                    logger.warning(f"配置值验证失败: {key} = {value}")
                    return False
            
            keys = key.split('.')
            config = self._config
            
            # 遍历到倒数第二层
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 获取旧值
            old_value = config.get(keys[-1])
            
            # 设置新值
            config[keys[-1]] = value
            
            # 通知观察者
            if notify and old_value != value:
                self._notify_observers(key, value, old_value)
            
            return True
        except Exception as e:
            logger.error(f"设置配置值失败: {key} = {value}, 错误: {str(e)}")
            return False
    
    def save(self) -> bool:
        """保存配置"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置文件已保存: {self._config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"配置文件已加载: {self._config_path}")
            else:
                self._config = self._get_default_config()
                logger.info("使用默认配置")
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "window": {
                "width": 1200,
                "height": 800,
                "maximized": False
            },
            "paths": {
                "last_folder": "",
                "output_dir": ""
            },
            "rename": {
                "default_format": "{datetime}",
                "copy_mode": True
            },
            "repair": {
                "time_source": "auto",
                "fix_extension": True,
                "fix_time": True,
                "rename_format": "{datetime}"
            },
            "plugin": {
                "dir": "plugins",
                "enabled": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/king_photo.log"
            },
            "ui": {
                "thumbnail_size": 120,
                "columns": 4,
                "async_threshold": 20
            }
        }
    
    def add_observer(self, observer: ConfigObserver) -> None:
        """添加配置观察者"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: ConfigObserver) -> None:
        """移除配置观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, key: str, value: Any, old_value: Any) -> None:
        """通知观察者配置变更"""
        for observer in self._observers:
            try:
                observer.on_config_changed(key, value, old_value)
            except Exception as e:
                logger.error(f"通知观察者失败: {str(e)}")
    
    def add_validator(self, key: str, validator: Callable[[Any], bool]) -> None:
        """
        添加配置验证器
        
        Args:
            key: 配置键
            validator: 验证函数，接受值返回是否有效
        """
        self._validators[key] = validator
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return deepcopy(self._config)
    
    def reset(self) -> bool:
        """重置为默认配置"""
        self._config = self._get_default_config()
        return self.save()
    
    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return self._config_path
    
    def set_config_path(self, config_path: str) -> None:
        """设置配置文件路径"""
        self._config_path = config_path
        self._load_config()


# 全局配置中心实例
_config_center: Optional[ConfigCenter] = None


def get_config_center(config_path: str = None) -> ConfigCenter:
    """
    获取全局配置中心实例
    
    Args:
        config_path: 配置文件路径，可选
        
    Returns:
        配置中心实例
    """
    global _config_center
    if _config_center is None:
        _config_center = ConfigCenter(config_path)
    return _config_center


def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值的快捷方法
    
    Args:
        key: 配置键
        default: 默认值
        
    Returns:
        配置值
    """
    return get_config_center().get(key, default)


def set_config(key: str, value: Any, notify: bool = True) -> bool:
    """
    设置配置值的快捷方法
    
    Args:
        key: 配置键
        value: 配置值
        notify: 是否通知观察者
        
    Returns:
        是否设置成功
    """
    return get_config_center().set(key, value, notify)


def save_config() -> bool:
    """保存配置的快捷方法"""
    return get_config_center().save()