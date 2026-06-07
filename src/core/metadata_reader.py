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
from ..api.interfaces import IMetadataReader

# 获取日志记录器
logger = logging.getLogger(__name__)


class MetadataReader(IMetadataReader):
    """元信息读取引擎，实现IMetadataReader接口"""

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
        if format_info.get('needs_exiftool', False):
            # 使用exiftool读取（HEIC、RAW、PSD等）
            MetadataReader._read_with_exiftool(filepath, result)
        else:
            # 使用内置方法读取
            if format_info.get('supports_exif', False):
                MetadataReader._read_exif(filepath, result)

            if format_info.get('supports_xmp', False):
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
        """获取可编辑的字段（基于 editable_fields.json 数据库适配）"""
        from ..utils.format_field_manager import get_field_manager

        metadata = MetadataReader.read_metadata(filepath)
        format_info = FormatDetector.get_format_info(filepath)
        format_name = format_info.get('format', 'Unknown')

        fm = get_field_manager()
        writable = fm.get_writable_fields(format_name)

        editable = {}

        # 添加格式信息，便于UI显示
        editable['_format_info'] = {
            'format': format_name,
            'format_label': fm.get_format_label(format_name),
            'supports_exif': format_info.get('supports_exif', False),
            'supports_xmp': format_info.get('supports_xmp', False),
            'needs_exiftool': format_info.get('needs_exiftool', False),
            'write_method': fm.get_write_method(format_name),
            'note': fm._resolve(format_name).get('note', '') if fm._resolve(format_name) else '',
        }

        # 1. 基本文件信息（所有格式显示，不可编辑）
        basic_fields = [
            ('filename', '文件名'),
            ('extension', '扩展名'),
            ('filesize', '文件大小'),
            ('width', '宽度'),
            ('height', '高度'),
            ('format', '格式'),
        ]
        for field, label in basic_fields:
            if field in metadata:
                editable[field] = {
                    'value': metadata[field],
                    'label': label,
                    'editable': False,
                    'category': 'basic',
                }

        # 文件系统时间（所有格式可显示+可编辑）
        for field, label in [('file_modified', '修改时间'), ('file_created', '创建时间')]:
            editable[field] = {
                'value': metadata.get(field, '') or '',
                'label': label,
                'editable': True,
                'category': 'time',
            }

        # 2. 根据数据库适配字段
        # descriptive → category: 'xmp'
        # camera → category: 'exif'
        # time → category: 'exif'
        # technical → category: 'exif', 但 writable=false

        field_labels = {
            'title': '标题', 'description': '描述', 'artist': '作者', 'copyright': '版权',
            'make': '相机品牌', 'model': '相机型号', 'software': '软件', 'lens': '镜头型号',
            'datetime': '拍摄时间', 'datetime_original': '原始时间',
            'datetime_digitized': '数字化时间', 'creation_time': '创建时间',
            'exposure_time': '曝光时间', 'fnumber': '光圈', 'iso': 'ISO',
            'focal_length': '焦距', 'orientation': '方向',
        }

        category_map = {
            'descriptive': 'xmp',
            'camera': 'exif',
            'time': 'exif',
            'technical': 'exif',
        }

        for category_name, fields in writable.items():
            cat = category_map.get(category_name, 'exif')
            for field_name, field_def in fields.items():
                is_writable = field_def.get('writable', True) is not False
                value = metadata.get(field_name, '')
                if value is None:
                    value = ''

                editable[field_name] = {
                    'value': value,
                    'label': field_labels.get(field_name, field_name),
                    'editable': is_writable,
                    'category': cat,
                }

        return editable
    
    @staticmethod
    def read_exif(filepath: str) -> Dict[str, Any]:
        """
        读取EXIF数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            EXIF数据字典
        """
        try:
            return ExifHandler.read_exif(filepath)
        except Exception as e:
            logger.warning(f"读取EXIF失败: {filepath}, 错误: {str(e)}")
            return {}
    
    @staticmethod
    def read_xmp(filepath: str) -> Dict[str, Any]:
        """
        读取XMP数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            XMP数据字典
        """
        try:
            ext = get_file_extension(filepath)
            
            if ext == '.png':
                xmp_data = XmpHandler.read_xmp_from_png(filepath)
            else:
                xmp_data = XmpHandler.read_xmp_from_file(filepath)
            
            return xmp_data or {}
        except Exception as e:
            logger.warning(f"读取XMP失败: {filepath}, 错误: {str(e)}")
            return {}
    
    @staticmethod
    def read_iptc(filepath: str) -> Dict[str, Any]:
        """
        读取IPTC数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            IPTC数据字典
        """
        try:
            # 尝试使用exiftool读取IPTC数据
            et = get_exiftool()
            if et.is_available:
                # ExifTool可以读取IPTC数据
                basic_info = et.get_basic_info(filepath)
                # 提取IPTC相关字段
                iptc_data = {}
                iptc_fields = ['Title', 'Description', 'Author', 'Copyright', 'Keywords']
                for field in iptc_fields:
                    if field in basic_info:
                        iptc_data[field.lower()] = basic_info[field]
                return iptc_data
            return {}
        except Exception as e:
            logger.warning(f"读取IPTC失败: {filepath}, 错误: {str(e)}")
            return {}
    
    @staticmethod
    def read_with_exiftool(filepath: str) -> Dict[str, Any]:
        """
        使用ExifTool读取元数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            ExifTool读取的元数据字典
        """
        try:
            et = get_exiftool()
            if et.is_available:
                return et.get_basic_info(filepath)
            return {}
        except Exception as e:
            logger.warning(f"使用ExifTool读取失败: {filepath}, 错误: {str(e)}")
            return {}
