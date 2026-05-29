"""
King_photo - 元信息写入引擎
统一的元信息写入接口
"""

import logging
import os
import shutil
from datetime import datetime
from typing import Optional, Dict, Any

from .format_detector import FormatDetector
from .exif_handler import ExifHandler
from .xmp_handler import XmpHandler
from ..utils.exiftool_wrapper import get_exiftool
from ..utils.helpers import get_file_extension, get_unique_filename
from ..api.interfaces import IMetadataWriter

# 获取日志记录器
logger = logging.getLogger(__name__)


class MetadataWriter(IMetadataWriter):
    """元信息写入引擎，实现IMetadataWriter接口"""

    @staticmethod
    def write_metadata(filepath: str, metadata: Dict[str, Any], copy_mode: bool = True, output_dir: str = None) -> Dict[str, Any]:
        """
        写入元信息

        Args:
            filepath: 源文件路径
            metadata: 要写入的元信息
            copy_mode: 是否复制模式（True=复制后修改，False=直接修改原文件）
            output_dir: 输出目录（copy_mode=True时使用）

        Returns:
            操作结果 {'success': bool, 'output_path': str, 'message': str}
        """
        if not os.path.exists(filepath):
            return {'success': False, 'output_path': None, 'message': '文件不存在'}

        # 检查文件是否真的是图片格式
        is_image, image_check_msg = FormatDetector.is_truly_image(filepath)
        if not is_image:
            logger.warning(f"文件不是真正的图片格式: {filepath}, {image_check_msg}")
            return {
                'success': False,
                'output_path': None,
                'message': f'文件不是图片格式: {image_check_msg}',
                'skipped': True,
                'error_type': 'not_image_file',
                'error_detail': image_check_msg
            }

        # 获取格式信息
        format_info = FormatDetector.get_format_info(filepath)

        # 确定输出路径
        if copy_mode:
            if output_dir is None:
                output_dir = os.path.dirname(filepath)
            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(output_dir, os.path.basename(filepath))
            output_path = get_unique_filename(output_path)

            # 复制文件
            try:
                shutil.copy2(filepath, output_path)
            except Exception as e:
                return {'success': False, 'output_path': None, 'message': f'复制文件失败: {str(e)}'}
        else:
            output_path = filepath

        # 写入元信息
        success = False

        # 获取文件扩展名
        ext = os.path.splitext(output_path)[1].lower()
        
        # 对于PNG文件，优先使用exiftool写入，因为PIL写入的XMP可能不兼容Windows显示
        if ext == '.png':
            logger.info(f"PNG文件，优先使用exiftool写入: {output_path}")
            success = MetadataWriter._write_with_exiftool(output_path, metadata)
            # 如果exiftool写入失败，尝试使用PIL写入作为回退
            if not success:
                logger.warning(f"exiftool写入PNG失败，尝试使用PIL写入: {output_path}")
                success = XmpHandler.write_xmp(output_path, metadata)
        elif format_info.get('needs_exiftool', False):
            # 使用exiftool写入
            success = MetadataWriter._write_with_exiftool(output_path, metadata)
        else:
            # 使用内置方法写入
            if format_info.get('supports_exif', False):
                success = MetadataWriter._write_exif(output_path, metadata)
            elif format_info.get('supports_xmp', False):
                # 使用XMP写入
                success = XmpHandler.write_xmp(output_path, metadata)
            
            # 如果内置方法写入失败，尝试使用exiftool作为回退
            if not success:
                logger.warning(f"内置方法写入失败，尝试使用exiftool作为回退: {output_path}")
                success = MetadataWriter._write_with_exiftool(output_path, metadata)

        if success:
            return {
                'success': True,
                'output_path': output_path,
                'message': '写入成功'
            }
        else:
            # 如果写入失败且是复制模式，删除复制的文件
            if copy_mode and os.path.exists(output_path):
                os.remove(output_path)
            return {
                'success': False,
                'output_path': None,
                'message': '写入失败'
            }

    @staticmethod
    def _write_exif(filepath: str, metadata: Dict[str, Any]) -> bool:
        """写入EXIF信息，如果piexif失败则使用exiftool作为回退"""
        try:
            # 首先尝试使用piexif写入
            success = MetadataWriter._write_exif_with_piexif(filepath, metadata)
            
            if success:
                return True
            
            # 如果piexif失败，尝试使用exiftool作为回退
            logger.warning(f"piexif写入失败，尝试使用exiftool作为回退: {filepath}")
            return MetadataWriter._write_exif_with_exiftool_fallback(filepath, metadata)

        except Exception as e:
            logger.error(f"写入EXIF信息失败: {filepath}, 错误: {str(e)}")
            # 尝试使用exiftool作为回退
            return MetadataWriter._write_exif_with_exiftool_fallback(filepath, metadata)

    @staticmethod
    def _write_exif_with_piexif(filepath: str, metadata: Dict[str, Any]) -> bool:
        """使用piexif写入EXIF信息"""
        try:
            # 转换字段名（内部名 -> ExifHandler接受的名）
            exif_metadata = {}

            field_mapping = {
                'artist': 'artist',
                'copyright': 'copyright',
                'description': 'description',
                'make': 'make',
                'model': 'model',
                'software': 'software',
                'lens': 'lens',
                'orientation': 'orientation',
                'exposure_time': 'exposure_time',
                'fnumber': 'fnumber',
                'iso': 'iso',
                'focal_length': 'focal_length',
            }

            for key, value in metadata.items():
                key_lower = key.lower()
                if key_lower in field_mapping:
                    exif_metadata[field_mapping[key_lower]] = str(value)

            # 处理时间字段
            if 'datetime' in metadata:
                dt = metadata['datetime']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                exif_metadata['datetime'] = dt_str
                exif_metadata['datetime_original'] = dt_str
                exif_metadata['datetime_digitized'] = dt_str

            # 处理单独指定的creation_time
            if 'creation_time' in metadata:
                dt = metadata['creation_time']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                exif_metadata['datetime_digitized'] = dt_str

            return ExifHandler.write_exif(filepath, exif_metadata)

        except Exception as e:
            logger.error(f"piexif写入EXIF信息失败: {filepath}, 错误: {str(e)}")
            return False

    @staticmethod
    def _write_exif_with_exiftool_fallback(filepath: str, metadata: Dict[str, Any]) -> bool:
        """使用exiftool作为回退写入EXIF信息
        ExifTool字段名参考: https://exiftool.org/TagNames.html
        注意: ExifTool使用不同的显示名和实际标签名，这里使用ExifTool的写入标签名
        """
        try:
            et = get_exiftool()
            if not et.is_available:
                logger.warning("ExifTool不可用，无法作为回退")
                return False

            # 转换字段名（内部名 -> ExifTool标签名）
            # ExifTool写入时自动选择最佳存储位置（EXIF/IPTC/XMP）
            et_metadata = {}

            field_mapping = {
                'artist': 'Artist',           # EXIF:Artist (Tag 315)
                'copyright': 'Copyright',     # EXIF:Copyright (Tag 33432)
                'description': 'ImageDescription',  # EXIF:ImageDescription (Tag 270)
                'make': 'Make',               # EXIF:Make (Tag 271)
                'model': 'Model',             # EXIF:Model (Tag 272)
                'software': 'Software',       # EXIF:Software (Tag 305)
                'title': 'Title',             # IPTC:Title / XMP:dc:title
                'keywords': 'Keywords',       # IPTC:Keywords / XMP:dc:subject
                'lens': 'LensModel',          # EXIF:LensModel (Tag 42036)
                'orientation': 'Orientation', # EXIF:Orientation (Tag 274)
                'exposure_time': 'ExposureTime',  # EXIF:ExposureTime (Tag 33434)
                'fnumber': 'FNumber',         # EXIF:FNumber (Tag 33437)
                'iso': 'ISO',                 # EXIF:ISOSpeedRatings (Tag 34855)
                'focal_length': 'FocalLength',  # EXIF:FocalLength (Tag 37386)
            }

            for key, value in metadata.items():
                key_lower = key.lower()
                if key_lower in field_mapping:
                    et_metadata[field_mapping[key_lower]] = str(value)

            # 处理时间字段 - ExifTool的时间标签名
            # EXIF规范: DateTimeOriginal(36867), DateTimeDigitized(36868), DateTime(306)
            # ExifTool显示名: DateTimeOriginal, CreateDate, ModifyDate
            if 'datetime' in metadata:
                dt = metadata['datetime']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['DateTimeOriginal'] = dt_str  # 拍摄时间
                et_metadata['CreateDate'] = dt_str         # 数字化时间 (EXIF:DateTimeDigitized)
                et_metadata['ModifyDate'] = dt_str         # 修改时间 (EXIF:DateTime)

            # 处理单独指定的datetime_original -> DateTimeOriginal
            if 'datetime_original' in metadata:
                dt = metadata['datetime_original']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['DateTimeOriginal'] = dt_str

            # 处理单独指定的datetime_digitized -> CreateDate
            if 'datetime_digitized' in metadata:
                dt = metadata['datetime_digitized']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['CreateDate'] = dt_str

            # 处理单独指定的creation_time -> CreateDate
            if 'creation_time' in metadata:
                dt = metadata['creation_time']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['CreateDate'] = dt_str

            # 使用exiftool写入
            success = et.write_metadata(filepath, et_metadata)
            
            if success:
                logger.info(f"使用exiftool成功写入EXIF信息: {filepath}")
                return True
            else:
                # 如果exiftool写入失败，尝试使用copy_filetime_to_exif方法
                logger.warning(f"exiftool写入失败，尝试使用copy_filetime_to_exif: {filepath}")
                return et.copy_filetime_to_exif(filepath)

        except Exception as e:
            logger.error(f"ExifTool回退写入EXIF信息失败: {filepath}, 错误: {str(e)}")
            return False

    @staticmethod
    def _write_with_exiftool(filepath: str, metadata: Dict[str, Any]) -> bool:
        """使用exiftool写入信息
        ExifTool字段名参考: https://exiftool.org/TagNames.html
        适用于需要exiftool的格式：HEIF/HEIC、RAW、AVIF、JPEG XL、PSD
        """
        try:
            et = get_exiftool()
            if not et.is_available:
                return False

            # 转换字段名（内部名 -> ExifTool标签名）
            et_metadata = {}

            field_mapping = {
                'artist': 'Artist',           # EXIF:Artist (Tag 315)
                'copyright': 'Copyright',     # EXIF:Copyright (Tag 33432)
                'description': 'ImageDescription',  # EXIF:ImageDescription (Tag 270)
                'make': 'Make',               # EXIF:Make (Tag 271)
                'model': 'Model',             # EXIF:Model (Tag 272)
                'software': 'Software',       # EXIF:Software (Tag 305)
                'title': 'Title',             # IPTC:Title / XMP:dc:title
                'keywords': 'Keywords',       # IPTC:Keywords / XMP:dc:subject
                'lens': 'LensModel',          # EXIF:LensModel (Tag 42036)
                'orientation': 'Orientation', # EXIF:Orientation (Tag 274)
                'exposure_time': 'ExposureTime',  # EXIF:ExposureTime (Tag 33434)
                'fnumber': 'FNumber',         # EXIF:FNumber (Tag 33437)
                'iso': 'ISO',                 # EXIF:ISOSpeedRatings (Tag 34855)
                'focal_length': 'FocalLength',  # EXIF:FocalLength (Tag 37386)
            }

            for key, value in metadata.items():
                key_lower = key.lower()
                if key_lower in field_mapping:
                    et_metadata[field_mapping[key_lower]] = str(value)

            # 处理时间字段
            if 'datetime' in metadata:
                dt = metadata['datetime']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['DateTimeOriginal'] = dt_str  # 拍摄时间
                et_metadata['CreateDate'] = dt_str         # 数字化时间
                et_metadata['ModifyDate'] = dt_str         # 修改时间

            # 处理单独指定的datetime_original -> DateTimeOriginal
            if 'datetime_original' in metadata:
                dt = metadata['datetime_original']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['DateTimeOriginal'] = dt_str

            # 处理单独指定的datetime_digitized -> CreateDate
            if 'datetime_digitized' in metadata:
                dt = metadata['datetime_digitized']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['CreateDate'] = dt_str

            # 处理单独指定的creation_time -> CreateDate
            if 'creation_time' in metadata:
                dt = metadata['creation_time']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['CreateDate'] = dt_str

            return et.write_metadata(filepath, et_metadata)

        except Exception as e:
            logger.error(f"ExifTool写入信息失败: {filepath}, 错误: {str(e)}")
            return False

    @staticmethod
    def batch_write_metadata(
        file_list: list,
        metadata: Dict[str, Any],
        copy_mode: bool = True,
        output_dir: str = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        批量写入元信息

        Args:
            file_list: 文件列表
            metadata: 要写入的元信息
            copy_mode: 是否复制模式
            output_dir: 输出目录
            progress_callback: 进度回调函数 (current, total, filename)

        Returns:
            操作结果统计
        """
        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
        }

        for i, filepath in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, len(file_list), os.path.basename(filepath))

            result = MetadataWriter.write_metadata(
                filepath, metadata, copy_mode, output_dir
            )

            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'file': filepath,
                    'message': result['message']
                })

        return results

    @staticmethod
    def write_metadata_from_filetime(filepath: str, copy_mode: bool = True, output_dir: str = None) -> Dict[str, Any]:
        """
        将文件修改时间复制到EXIF DateTimeOriginal

        Args:
            filepath: 源文件路径
            copy_mode: 是否复制模式（True=复制后修改，False=直接修改原文件）
            output_dir: 输出目录（copy_mode=True时使用）

        Returns:
            操作结果 {'success': bool, 'output_path': str, 'message': str}
        """
        if not os.path.exists(filepath):
            return {'success': False, 'output_path': None, 'message': '文件不存在'}

        # 检查文件是否真的是图片格式
        is_image, image_check_msg = FormatDetector.is_truly_image(filepath)
        if not is_image:
            logger.warning(f"文件不是真正的图片格式: {filepath}, {image_check_msg}")
            return {
                'success': False,
                'output_path': None,
                'message': f'文件不是图片格式: {image_check_msg}',
                'skipped': True,
                'error_type': 'not_image_file',
                'error_detail': image_check_msg
            }

        # 获取格式信息
        format_info = FormatDetector.get_format_info(filepath)

        # 确定输出路径
        if copy_mode:
            if output_dir is None:
                output_dir = os.path.dirname(filepath)
            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(output_dir, os.path.basename(filepath))
            output_path = get_unique_filename(output_path)

            # 复制文件
            try:
                shutil.copy2(filepath, output_path)
            except Exception as e:
                return {'success': False, 'output_path': None, 'message': f'复制文件失败: {str(e)}'}
        else:
            output_path = filepath

        # 尝试将文件修改时间写入元信息
        success = False
        
        # 如果文件支持XMP，使用XMP写入时间
        if format_info['supports_xmp']:
            # 获取文件修改时间
            stat = os.stat(output_path)
            file_mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # 构建XMP元数据
            xmp_metadata = {
                'datetime_original': file_mtime,
                'datetime_digitized': file_mtime,
                'xmp:ModifyDate': file_mtime
            }
            
            # 使用XMP写入
            success = XmpHandler.write_xmp(output_path, xmp_metadata)
            
            if success:
                logger.info(f"成功将文件修改时间写入XMP: {output_path}")
            else:
                logger.warning(f"XMP写入失败: {output_path}")
                
                # 如果XMP写入失败，尝试使用exiftool作为回退
                try:
                    et = get_exiftool()
                    if et.is_available:
                        success = et.copy_filetime_to_exif(output_path)
                        if success:
                            logger.info(f"使用exiftool成功将文件修改时间写入EXIF: {output_path}")
                        else:
                            logger.warning(f"使用exiftool复制时间失败: {output_path}")
                except Exception as e:
                    logger.error(f"exiftool回退失败: {output_path}, 错误: {str(e)}")
        else:
            # 对于不支持XMP的文件，尝试使用exiftool
            try:
                et = get_exiftool()
                if et.is_available:
                    success = et.copy_filetime_to_exif(output_path)
                    
                    if success:
                        logger.info(f"成功将文件修改时间复制到EXIF: {output_path}")
                    else:
                        logger.warning(f"使用exiftool复制时间失败: {output_path}")
                else:
                    logger.warning("ExifTool不可用，无法复制文件时间")
                    
            except Exception as e:
                logger.error(f"复制文件时间失败: {output_path}, 错误: {str(e)}")

        if success:
            return {
                'success': True,
                'output_path': output_path,
                'message': '成功将文件修改时间写入元信息'
            }
        else:
            # 如果失败且是复制模式，删除复制的文件
            if copy_mode and os.path.exists(output_path):
                os.remove(output_path)
            return {
                'success': False,
                'output_path': None,
                'message': '无法将文件修改时间写入元信息'
            }

    @staticmethod
    def batch_write_metadata_from_filetime(
        file_list: list,
        copy_mode: bool = True,
        output_dir: str = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        批量将文件修改时间复制到EXIF DateTimeOriginal

        Args:
            file_list: 文件列表
            copy_mode: 是否复制模式
            output_dir: 输出目录
            progress_callback: 进度回调函数 (current, total, filename)

        Returns:
            操作结果统计
        """
        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
        }

        for i, filepath in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, len(file_list), os.path.basename(filepath))

            result = MetadataWriter.write_metadata_from_filetime(
                filepath, copy_mode, output_dir
            )

            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'file': filepath,
                    'message': result['message']
                })

        return results
    
    @staticmethod
    def write_exif(filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入EXIF数据
        
        Args:
            filepath: 图片路径
            metadata: EXIF数据字典
            
        Returns:
            是否成功
        """
        try:
            return MetadataWriter._write_exif(filepath, metadata)
        except Exception as e:
            logger.error(f"写入EXIF失败: {filepath}, 错误: {str(e)}")
            return False
    
    @staticmethod
    def write_xmp(filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入XMP数据
        
        Args:
            filepath: 图片路径
            metadata: XMP数据字典
            
        Returns:
            是否成功
        """
        try:
            return XmpHandler.write_xmp(filepath, metadata)
        except Exception as e:
            logger.error(f"写入XMP失败: {filepath}, 错误: {str(e)}")
            return False
    
    @staticmethod
    def write_iptc(filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入IPTC数据
        
        Args:
            filepath: 图片路径
            metadata: IPTC数据字典
            
        Returns:
            是否成功
        """
        try:
            # 尝试使用exiftool写入IPTC数据
            et = get_exiftool()
            if et.is_available:
                # 转换字段名（内部名 -> ExifTool标签名）
                iptc_metadata = {}
                field_mapping = {
                    'title': 'Title',
                    'description': 'Description',
                    'author': 'Author',
                    'copyright': 'Copyright',
                    'keywords': 'Keywords',
                }
                
                for key, value in metadata.items():
                    key_lower = key.lower()
                    if key_lower in field_mapping:
                        iptc_metadata[field_mapping[key_lower]] = str(value)
                
                return et.write_metadata(filepath, iptc_metadata)
            return False
        except Exception as e:
            logger.error(f"写入IPTC失败: {filepath}, 错误: {str(e)}")
            return False
    
    @staticmethod
    def copy_filetime_to_exif(filepath: str) -> bool:
        """
        复制文件时间到EXIF
        
        Args:
            filepath: 图片路径
            
        Returns:
            是否成功
        """
        try:
            et = get_exiftool()
            if et.is_available:
                return et.copy_filetime_to_exif(filepath)
            return False
        except Exception as e:
            logger.error(f"复制文件时间到EXIF失败: {filepath}, 错误: {str(e)}")
            return False
