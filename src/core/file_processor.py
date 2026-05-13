"""
King_photo - 文件处理模块
处理文件重命名、时间修复等
"""

import os
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

from .metadata_reader import MetadataReader
from ..utils.helpers import (
    generate_renamed_filename,
    set_file_times,
    get_file_times,
    ensure_output_folder,
    get_unique_filename,
    sanitize_filename
)
from ..utils.constants import DEFAULT_RENAME_FORMAT


class FileProcessor:
    """文件处理器"""

    @staticmethod
    def rename_file(
        filepath: str,
        rename_format: str = DEFAULT_RENAME_FORMAT,
        output_dir: str = None,
        sequence: int = 1,
        copy_mode: bool = True
    ) -> Dict[str, Any]:
        """
        重命名文件

        Args:
            filepath: 源文件路径
            rename_format: 重命名格式
            output_dir: 输出目录
            sequence: 序号
            copy_mode: 是否复制模式

        Returns:
            操作结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'message': '文件不存在'}

        # 读取元信息
        metadata = MetadataReader.read_metadata(filepath)

        # 获取原文件名（不含扩展名）
        original_name = os.path.splitext(os.path.basename(filepath))[0]
        ext = os.path.splitext(filepath)[1].lower()

        # 生成新文件名
        new_filename = generate_renamed_filename(
            original_name, rename_format, metadata, sequence, ext
        )

        # 确定输出路径
        if output_dir is None:
            output_dir = os.path.dirname(filepath)

        ensure_output_folder(output_dir)
        new_filepath = os.path.join(output_dir, new_filename)
        new_filepath = get_unique_filename(new_filepath)

        try:
            if copy_mode:
                shutil.copy2(filepath, new_filepath)
            else:
                os.rename(filepath, new_filepath)

            return {
                'success': True,
                'original_path': filepath,
                'new_path': new_filepath,
                'new_filename': os.path.basename(new_filepath),
                'message': '重命名成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'重命名失败: {str(e)}'
            }

    @staticmethod
    def fix_file_time(
        filepath: str,
        copy_mode: bool = True,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        修复文件时间（将文件时间设为拍摄时间）

        Args:
            filepath: 源文件路径
            copy_mode: 是否复制模式
            output_dir: 输出目录

        Returns:
            操作结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'message': '文件不存在'}

        # 获取拍摄时间
        photo_dt = MetadataReader.get_datetime(filepath)

        if photo_dt is None:
            return {
                'success': False,
                'message': '无法获取拍摄时间'
            }

        # 确定输出路径
        if copy_mode:
            if output_dir is None:
                output_dir = os.path.dirname(filepath)
            ensure_output_folder(output_dir)
            output_path = os.path.join(output_dir, os.path.basename(filepath))
            output_path = get_unique_filename(output_path)
            shutil.copy2(filepath, output_path)
        else:
            output_path = filepath

        # 修改文件时间
        success = set_file_times(output_path, photo_dt)

        if success:
            return {
                'success': True,
                'original_path': filepath,
                'output_path': output_path,
                'datetime': photo_dt,
                'message': f'时间已修复为 {photo_dt.strftime("%Y-%m-%d %H:%M:%S")}'
            }
        else:
            return {
                'success': False,
                'message': '修改文件时间失败'
            }

    @staticmethod
    def batch_rename(
        file_list: List[str],
        rename_format: str = DEFAULT_RENAME_FORMAT,
        output_dir: str = None,
        copy_mode: bool = True,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        批量重命名

        Args:
            file_list: 文件列表
            rename_format: 重命名格式
            output_dir: 输出目录
            copy_mode: 是否复制模式
            progress_callback: 进度回调

        Returns:
            操作结果统计
        """
        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
            'details': []
        }

        for i, filepath in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, len(file_list), os.path.basename(filepath))

            result = FileProcessor.rename_file(
                filepath, rename_format, output_dir, i + 1, copy_mode
            )

            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1

            results['details'].append({
                'file': filepath,
                'result': result
            })

        return results

    @staticmethod
    def batch_fix_time(
        file_list: List[str],
        output_dir: str = None,
        copy_mode: bool = True,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        批量修复时间

        Args:
            file_list: 文件列表
            output_dir: 输出目录
            copy_mode: 是否复制模式
            progress_callback: 进度回调

        Returns:
            操作结果统计
        """
        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        for i, filepath in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, len(file_list), os.path.basename(filepath))

            result = FileProcessor.fix_file_time(filepath, copy_mode, output_dir)

            if result['success']:
                results['success'] += 1
            else:
                if '无法获取' in result['message']:
                    results['skipped'] += 1
                else:
                    results['failed'] += 1

            results['details'].append({
                'file': filepath,
                'result': result
            })

        return results

    @staticmethod
    def copy_files(
        file_list: List[str],
        output_dir: str,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        复制文件到指定目录

        Args:
            file_list: 文件列表
            output_dir: 输出目录
            progress_callback: 进度回调

        Returns:
            操作结果统计
        """
        ensure_output_folder(output_dir)

        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
        }

        for i, filepath in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, len(file_list), os.path.basename(filepath))

            try:
                dest_path = os.path.join(output_dir, os.path.basename(filepath))
                dest_path = get_unique_filename(dest_path)
                shutil.copy2(filepath, dest_path)
                results['success'] += 1
            except Exception:
                results['failed'] += 1

        return results
