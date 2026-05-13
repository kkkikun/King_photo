"""
King_photo - 元信息读取引擎
统一的元信息读取接口，支持所有格式
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from PIL import Image

from .format_detector import FormatDetector
from .exif_handler import ExifHandler
from .xmp_handler import XmpHandler
from ..utils.exiftool_wrapper import get_exiftool
from ..utils.helpers import get_file_extension, get_file_times


class MetadataReader:
    """元信息读取引擎"""

    @staticmethod
    def read_metadata(filepath: str) -> Dict[str, Any]:
        """读取图片元信息（完整信息）"""
        if not os.path.exists(filepath):
            return {'error': '文件不存在'}

        result = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'extension': get_file_extension(filepath),
            'filesize': os.path.getsize(filepath),
        }

        # 获取文件系统时间
        file_times = get_file_times(filepath)
        result['file_created'] = file_times['created']
        result['file_modified'] = file_times['modified']

        # 获取格式信息
        format_info = FormatDetector.get_format_info(filepath)
        result.update(format_info)

        # 获取图片尺寸
        width, height = MetadataReader._get_image_size(filepath)
        result['width'] = width
        result['height'] = height

        # 根据格式读取元信息
        if format_info['needs_exiftool']:
            # 使用exiftool读取（HEIC、RAW、PSD等）
            MetadataReader._read_with_exiftool(filepath, result)
        else:
            # 使用内置方法读取
            if format_info['supports_exif']:
                MetadataReader._read_exif(filepath, result)

            if format_info['supports_xmp']:
                MetadataReader._read_xmp(filepath, result)

        # 确保datetime字段存在
        if 'datetime' not in result:
            result['datetime'] = None

        return result

    @staticmethod
    def _get_image_size(filepath: str) -> tuple:
        """获取图片尺寸"""
        try:
            with Image.open(filepath) as img:
                return img.size
        except Exception:
            return (0, 0)

    @staticmethod
    def _read_exif(filepath: str, result: Dict[str, Any]):
        """读取EXIF信息"""
        try:
            exif_data = ExifHandler.read_exif(filepath)
            result.update(exif_data)
        except Exception:
            pass

    @staticmethod
    def _read_xmp(filepath: str, result: Dict[str, Any]):
        """读取XMP信息"""
        try:
            ext = get_file_extension(filepath)

            if ext == '.png':
                xmp_data = XmpHandler.read_xmp_from_png(filepath)
            else:
                xmp_data = XmpHandler.read_xmp_from_file(filepath)

            if xmp_data:
                # XMP信息作为补充，不覆盖已有信息
                for key, value in xmp_data.items():
                    if key not in result or result[key] is None:
                        result[key] = value

                # 获取XMP时间
                xmp_dt = XmpHandler.get_datetime(xmp_data)
                if xmp_dt and ('datetime' not in result or result['datetime'] is None):
                    result['datetime'] = xmp_dt

        except Exception:
            pass

    @staticmethod
    def _read_with_exiftool(filepath: str, result: Dict[str, Any]):
        """使用exiftool读取信息"""
        try:
            et = get_exiftool()
            if et.is_available:
                et_info = et.get_basic_info(filepath)
                result.update(et_info)

                et_dt = et.get_datetime(filepath)
                if et_dt:
                    result['datetime'] = et_dt
        except Exception:
            pass

    @staticmethod
    def get_datetime(filepath: str) -> Optional[datetime]:
        """快速获取拍摄时间"""
        if not os.path.exists(filepath):
            return None

        # 检查是否需要exiftool
        if FormatDetector.needs_exiftool(filepath):
            et = get_exiftool()
            if et.is_available:
                return et.get_datetime(filepath)
            return None

        # 尝试EXIF
        if FormatDetector.supports_exif(filepath):
            dt = ExifHandler.get_datetime(filepath)
            if dt:
                return dt

        # 尝试XMP
        if FormatDetector.supports_xmp(filepath):
            try:
                ext = get_file_extension(filepath)
                if ext == '.png':
                    xmp_data = XmpHandler.read_xmp_from_png(filepath)
                else:
                    xmp_data = XmpHandler.read_xmp_from_file(filepath)

                return XmpHandler.get_datetime(xmp_data)
            except Exception:
                pass

        return None

    @staticmethod
    def get_summary(filepath: str) -> Dict[str, Any]:
        """获取元信息摘要（用于列表显示）"""
        metadata = MetadataReader.read_metadata(filepath)

        return {
            'filename': metadata.get('filename', ''),
            'extension': metadata.get('extension', ''),
            'filesize': metadata.get('filesize', 0),
            'width': metadata.get('width', 0),
            'height': metadata.get('height', 0),
            'datetime': metadata.get('datetime'),
            'make': metadata.get('make', ''),
            'model': metadata.get('model', ''),
            'format': metadata.get('format', 'Unknown'),
            'is_consistent': metadata.get('is_consistent', True),
        }

    @staticmethod
    def get_editable_fields(filepath: str) -> Dict[str, Any]:
        """获取可编辑的字段"""
        metadata = MetadataReader.read_metadata(filepath)

        editable = {}

        # 基本可编辑字段
        edit_fields = [
            ('title', '标题'),
            ('description', '描述'),
            ('artist', '作者'),
            ('copyright', '版权'),
            ('make', '相机品牌'),
            ('model', '相机型号'),
            ('software', '软件'),
            ('lens', '镜头型号'),
            ('datetime', '拍摄时间'),
        ]

        for field, label in edit_fields:
            if field in metadata:
                editable[field] = {
                    'value': metadata[field],
                    'label': label,
                }

        return editable
