"""
King_photo - 修复引擎
处理文件后缀错误、时间信息提取和修复
支持回滚机制和恢复功能
"""

import os
import re
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

from .format_detector import FormatDetector
from .metadata_reader import MetadataReader
from ..utils.helpers import (
    extract_time_from_filename,
    set_file_times,
    get_file_times,
    ensure_output_folder,
    get_unique_filename,
    generate_renamed_filename,
    sanitize_filename
)


# 备份文件后缀
BACKUP_SUFFIX = '.res'


class RepairEngine:
    """修复引擎"""

    @staticmethod
    def get_backup_path(filepath: str) -> str:
        """获取备份文件路径"""
        return filepath + BACKUP_SUFFIX

    @staticmethod
    def has_backup(filepath: str) -> bool:
        """检查是否有备份文件"""
        backup_path = RepairEngine.get_backup_path(filepath)
        return os.path.exists(backup_path)

    @staticmethod
    def create_backup(filepath: str, output_dir: str = None) -> Dict[str, Any]:
        """
        创建备份文件（原文件添加.res后缀）
        如果备份已存在，不重复创建

        Args:
            filepath: 原文件路径
            output_dir: 输出目录（如果指定，备份在输出目录）

        Returns:
            {'success': bool, 'backup_path': str, 'message': str}
        """
        if not os.path.exists(filepath):
            return {'success': False, 'backup_path': None, 'message': '文件不存在'}

        # 确定备份路径
        if output_dir:
            ensure_output_folder(output_dir)
            filename = os.path.basename(filepath)
            backup_path = os.path.join(output_dir, filename + BACKUP_SUFFIX)
        else:
            backup_path = filepath + BACKUP_SUFFIX

        # 如果备份已存在，跳过
        if os.path.exists(backup_path):
            return {
                'success': True,
                'backup_path': backup_path,
                'message': '备份已存在',
                'already_exists': True
            }

        try:
            shutil.copy2(filepath, backup_path)
            return {
                'success': True,
                'backup_path': backup_path,
                'message': f'备份成功',
                'already_exists': False
            }
        except Exception as e:
            return {
                'success': False,
                'backup_path': None,
                'message': f'备份失败: {str(e)}'
            }

    @staticmethod
    def restore_from_backup(backup_path: str, restore_path: str = None) -> Dict[str, Any]:
        """
        从备份恢复文件

        Args:
            backup_path: 备份文件路径
            restore_path: 恢复目标路径（默认为去掉.res后缀）

        Returns:
            {'success': bool, 'message': str}
        """
        if not os.path.exists(backup_path):
            return {'success': False, 'message': '备份文件不存在'}

        # 确定恢复路径
        if restore_path is None:
            if backup_path.endswith(BACKUP_SUFFIX):
                restore_path = backup_path[:-len(BACKUP_SUFFIX)]
            else:
                return {'success': False, 'message': '无法确定恢复路径'}

        try:
            shutil.copy2(backup_path, restore_path)
            return {
                'success': True,
                'restore_path': restore_path,
                'message': f'恢复成功: {os.path.basename(restore_path)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'恢复失败: {str(e)}'
            }

    @staticmethod
    def delete_backup(filepath: str) -> Dict[str, Any]:
        """
        删除备份文件

        Args:
            filepath: 原文件路径（会自动查找对应的.res文件）

        Returns:
            {'success': bool, 'message': str}
        """
        backup_path = RepairEngine.get_backup_path(filepath)

        if not os.path.exists(backup_path):
            return {'success': False, 'message': '备份文件不存在'}

        try:
            os.remove(backup_path)
            return {'success': True, 'message': '备份已删除'}
        except Exception as e:
            return {'success': False, 'message': f'删除失败: {str(e)}'}

    @staticmethod
    def delete_backups(folder_path: str) -> Dict[str, Any]:
        """
        删除文件夹中所有备份文件（.res后缀）

        Args:
            folder_path: 文件夹路径

        Returns:
            {'total': int, 'deleted': int, 'failed': int}
        """
        results = {
            'total': 0,
            'deleted': 0,
            'failed': 0,
            'files': []
        }

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(BACKUP_SUFFIX) or re.search(r'\.res_\d+$', file):
                    filepath = os.path.join(root, file)
                    results['total'] += 1

                    try:
                        os.remove(filepath)
                        results['deleted'] += 1
                        results['files'].append(filepath)
                    except Exception:
                        results['failed'] += 1

        return results

    @staticmethod
    def check_file_extension(filepath: str) -> Dict[str, Any]:
        """检查文件后缀是否正确"""
        current_ext = os.path.splitext(filepath)[1].lower()
        real_format, is_consistent = FormatDetector.get_real_format(filepath)
        correct_ext = FormatDetector.get_correct_extension(filepath)

        return {
            'needs_fix': not is_consistent,
            'current_ext': current_ext,
            'correct_ext': correct_ext,
            'real_format': real_format,
            'is_consistent': is_consistent,
        }

    @staticmethod
    def fix_extension(
        filepath: str,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        修复文件后缀（带备份）

        Args:
            filepath: 源文件路径
            output_dir: 输出目录

        Returns:
            操作结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'message': '文件不存在'}

        check_result = RepairEngine.check_file_extension(filepath)

        if not check_result['needs_fix']:
            return {
                'success': True,
                'message': '后缀正确，无需修复',
                'skipped': True,
                'original_path': filepath,
                'new_path': filepath
            }

        correct_ext = check_result['correct_ext']
        if not correct_ext:
            return {
                'success': False,
                'message': '无法确定正确的文件格式'
            }

        # 确定输出目录
        if output_dir is None:
            output_dir = os.path.dirname(filepath)
        ensure_output_folder(output_dir)

        # 创建备份（在输出目录）
        backup_result = RepairEngine.create_backup(filepath, output_dir)

        # 生成新文件名
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        new_filename = base_name + correct_ext
        new_filepath = os.path.join(output_dir, new_filename)
        new_filepath = get_unique_filename(new_filepath)

        try:
            # 复制修复后的文件
            shutil.copy2(filepath, new_filepath)

            return {
                'success': True,
                'original_path': filepath,
                'new_path': new_filepath,
                'backup_path': backup_result.get('backup_path'),
                'old_ext': check_result['current_ext'],
                'new_ext': correct_ext,
                'real_format': check_result['real_format'],
                'message': f'后缀已修复: {check_result["current_ext"]} -> {correct_ext}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'修复失败: {str(e)}'
            }

    @staticmethod
    def extract_time_info(filepath: str) -> Dict[str, Any]:
        """
        提取时间信息（从文件名和元数据）
        对不同格式做适配
        """
        result = {
            'from_filename': None,
            'from_metadata': None,
            'best_match': None,
            'source': 'none'
        }

        # 从文件名提取
        filename = os.path.basename(filepath)
        result['from_filename'] = extract_time_from_filename(filename)

        # 从元数据提取（根据格式适配）
        ext = os.path.splitext(filepath)[1].lower()

        # GIF文件通常没有拍摄时间，跳过元数据读取
        if ext != '.gif':
            result['from_metadata'] = MetadataReader.get_datetime(filepath)

        # 选择最佳时间
        if result['from_metadata']:
            result['best_match'] = result['from_metadata']
            result['source'] = 'metadata'
        elif result['from_filename']:
            result['best_match'] = result['from_filename']
            result['source'] = 'filename'

        return result

    @staticmethod
    def get_file_times_info(filepath: str) -> Dict[str, datetime]:
        """获取文件的所有时间信息"""
        stat = os.stat(filepath)
        return {
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'accessed': datetime.fromtimestamp(stat.st_atime),
        }

    @staticmethod
    def repair_with_backup(
        filepath: str,
        rename_format: str = '{datetime}',
        output_dir: str = None,
        fix_extension: bool = True,
        fix_time: bool = True
    ) -> Dict[str, Any]:
        """
        带备份的修复

        Args:
            filepath: 源文件路径
            rename_format: 重命名格式
            output_dir: 输出目录
            fix_extension: 是否修复后缀
            fix_time: 是否修复时间

        Returns:
            操作结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'message': '文件不存在'}

        # 确定输出目录
        if output_dir is None:
            output_dir = os.path.dirname(filepath)
        ensure_output_folder(output_dir)

        results = {
            'backup': None,
            'extension': None,
            'time': None,
        }

        actual_path = filepath

        # Step 1: 创建备份（始终创建）
        backup_result = RepairEngine.create_backup(filepath, output_dir)
        results['backup'] = backup_result

        # Step 2: 修复后缀
        if fix_extension:
            ext_result = RepairEngine.fix_extension(actual_path, output_dir)
            results['extension'] = ext_result
            if ext_result['success'] and not ext_result.get('skipped'):
                actual_path = ext_result['new_path']

        # Step 3: 提取时间并重命名
        if fix_time:
            time_info = RepairEngine.extract_time_info(actual_path)
            file_times = RepairEngine.get_file_times_info(actual_path)

            # 获取要使用的时间
            photo_dt = time_info['best_match']

            # 如果没有拍摄时间，使用文件修改时间
            if photo_dt is None:
                photo_dt = file_times['modified']
                time_info['source'] = 'file_modified'

            if photo_dt:
                ext = os.path.splitext(actual_path)[1].lower()

                # 生成新文件名
                original_name = os.path.splitext(os.path.basename(actual_path))[0]

                # 读取元数据用于重命名
                metadata = MetadataReader.read_metadata(actual_path)
                metadata['datetime'] = photo_dt

                new_filename = generate_renamed_filename(
                    original_name, rename_format, metadata, 1, ext
                )

                new_filepath = os.path.join(output_dir, new_filename)
                new_filepath = get_unique_filename(new_filepath)

                try:
                    # 复制修复后的文件
                    shutil.copy2(actual_path, new_filepath)

                    # 修改文件时间
                    set_file_times(new_filepath, photo_dt)

                    results['time'] = {
                        'success': True,
                        'new_path': new_filepath,
                        'datetime': photo_dt,
                        'source': time_info['source'],
                        'message': f'时间修复成功'
                    }
                    actual_path = new_filepath
                except Exception as e:
                    results['time'] = {
                        'success': False,
                        'message': f'重命名失败: {str(e)}'
                    }
            else:
                results['time'] = {
                    'success': False,
                    'message': '无法获取时间信息'
                }

        # 判断整体是否成功
        success = True
        if fix_extension and results['extension'] and not results['extension']['success'] and not results['extension'].get('skipped'):
            success = False
        if fix_time and results['time'] and not results['time']['success']:
            success = False

        return {
            'success': success,
            'details': results,
            'output_path': actual_path,
            'backup_path': backup_result.get('backup_path'),
            'message': '修复成功' if success else '部分修复失败'
        }

    @staticmethod
    def batch_repair(
        file_list: List[str],
        rename_format: str = '{datetime}',
        output_dir: str = None,
        fix_extension: bool = True,
        fix_time: bool = True,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        批量修复（带备份）
        """
        results = {
            'total': len(file_list),
            'success': 0,
            'partial': 0,
            'failed': 0,
            'details': []
        }

        for i, filepath in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, len(file_list), os.path.basename(filepath))

            result = RepairEngine.repair_with_backup(
                filepath, rename_format, output_dir,
                fix_extension, fix_time
            )

            if result['success']:
                results['success'] += 1
            else:
                details = result['details']
                partial = False
                if details.get('extension') and details['extension'].get('success'):
                    partial = True
                if details.get('time') and details['time'].get('success'):
                    partial = True

                if partial:
                    results['partial'] += 1
                else:
                    results['failed'] += 1

            results['details'].append({
                'file': filepath,
                'result': result
            })

        return results

    @staticmethod
    def batch_restore(
        file_list: List[str],
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        批量恢复（从备份）

        Args:
            file_list: 文件列表（可以是原文件或备份文件）
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

            # 确定备份文件路径
            if filepath.endswith(BACKUP_SUFFIX):
                backup_path = filepath
            else:
                backup_path = RepairEngine.get_backup_path(filepath)

            if os.path.exists(backup_path):
                restore_result = RepairEngine.restore_from_backup(backup_path)
                if restore_result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                results['details'].append({
                    'backup': backup_path,
                    'result': restore_result
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'backup': backup_path,
                    'result': {'success': False, 'message': '备份文件不存在'}
                })

        return results
