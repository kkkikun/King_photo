"""
King_photo - 修复引擎
处理文件后缀错误、时间信息提取和修复
"""

import logging
import os
import re
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

from .format_detector import FormatDetector
from .metadata_reader import MetadataReader
from .metadata_writer import MetadataWriter
from ..utils.helpers import (
    extract_time_from_filename,
    set_file_times,
    get_file_times,
    ensure_output_folder,
    get_unique_filename,
    generate_renamed_filename,
    sanitize_filename
)

# 获取日志记录器
logger = logging.getLogger(__name__)





class RepairEngine:
    """修复引擎"""

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
        修复文件后缀

        Args:
            filepath: 源文件路径
            output_dir: 输出目录

        Returns:
            操作结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'message': '文件不存在', 'error_type': 'file_not_found'}

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
                'message': f'无法确定正确的文件格式 (当前扩展名: {check_result["current_ext"]})',
                'error_type': 'unknown_format',
                'current_ext': check_result['current_ext']
            }

        # 确定输出目录
        if output_dir is None:
            output_dir = os.path.dirname(filepath)
        ensure_output_folder(output_dir)

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
                'old_ext': check_result['current_ext'],
                'new_ext': correct_ext,
                'real_format': check_result['real_format'],
                'message': f'后缀已修复: {check_result["current_ext"]} -> {correct_ext}'
            }
        except Exception as e:
            logger.error(f"修复后缀失败: {filepath}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'修复失败: {str(e)}',
                'error_type': 'copy_failed',
                'error_detail': str(e)
            }

    @staticmethod
    def extract_time_info(filepath: str, time_source: str = 'auto') -> Dict[str, Any]:
        """
        提取时间信息（从文件名和元数据）
        对不同格式做适配
        
        Args:
            filepath: 文件路径
            time_source: 时间来源 ('auto', 'metadata', 'modified', 'created')
        
        Returns:
            包含时间信息的字典
        """
        result = {
            'from_filename': None,
            'from_metadata': None,
            'from_file_modified': None,
            'from_file_created': None,
            'best_match': None,
            'source': 'none'
        }

        # 获取文件系统时间
        try:
            file_times = RepairEngine.get_file_times_info(filepath)
            result['from_file_modified'] = file_times['modified']
            result['from_file_created'] = file_times['created']
        except Exception as e:
            logger.debug(f"获取文件系统时间失败: {filepath}, 错误: {str(e)}")

        # 根据time_source选择时间源
        if time_source == 'metadata':
            # 只使用元数据时间
            try:
                result['from_metadata'] = MetadataReader.get_datetime(filepath)
            except Exception as e:
                logger.debug(f"从元数据提取时间失败: {filepath}, 错误: {str(e)}")
            
            if result['from_metadata']:
                result['best_match'] = result['from_metadata']
                result['source'] = 'metadata'
                
        elif time_source == 'modified':
            # 使用文件修改时间
            if result['from_file_modified']:
                result['best_match'] = result['from_file_modified']
                result['source'] = 'file_modified'
                
        elif time_source == 'created':
            # 使用文件创建时间
            if result['from_file_created']:
                result['best_match'] = result['from_file_created']
                result['source'] = 'file_created'
                
        else:  # 'auto' 或其他值
            # 自动选择（先尝试元数据，再尝试文件名，最后使用文件修改时间）
            # 从文件名提取
            filename = os.path.basename(filepath)
            result['from_filename'] = extract_time_from_filename(filename)

            # 从元数据提取（所有格式都尝试）
            try:
                result['from_metadata'] = MetadataReader.get_datetime(filepath)
            except Exception as e:
                logger.debug(f"从元数据提取时间失败: {filepath}, 错误: {str(e)}")

            # 选择最佳时间
            if result['from_metadata']:
                result['best_match'] = result['from_metadata']
                result['source'] = 'metadata'
            elif result['from_filename']:
                result['best_match'] = result['from_filename']
                result['source'] = 'filename'
            elif result['from_file_modified']:
                result['best_match'] = result['from_file_modified']
                result['source'] = 'file_modified'

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
    def repair(
        filepath: str,
        rename_format: str = '{datetime}',
        output_dir: str = None,
        fix_extension: bool = True,
        fix_time: bool = True,
        time_source: str = 'auto',
        unprocessed_dir: str = None
    ) -> Dict[str, Any]:
        """
        修复文件

        Args:
            filepath: 源文件路径
            rename_format: 重命名格式
            output_dir: 输出目录
            fix_extension: 是否修复后缀
            fix_time: 是否修复时间
            time_source: 时间来源 ('auto', 'metadata', 'modified', 'created', 'custom')
            unprocessed_dir: 未处理文件输出目录

        Returns:
            操作结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'message': '文件不存在'}

        # 预先检查文件是否真的是图片格式
        is_image, image_check_msg = FormatDetector.is_truly_image(filepath)
        if not is_image:
            # 检查是否是格式不匹配但仍然是图片格式的情况
            header_format = FormatDetector.detect_by_header(filepath)
            ext_format = FormatDetector.detect_by_extension(filepath)
            
            # 如果是格式不匹配但仍然是图片格式，继续处理（修复后缀）
            if header_format and ext_format:
                logger.info(f"文件格式不匹配，将尝试修复后缀: {filepath}, 文件头格式: {header_format}, 扩展名格式: {ext_format}")
            else:
                # 如果是真正的非图片格式（如视频），跳过处理
                logger.warning(f"文件不是真正的图片格式: {filepath}, {image_check_msg}")
                
                # 如果指定了未处理输出目录，将文件复制到该目录
                if unprocessed_dir:
                    try:
                        # 确保未处理输出目录存在
                        ensure_output_folder(unprocessed_dir)
                        
                        # 复制文件到未处理目录
                        filename = os.path.basename(filepath)
                        dest_path = os.path.join(unprocessed_dir, filename)
                        dest_path = get_unique_filename(dest_path)
                        
                        shutil.copy2(filepath, dest_path)
                        logger.info(f"已将未处理文件复制到: {dest_path}")
                        
                        return {
                            'success': False,
                            'message': f'文件不是图片格式: {image_check_msg}',
                            'skipped': True,
                            'error_type': 'not_image_file',
                            'error_detail': image_check_msg,
                            'unprocessed_path': dest_path
                        }
                    except Exception as e:
                        logger.error(f"复制未处理文件失败: {filepath}, 错误: {str(e)}")
                
                return {
                    'success': False,
                    'message': f'文件不是图片格式: {image_check_msg}',
                    'skipped': True,
                    'error_type': 'not_image_file',
                    'error_detail': image_check_msg
                }

        # 记录原始文件属性（用于操作完成后恢复）
        original_file_times = None
        try:
            stat = os.stat(filepath)
            original_file_times = {
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
            }
        except Exception as e:
            logger.warning(f"记录文件属性失败: {filepath}, 错误: {str(e)}")

        # 确定输出目录
        if output_dir is None:
            output_dir = os.path.dirname(filepath)
        ensure_output_folder(output_dir)

        # 验证文件格式是否与扩展名匹配
        format_check = FormatDetector.get_real_format(filepath)
        real_format, is_consistent = format_check
        
        if not is_consistent:
            logger.warning(f"文件格式不匹配: {os.path.basename(filepath)}")
            logger.info(f"文件头格式: {real_format}, 扩展名格式: {FormatDetector.detect_by_extension(filepath)}")
            
            # 如果不修复后缀，跳过处理
            if not fix_extension:
                return {
                    'success': False,
                    'message': f'文件格式不匹配，跳过处理',
                    'skipped': True,
                    'format_mismatch': True,
                    'real_format': real_format,
                    'extension_format': FormatDetector.detect_by_extension(filepath)
                }
            else:
                logger.info(f"将修复文件后缀: {os.path.basename(filepath)}")
                # 记录格式不匹配警告
                logger.warning(f"文件格式不匹配，将自动修复后缀: {os.path.basename(filepath)}")

        results = {
            'extension': None,
            'time': None,
        }

        actual_path = filepath

        # Step 2: 修复后缀
        # 在修复前记录原始文件的时间信息
        original_file_times = RepairEngine.get_file_times_info(actual_path) if fix_extension else None
        
        if fix_extension:
            ext_result = RepairEngine.fix_extension(actual_path, output_dir)
            results['extension'] = ext_result
            if ext_result['success'] and not ext_result.get('skipped'):
                actual_path = ext_result['new_path']
                # 修复后缀后，恢复原始文件的时间信息
                if original_file_times:
                    try:
                        # 恢复修改时间和访问时间
                        set_file_times(actual_path, original_file_times['modified'], set_created=False)
                        # 在Windows上尝试恢复创建时间
                        if os.name == 'nt':
                            import ctypes
                            from ctypes import wintypes
                            
                            # Windows API 常量
                            GENERIC_WRITE = 0x40000000
                            FILE_SHARE_READ = 0x00000001
                            FILE_SHARE_WRITE = 0x00000002
                            OPEN_EXISTING = 3
                            FILE_ATTRIBUTE_NORMAL = 0x80
                            
                            # 打开文件
                            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                            file_handle = kernel32.CreateFileW(
                                actual_path,
                                GENERIC_WRITE,
                                FILE_SHARE_READ | FILE_SHARE_WRITE,
                                None,
                                OPEN_EXISTING,
                                FILE_ATTRIBUTE_NORMAL,
                                None
                            )
                            
                            if file_handle != -1:
                                try:
                                    # 转换为Windows FILETIME
                                    unix_timestamp = int(original_file_times['created'].timestamp())
                                    epoc_diff = 116444736000000000
                                    filetime = int((unix_timestamp * 10000000) + epoc_diff)
                                    
                                    # 设置文件创建时间
                                    ctypes.windll.kernel32.SetFileTime(
                                        file_handle,
                                        ctypes.byref(ctypes.c_longlong(filetime)),  # 创建时间
                                        None,  # 访问时间
                                        None   # 修改时间
                                    )
                                finally:
                                    kernel32.CloseHandle(file_handle)
                        logger.info(f"已恢复原始文件时间信息: {actual_path}")
                    except Exception as e:
                        logger.warning(f"恢复文件时间信息失败: {actual_path}, 错误: {str(e)}")

        # Step 3: 提取时间并重命名
        if fix_time:
            time_info = RepairEngine.extract_time_info(actual_path, time_source)
            file_times = RepairEngine.get_file_times_info(actual_path)

            # 获取要使用的时间
            photo_dt = time_info['best_match']

            # 如果没有拍摄时间，使用文件修改时间
            if photo_dt is None:
                photo_dt = file_times['modified']
                time_info['source'] = 'file_modified'
                logger.info(f"未找到拍摄时间，使用文件修改时间: {photo_dt}")
                
                # 尝试将文件修改时间写入EXIF（对于不支持EXIF的格式如GIF，这会失败但不影响后续操作）
                exif_write_result = MetadataWriter.write_metadata_from_filetime(actual_path, copy_mode=False)
                if exif_write_result['success']:
                    logger.info(f"成功将文件修改时间写入EXIF: {actual_path}")
                else:
                    logger.info(f"无法将文件修改时间写入EXIF（可能格式不支持）: {actual_path}")

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
                    
                    # 先写入元数据（此操作会修改文件，重置修改时间）
                    metadata = {
                        'datetime': photo_dt,
                        'datetime_original': photo_dt,
                        'datetime_digitized': photo_dt,
                        'creation_time': photo_dt
                    }
                    
                    write_result = MetadataWriter.write_metadata(new_filepath, metadata, copy_mode=False)
                    if not write_result['success']:
                        logger.warning(f"写入元数据时间失败: {new_filepath}, 错误: {write_result.get('message')}")

                    # 再修改文件时间（包括创建时间）- 必须在元数据写入之后，因为写入元数据会修改文件重置修改时间
                    set_file_times(new_filepath, photo_dt, set_created=True)

                    # 删除Step 2创建的中间文件（如果存在且不是原始文件）
                    if actual_path != filepath and os.path.exists(actual_path) and os.path.exists(new_filepath):
                        try:
                            os.remove(actual_path)
                            logger.info(f"已删除中间文件: {actual_path}")
                        except Exception as e:
                            logger.warning(f"删除中间文件失败: {actual_path}, 错误: {str(e)}")

                    results['time'] = {
                        'success': True,
                        'new_path': new_filepath,
                        'datetime': photo_dt,
                        'source': time_info['source'],
                        'message': f'时间修复成功'
                    }
                    actual_path = new_filepath
                except Exception as e:
                    logger.error(f"重命名失败: {filepath}, 错误: {str(e)}")
                    results['time'] = {
                        'success': False,
                        'message': f'重命名失败: {str(e)}',
                        'error_type': 'rename_failed',
                        'error_detail': str(e)
                    }
            else:
                results['time'] = {
                    'success': False,
                    'message': '无法获取时间信息'
                }

        # 判断整体是否成功（提前计算，用于恢复文件属性逻辑）
        operation_success = True
        if fix_extension and results['extension'] and not results['extension']['success'] and not results['extension'].get('skipped'):
            operation_success = False
        if fix_time and results['time'] and not results['time']['success']:
            operation_success = False

        # 恢复原始文件属性（如果操作成功且没有修复时间）
        # 注意：如果修复时间成功，文件属性会被修改为新时间，所以只恢复非时间修复的情况
        if original_file_times and operation_success:
            # 如果没有修复时间，或者时间修复失败，恢复原始文件属性
            if not fix_time or (results.get('time') and not results['time'].get('success')):
                try:
                    # 恢复修改时间和访问时间
                    set_file_times(actual_path, original_file_times['modified'], set_created=False)
                    
                    # 在Windows上尝试恢复创建时间
                    if os.name == 'nt':
                        import ctypes
                        from ctypes import wintypes
                        
                        # Windows API 常量
                        GENERIC_WRITE = 0x40000000
                        FILE_SHARE_READ = 0x00000001
                        FILE_SHARE_WRITE = 0x00000002
                        OPEN_EXISTING = 3
                        FILE_ATTRIBUTE_NORMAL = 0x80
                        
                        # 打开文件
                        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                        file_handle = kernel32.CreateFileW(
                            actual_path,
                            GENERIC_WRITE,
                            FILE_SHARE_READ | FILE_SHARE_WRITE,
                            None,
                            OPEN_EXISTING,
                            FILE_ATTRIBUTE_NORMAL,
                            None
                        )
                        
                        if file_handle != -1:
                            try:
                                # 转换为Windows FILETIME
                                unix_timestamp = int(original_file_times['created'].timestamp())
                                epoc_diff = 116444736000000000
                                filetime = int((unix_timestamp * 10000000) + epoc_diff)
                                
                                # 设置文件创建时间
                                ctypes.windll.kernel32.SetFileTime(
                                    file_handle,
                                    ctypes.byref(ctypes.c_longlong(filetime)),  # 创建时间
                                    None,  # 访问时间
                                    None   # 修改时间
                                )
                            finally:
                                kernel32.CloseHandle(file_handle)
                    
                    logger.info(f"已恢复原始文件属性: {actual_path}")
                except Exception as e:
                    logger.warning(f"恢复文件属性失败: {actual_path}, 错误: {str(e)}")

        return {
            'success': operation_success,
            'details': results,
            'output_path': actual_path,
            'message': '修复成功' if operation_success else '部分修复失败'
        }

    @staticmethod
    def batch_repair(
        file_list: List[str],
        rename_format: str = '{datetime}',
        output_dir: str = None,
        fix_extension: bool = True,
        fix_time: bool = True,
        progress_callback: Callable = None,
        time_source: str = 'auto',
        unprocessed_dir: str = None
    ) -> Dict[str, Any]:
        """
        批量修复

        Args:
            file_list: 文件列表
            rename_format: 重命名格式
            output_dir: 输出目录
            fix_extension: 是否修复后缀
            fix_time: 是否修复时间
            progress_callback: 进度回调
            time_source: 时间来源
            unprocessed_dir: 未处理文件输出目录

        Returns:
            操作结果统计
        """
        results = {
            'total': len(file_list),
            'success': 0,
            'partial': 0,
            'failed': 0,
            'skipped': 0,
            'unprocessed': 0,
            'details': []
        }

        # 如果指定了未处理输出目录，确保目录存在
        if unprocessed_dir:
            ensure_output_folder(unprocessed_dir)

        for i, filepath in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, len(file_list), os.path.basename(filepath))

            result = RepairEngine.repair(
                filepath, rename_format, output_dir,
                fix_extension, fix_time, time_source, unprocessed_dir
            )

            if result.get('skipped', False):
                results['skipped'] += 1
                # 检查是否是未处理文件（如视频文件）
                if result.get('error_type') == 'not_image_file':
                    results['unprocessed'] += 1
            elif result['success']:
                results['success'] += 1
            else:
                details = result.get('details', {})
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
    def batch_repair_extension(
        file_list: List[str],
        output_dir: str = None,
        auto_fix: bool = True,
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        批量修复后缀

        Args:
            file_list: 文件列表
            output_dir: 输出目录
            auto_fix: 是否自动修复
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

            result = RepairEngine.fix_extension(filepath, output_dir)
            
            if result.get('skipped', False):
                results['skipped'] += 1
            elif result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1

            results['details'].append({
                'file': filepath,
                'result': result
            })

        return results
