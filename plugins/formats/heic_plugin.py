"""
King_photo - HEIC格式插件示例
演示如何创建HEIC格式插件
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.api.plugin_interfaces import IFormatPlugin

# 获取日志记录器
logger = logging.getLogger(__name__)


class HEICFormatPlugin(IFormatPlugin):
    """HEIC格式插件"""
    
    @property
    def format_name(self) -> str:
        """格式名称"""
        return "HEIC"
    
    @property
    def extensions(self) -> List[str]:
        """支持的扩展名列表"""
        return [".heic", ".heif"]
    
    @property
    def magic_numbers(self) -> List[bytes]:
        """文件头魔数列表"""
        return [
            b'\x00\x00\x00\x18ftypheic',
            b'\x00\x00\x00\x18ftypheif',
            b'\x00\x00\x00\x1cmif1heic',
            b'\x00\x00\x00\x20ftypmif1'
        ]
    
    @property
    def description(self) -> str:
        """格式描述"""
        return "HEIC/HEIF图片格式插件，支持EXIF和XMP元数据（需要ExifTool）"
    
    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        """
        读取元数据
        
        Args:
            filepath: 文件路径
            
        Returns:
            元数据字典
        """
        try:
            # HEIC文件需要使用ExifTool读取
            from src.core.metadata_reader import MetadataReader
            return MetadataReader.read_metadata(filepath)
        except Exception as e:
            logger.error(f"读取HEIC元数据失败: {filepath}, 错误: {str(e)}")
            return {"error": str(e)}
    
    def write_metadata(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入元数据
        
        Args:
            filepath: 文件路径
            metadata: 元数据字典
            
        Returns:
            是否成功
        """
        try:
            # HEIC文件需要使用ExifTool写入
            from src.core.metadata_writer import MetadataWriter
            result = MetadataWriter.write_metadata(filepath, metadata)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"写入HEIC元数据失败: {filepath}, 错误: {str(e)}")
            return False
    
    def get_datetime(self, filepath: str) -> Optional[datetime]:
        """
        获取拍摄时间
        
        Args:
            filepath: 文件路径
            
        Returns:
            拍摄时间
        """
        try:
            # HEIC文件需要使用ExifTool获取时间
            from src.core.metadata_reader import MetadataReader
            return MetadataReader.get_datetime(filepath)
        except Exception as e:
            logger.error(f"获取HEIC拍摄时间失败: {filepath}, 错误: {str(e)}")
            return None
    
    def get_capabilities(self) -> Dict[str, bool]:
        """获取插件能力"""
        return {
            "exif_support": True,   # HEIC支持EXIF
            "xmp_support": True,    # HEIC支持XMP
            "iptc_support": False,
            "write_support": True,
            "batch_support": True,
            "needs_exiftool": True  # 需要ExifTool
        }


# 插件元数据
PLUGIN_METADATA = {
    "name": "HEIC Format Plugin",
    "version": "1.0.0",
    "author": "King_photo Team",
    "description": "HEIC/HEIF图片格式插件",
    "format_name": "HEIC"
}