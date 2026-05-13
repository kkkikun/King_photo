"""
King_photo - 元信息写入引擎
统一的元信息写入接口
"""

import os
import shutil
from datetime import datetime
from typing import Optional, Dict, Any

from .format_detector import FormatDetector
from .exif_handler import ExifHandler
from ..utils.exiftool_wrapper import get_exiftool
from ..utils.helpers import get_file_extension, get_unique_filename


class MetadataWriter:
    """元信息写入引擎"""

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

        if format_info['needs_exiftool']:
            # 使用exiftool写入
            success = MetadataWriter._write_with_exiftool(output_path, metadata)
        else:
            # 使用内置方法写入
            if format_info['supports_exif']:
                success = MetadataWriter._write_exif(output_path, metadata)
            elif format_info['supports_xmp']:
                # XMP写入暂不支持，仅标记成功
                success = True

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
        """写入EXIF信息"""
        try:
            # 转换字段名
            exif_metadata = {}

            field_mapping = {
                'artist': 'artist',
                'copyright': 'copyright',
                'description': 'description',
                'make': 'make',
                'model': 'model',
                'software': 'software',
            }

            for key, value in metadata.items():
                if key in field_mapping:
                    exif_metadata[field_mapping[key]] = str(value)

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

            return ExifHandler.write_exif(filepath, exif_metadata)

        except Exception:
            return False

    @staticmethod
    def _write_with_exiftool(filepath: str, metadata: Dict[str, Any]) -> bool:
        """使用exiftool写入信息"""
        try:
            et = get_exiftool()
            if not et.is_available:
                return False

            # 转换字段名
            et_metadata = {}

            field_mapping = {
                'artist': 'Artist',
                'copyright': 'Copyright',
                'description': 'ImageDescription',
                'make': 'Make',
                'model': 'Model',
                'software': 'Software',
                'title': 'Title',
                'keywords': 'Keywords',
            }

            for key, value in metadata.items():
                if key in field_mapping:
                    et_metadata[field_mapping[key]] = str(value)

            # 处理时间字段
            if 'datetime' in metadata:
                dt = metadata['datetime']
                if isinstance(dt, datetime):
                    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")
                else:
                    dt_str = str(dt)
                et_metadata['DateTimeOriginal'] = dt_str
                et_metadata['CreateDate'] = dt_str
                et_metadata['ModifyDate'] = dt_str

            return et.write_metadata(filepath, et_metadata)

        except Exception:
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
