"""
King_photo - 文件处理模块
处理文件重命名、时间修复等
"""

import logging
import os
import shutil
from typing import Optional, Dict, Any, List, Callable

from ..api.interfaces import IFileProcessor
from .metadata_reader import MetadataReader
from ..utils.helpers import (
    generate_renamed_filename,
    set_file_times,
    get_file_times,
    ensure_output_folder,
    get_unique_filename,
)
from ..utils.constants import DEFAULT_RENAME_FORMAT, ALL_EXTENSIONS

# 获取日志记录器
logger = logging.getLogger(__name__)


class FileProcessor(IFileProcessor):
    """文件处理器，实现IFileProcessor接口"""

    @staticmethod
    def get_image_files(folder_path: str, recursive: bool = False) -> List[str]:
        """
        获取文件夹中的图片文件
        
        Args:
            folder_path: 文件夹路径
            recursive: 是否递归查找子文件夹
            
        Returns:
            图片文件路径列表
        """
        if not os.path.exists(folder_path):
            return []
        
        image_files = []
        
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    if ext in ALL_EXTENSIONS:
                        image_files.append(filepath)
        else:
            for file in os.listdir(folder_path):
                filepath = os.path.join(folder_path, file)
                if os.path.isfile(filepath):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in ALL_EXTENSIONS:
                        image_files.append(filepath)
        
        return sorted(image_files)
    
    @staticmethod
    def process_files(file_list: List[str], operation: str, **kwargs) -> Dict[str, Any]:
        """
        批量处理文件
        
        Args:
            file_list: 文件列表
            operation: 操作类型 ('rename', 'repair', 'export' 等)
            **kwargs: 操作参数
            
        Returns:
            处理结果字典
        """
        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for filepath in file_list:
            try:
                if operation == 'rename':
                    result = FileProcessor.rename_file(filepath, **kwargs)
                elif operation == 'fix_time':
                    result = FileProcessor.fix_file_time(filepath, **kwargs)
                else:
                    result = {'success': False, 'message': f'不支持的操作: {operation}'}
                
                if result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'file': filepath,
                    'result': result
                })
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'file': filepath,
                    'result': {
                        'success': False,
                        'message': f'处理失败: {str(e)}'
                    }
                })
        
        return results
    
    @staticmethod
    def rename_files(file_list: List[str], pattern: str, 
                    output_dir: str = None, **kwargs) -> Dict[str, Any]:
        """
        批量重命名文件
        
        Args:
            file_list: 文件列表
            pattern: 重命名模式
            output_dir: 输出目录
            **kwargs: 额外参数
            
        Returns:
            重命名结果字典
        """
        return FileProcessor.batch_rename(
            file_list=file_list,
            rename_format=pattern,
            output_dir=output_dir,
            **kwargs
        )
    
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
        output_dir: str = None,
        preserve_created_time: bool = True,
        time_source: str = 'auto'
    ) -> Dict[str, Any]:
        """
        修复文件时间（将文件时间设为拍摄时间）

        Args:
            filepath: 源文件路径
            copy_mode: 是否复制模式
            output_dir: 输出目录
            preserve_created_time: 是否保留原始创建时间（默认True）
            time_source: 时间来源 ('auto', 'metadata', 'modified', 'created')

        Returns:
            操作结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'message': '文件不存在'}

        # 根据time_source获取时间
        photo_dt = None
        if time_source == 'metadata':
            # 只使用元数据时间
            photo_dt = MetadataReader.get_datetime(filepath)
        elif time_source == 'modified':
            # 使用文件修改时间
            try:
                stat = os.stat(filepath)
                photo_dt = datetime.fromtimestamp(stat.st_mtime)
            except Exception as e:
                logger.debug(f"获取文件修改时间失败: {filepath}, 错误: {str(e)}")
        elif time_source == 'created':
            # 使用文件创建时间
            try:
                stat = os.stat(filepath)
                photo_dt = datetime.fromtimestamp(stat.st_ctime)
            except Exception as e:
                logger.debug(f"获取文件创建时间失败: {filepath}, 错误: {str(e)}")
        else:  # 'auto' 或其他值
            # 自动选择（先尝试元数据，再使用文件修改时间）
            photo_dt = MetadataReader.get_datetime(filepath)
            if photo_dt is None:
                try:
                    stat = os.stat(filepath)
                    photo_dt = datetime.fromtimestamp(stat.st_mtime)
                except Exception as e:
                    logger.debug(f"获取文件修改时间失败: {filepath}, 错误: {str(e)}")

        if photo_dt is None:
            return {
                'success': False,
                'message': '无法获取时间信息'
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
        # 如果preserve_created_time为True，则不修改创建时间
        set_created = not preserve_created_time
        success = set_file_times(output_path, photo_dt, set_created=set_created)

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
        progress_callback: Callable = None,
        preserve_created_time: bool = True,
        time_source: str = 'auto'
    ) -> Dict[str, Any]:
        """
        批量修复时间

        Args:
            file_list: 文件列表
            output_dir: 输出目录
            copy_mode: 是否复制模式
            progress_callback: 进度回调
            preserve_created_time: 是否保留原始创建时间（默认True）
            time_source: 时间来源 ('auto', 'metadata', 'modified', 'created')

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

            result = FileProcessor.fix_file_time(filepath, copy_mode, output_dir, preserve_created_time, time_source)

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
    def copy_files(file_list: List[str], output_dir: str, 
                  preserve_structure: bool = True) -> Dict[str, Any]:
        """
        批量复制文件
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            preserve_structure: 是否保持目录结构
            
        Returns:
            复制结果字典
        """
        ensure_output_folder(output_dir)
        
        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for filepath in file_list:
            try:
                if preserve_structure:
                    # 保持相对路径结构
                    rel_path = os.path.relpath(filepath, os.path.dirname(file_list[0]) if file_list else filepath)
                    dest_path = os.path.join(output_dir, rel_path)
                else:
                    dest_path = os.path.join(output_dir, os.path.basename(filepath))
                
                # 确保目标目录存在
                dest_dir = os.path.dirname(dest_path)
                ensure_output_folder(dest_dir)
                
                dest_path = get_unique_filename(dest_path)
                shutil.copy2(filepath, dest_path)
                results['success'] += 1
                results['details'].append({
                    'file': filepath,
                    'dest': dest_path,
                    'success': True
                })
            except Exception as e:
                logger.error(f"复制文件失败: {filepath}, 错误: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'file': filepath,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    @staticmethod
    def move_files(file_list: List[str], output_dir: str,
                  preserve_structure: bool = True) -> Dict[str, Any]:
        """
        批量移动文件
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            preserve_structure: 是否保持目录结构
            
        Returns:
            移动结果字典
        """
        ensure_output_folder(output_dir)
        
        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for filepath in file_list:
            try:
                if preserve_structure:
                    # 保持相对路径结构
                    rel_path = os.path.relpath(filepath, os.path.dirname(file_list[0]) if file_list else filepath)
                    dest_path = os.path.join(output_dir, rel_path)
                else:
                    dest_path = os.path.join(output_dir, os.path.basename(filepath))
                
                # 确保目标目录存在
                dest_dir = os.path.dirname(dest_path)
                ensure_output_folder(dest_dir)
                
                dest_path = get_unique_filename(dest_path)
                shutil.move(filepath, dest_path)
                results['success'] += 1
                results['details'].append({
                    'file': filepath,
                    'dest': dest_path,
                    'success': True
                })
            except Exception as e:
                logger.error(f"移动文件失败: {filepath}, 错误: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'file': filepath,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    @staticmethod
    def delete_files(file_list: List[str], 
                    backup: bool = False, backup_dir: str = None) -> Dict[str, Any]:
        """
        批量删除文件
        
        Args:
            file_list: 文件列表
            backup: 是否备份
            backup_dir: 备份目录
            
        Returns:
            删除结果字典
        """
        if backup and backup_dir:
            ensure_output_folder(backup_dir)
        
        results = {
            'total': len(file_list),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for filepath in file_list:
            try:
                if not os.path.exists(filepath):
                    results['failed'] += 1
                    results['details'].append({
                        'file': filepath,
                        'success': False,
                        'error': '文件不存在'
                    })
                    continue
                
                # 备份文件
                if backup and backup_dir:
                    backup_path = os.path.join(backup_dir, os.path.basename(filepath))
                    backup_path = get_unique_filename(backup_path)
                    shutil.copy2(filepath, backup_path)
                
                # 删除文件
                os.remove(filepath)
                results['success'] += 1
                results['details'].append({
                    'file': filepath,
                    'success': True,
                    'backed_up': backup
                })
            except Exception as e:
                logger.error(f"删除文件失败: {filepath}, 错误: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'file': filepath,
                    'success': False,
                    'error': str(e)
                })
        
        return results
