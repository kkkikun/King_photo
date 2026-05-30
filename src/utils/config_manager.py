"""
King_photo - 配置管理模块
提供配置文件的读写功能
"""

import json
import logging
import os
from typing import Any, Dict, Optional


# 获取日志记录器
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    # 窗口设置
    'window': {
        'width': 1200,
        'height': 800,
        'maximized': False,
    },

    # 路径设置
    'paths': {
        'last_folder': '',
        'output_dir': '',
    },

    # 重命名设置
    'rename': {
        'format': '{datetime}',
        'copy_mode': True,
    },

    # 修复设置
    'repair': {
        'fix_extension': True,
        'fix_time': True,
        'rename_format': '{datetime}',
    },

    # 界面设置
    'ui': {
        'thumbnail_size': 120,
        'columns': 4,
        'async_threshold': 20,
    },
}


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为程序运行目录下的config文件夹
        """
        if config_dir is None:
            # 使用程序运行目录下的config文件夹
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'config'
            )

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'settings.json')
        self.config = {}

        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)

        # 加载配置
        self.load()

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # 合并默认配置和加载的配置
                self.config = self._merge_config(DEFAULT_CONFIG, loaded_config)
                logger.info(f"配置文件已加载: {self.config_file}")
            else:
                # 使用默认配置
                self.config = DEFAULT_CONFIG.copy()
                logger.info("使用默认配置")

        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            self.config = DEFAULT_CONFIG.copy()

        return self.config

    def save(self) -> bool:
        """
        保存配置文件

        Returns:
            是否保存成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

            logger.info(f"配置文件已保存: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的层级路径（如 'window.width'）
            default: 默认值

        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self.config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

        except Exception:
            return default

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的层级路径（如 'window.width'）
            value: 配置值

        Returns:
            是否设置成功
        """
        try:
            keys = key.split('.')
            config = self.config

            # 遍历到倒数第二层
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 设置值
            config[keys[-1]] = value
            return True

        except Exception as e:
            logger.error(f"设置配置值失败: {key} = {value}, 错误: {str(e)}")
            return False

    def _merge_config(self, default: Dict, loaded: Dict) -> Dict:
        """
        合并配置（保留默认配置的结构，用加载的配置覆盖值）

        Args:
            default: 默认配置
            loaded: 加载的配置

        Returns:
            合并后的配置
        """
        result = default.copy()

        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并字典
                result[key] = self._merge_config(result[key], value)
            else:
                # 直接覆盖
                result[key] = value

        return result

    def reset(self) -> bool:
        """
        重置为默认配置

        Returns:
            是否重置成功
        """
        self.config = DEFAULT_CONFIG.copy()
        return self.save()


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的快捷方法"""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> bool:
    """设置配置值的快捷方法"""
    return get_config_manager().set(key, value)


def save_config() -> bool:
    """保存配置的快捷方法"""
    return get_config_manager().save()