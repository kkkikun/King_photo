"""
King_photo - 格式字段管理器
加载 editable_fields.json，提供每个格式的可编辑字段查询
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FormatFieldManager:
    """格式字段管理器
    
    基于 ExifTool 13.59 官方格式支持表，为每个图片格式定义：
    - 哪些字段可写
    - 写入方式（piexif / exiftool / xmp）
    - 字段标签映射
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self._data: Dict[str, Any] = {}
        self._load()
        self._loaded = True

    def _load(self):
        """加载 editable_fields.json"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "editable_fields.json"
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            logger.info(f"格式字段配置加载完成: {len(self._data) - 1} 个格式")
        except Exception as e:
            logger.warning(f"加载 editable_fields.json 失败: {e}，使用空配置")
            self._data = {}

    def _resolve(self, format_name: str) -> Optional[Dict[str, Any]]:
        """获取格式配置，支持 _inherit 继承"""
        if format_name not in self._data:
            return None

        config = self._data[format_name]
        if "_meta" in config:
            return None  # skip meta block

        # 支持继承（如 TIFF → JPEG）
        parent = config.get("_inherit")
        if parent:
            parent_config = self._resolve(parent)
            if parent_config:
                merged = parent_config.copy()
                for key, value in config.items():
                    if key != "_inherit" and key in self._data[format_name]:
                        if isinstance(value, dict) and isinstance(merged.get(key), dict):
                            merged[key] = {**merged.get(key, {}), **value}
                        else:
                            merged[key] = value
                return merged
        return config

    def get_writable_fields(self, format_name: str) -> Dict[str, Any]:
        """获取指定格式的可写字段定义

        Returns:
            {
                'descriptive': {field: {field, piexif_tag, exiftool_tag, xmp_tag}},
                'camera':      {...},
                'time':        {...},
                'technical':   {...}
            }
        """
        config = self._resolve(format_name)
        if not config:
            return {}
        return config.get("writable", {})

    def get_field_info(self, format_name: str, field_name: str) -> Optional[Dict[str, Any]]:
        """获取单个字段的写入信息（含标签映射）"""
        writable = self.get_writable_fields(format_name)
        for category, fields in writable.items():
            if field_name in fields:
                return fields[field_name]
        return None

    def is_field_writable(self, format_name: str, field_name: str) -> bool:
        """检查字段在该格式下是否可写"""
        info = self.get_field_info(format_name, field_name)
        if info is None:
            # 未定义 = 不可写
            return False
        # 显式标记 writable=false（如技术参数）
        if info.get("writable") is False:
            return False
        return True

    def get_write_method(self, format_name: str) -> Optional[str]:
        """获取格式的推荐写入方式"""
        config = self._resolve(format_name)
        if not config:
            return None
        return config.get("write_method")

    def supports_exif_write(self, format_name: str) -> bool:
        config = self._resolve(format_name)
        if not config:
            return False
        return config.get("exif_native", False)

    def supports_xmp_write(self, format_name: str) -> bool:
        config = self._resolve(format_name)
        if not config:
            return False
        return config.get("xmp_support", False)

    def get_format_label(self, format_name: str) -> str:
        config = self._resolve(format_name)
        if not config:
            return format_name
        return config.get("label", format_name)

    def get_all_writable_field_names(self, format_name: str) -> list:
        """获取某格式所有可写字段名（扁平列表，用于 UI 和 writer）"""
        writable = self.get_writable_fields(format_name)
        names = []
        for category, fields in writable.items():
            for field_name, info in fields.items():
                if info.get("writable") is not False:
                    names.append(field_name)
        return names


def get_field_manager() -> FormatFieldManager:
    """获取 FormatFieldManager 单例"""
    return FormatFieldManager()
