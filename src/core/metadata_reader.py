"""
King_photo - 元信息读取引擎
统一的元信息读取接口，支持所有格式
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from PIL import Image

from .format_detector import FormatDetector
from .exif_handler import ExifHandler
from .xmp_handler import XmpHandler
from ..utils.exiftool_wrapper import get_exiftool
from ..utils.helpers import get_file_extension, get_file_times

# 获取日志记录器
logger = logging.getLogger(__name__)


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
        except Exception as e:
            logger.debug(f"获取图片尺寸失败: {filepath}, 错误: {str(e)}")
            return (0, 0)

    @staticmethod
    def _read_exif(filepath: str, result: Dict[str, Any]):
        """读取EXIF信息"""
        try:
            exif_data = ExifHandler.read_exif(filepath)
            result.update(exif_data)
        except Exception as e:
            logger.warning(f"读取EXIF补充信息失败: {filepath}, 错误: {str(e)}")

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

        except Exception as e:
            logger.warning(f"读取XMP补充信息失败: {filepath}, 错误: {str(e)}")

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
        except Exception as e:
            logger.warning(f"ExifTool读取信息失败: {filepath}, 错误: {str(e)}")

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
            except Exception as e:
                logger.debug(f"获取XMP时间失败: {filepath}, 错误: {str(e)}")

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
        """获取可编辑的字段（根据格式适配）"""
        metadata = MetadataReader.read_metadata(filepath)
        format_info = FormatDetector.get_format_info(filepath)
        
        editable = {}
        
        # 添加格式信息，便于UI显示
        editable['_format_info'] = {
            'format': format_info.get('format', 'Unknown'),
            'supports_exif': format_info.get('supports_exif', False),
            'supports_xmp': format_info.get('supports_xmp', False),
            'needs_exiftool': format_info.get('needs_exiftool', False),
            'extension': metadata.get('extension', ''),
        }
        
        # 根据格式支持情况确定可编辑字段
        supports_exif = format_info.get('supports_exif', False)
        supports_xmp = format_info.get('supports_xmp', False)
        needs_exiftool = format_info.get('needs_exiftool', False)
        
        # 1. 基本文件信息（所有格式都可显示，但不可编辑）
        basic_fields = [
            ('filename', '文件名', False),
            ('extension', '扩展名', False),
            ('filesize', '文件大小', False),
            ('width', '宽度', False),
            ('height', '高度', False),
            ('format', '格式', False),
        ]
        
        # 文件时间字段（所有格式都可显示，可编辑）
        time_fields = [
            ('file_modified', '修改时间', True),
            ('file_created', '创建时间', True),
        ]
        
        for field, label, editable_flag in basic_fields:
            if field in metadata:
                editable[field] = {
                    'value': metadata[field],
                    'label': label,
                    'editable': editable_flag,
                    'category': 'basic',
                }
        
        # 添加时间字段
        for field, label, editable_flag in time_fields:
            value = metadata.get(field, '')
            if value is None:
                value = ''
            editable[field] = {
                'value': value,
                'label': label,
                'editable': editable_flag,
                'category': 'time',
            }
        
        # 2. 添加所有可能编辑的字段
        
        # 通用XMP字段
        xmp_editable_fields = [
            ('title', '标题', True),
            ('description', '描述', True),
            ('artist', '作者', True),
            ('copyright', '版权', True),
        ]
        
        for field, label, editable_flag in xmp_editable_fields:
            # 如果字段不存在，设置默认值
            value = metadata.get(field, '')
            if value is None:
                value = ''
            
            # 根据格式设置可编辑标志
            field_editable = editable_flag and supports_xmp
            
            editable[field] = {
                'value': value,
                'label': label,
                'editable': field_editable,
                'category': 'xmp',
            }
        
        # EXIF字段
        exif_editable_fields = [
            ('make', '相机品牌', True),
            ('model', '相机型号', True),
            ('software', '软件', True),
            ('lens', '镜头型号', True),
            ('datetime', '拍摄时间', True),
            ('exposure_time', '曝光时间', False),
            ('fnumber', '光圈', False),
            ('iso', 'ISO', False),
            ('focal_length', '焦距', False),
            ('orientation', '方向', False),
        ]
        
        for field, label, editable_flag in exif_editable_fields:
            # 如果字段不存在，设置默认值
            value = metadata.get(field, '')
            if value is None:
                value = ''
            
            # 根据格式设置可编辑标志
            field_editable = editable_flag and supports_exif
            
            editable[field] = {
                'value': value,
                'label': label,
                'editable': field_editable,
                'category': 'exif',
            }
        
        # 3. 对于需要exiftool的格式（HEIF、RAW等），所有字段都可编辑
        if needs_exiftool:
            # 确保所有EXIF和XMP字段都标记为可编辑
            for field_key, field_info in editable.items():
                if field_key.startswith('_'):
                    continue
                if field_info.get('category') in ['exif', 'xmp']:
                    field_info['editable'] = True
        
        return editable
