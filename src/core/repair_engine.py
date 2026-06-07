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
from ..api.interfaces import IRepairEngine

# 获取日志记录器
logger = logging.getLogger(__name__)





class RepairEngine(IRepairEngine):
    """修复引擎，实现IRepairEngine接口"""

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
        output_dir: str = None,
        fix_extension: bool = True,
        fix_time: bool = True,
        time_source: str = 'auto',
        rename_format: str = '{datetime}',
        unprocessed_dir: str = None
    ) -> Dict[str, Any]:
        """
        修复文件（新逻辑：先检查并修复后缀 → 再修复时间）

        修复流程:
        1. 检查文件真实格式 → 若后缀不匹配则先修复后缀
        2. 在修正后缀后的文件上提取时间信息
        3. 写入元数据时间 + 设置文件时间 + 按时间重命名

        Args:
            filepath: 源文件路径
            output_dir: 输出目录
            fix_extension: 是否修复后缀
            fix_time: 是否修复时间
            time_source: 时间来源 ('auto', 'metadata', 'modified', 'created', 'custom')
            rename_format: 重命名格式
            unprocessed_dir: 未处理文件输出目录

        Returns:
            操作结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'message': '文件不存在'}

        # 确定输出目录
        if output_dir is None:
            output_dir = os.path.dirname(filepath)
        ensure_output_folder(output_dir)

        results = {'extension': None, 'time': None}
        actual_path = filepath

        # ============================================================
        # Phase 1: 格式检测 + 后缀修复
        # ============================================================
        header_format = FormatDetector.detect_by_header(filepath)
        ext_format = FormatDetector.detect_by_extension(filepath)

        # 检查是否为视频文件
        video_formats = ['MOV', 'MP4', 'AVI', 'WMV']
        if header_format in video_formats:
            # 视频文件 → 跳过或复制到未处理目录
            logger.warning(f"文件是视频格式 ({header_format})，非图片: {filepath}")
            if unprocessed_dir:
                try:
                    ensure_output_folder(unprocessed_dir)
                    dest = get_unique_filename(os.path.join(unprocessed_dir, os.path.basename(filepath)))
                    shutil.copy2(filepath, dest)
                    return {'success': False, 'skipped': True, 'unprocessed': True,
                            'message': f'视频文件已复制到未处理目录',
                            'error_type': 'not_image_file'}
                except Exception as e:
                    pass
            return {'success': False, 'skipped': True,
                    'message': f'文件是视频格式 ({header_format})',
                    'error_type': 'not_image_file'}

        # 后缀修复: 如果文件头格式与扩展名不一致
        needs_ext_fix = (header_format is not None and header_format != ext_format)

        if needs_ext_fix and fix_extension:
            logger.info(f"后缀不匹配: 文件头={header_format}, 扩展名={ext_format} → 修复中")
            ext_result = RepairEngine.fix_extension(filepath, output_dir)
            results['extension'] = ext_result
            if ext_result['success'] and not ext_result.get('skipped'):
                actual_path = ext_result['new_path']
                logger.info(f"后缀已修复: {os.path.basename(actual_path)}")
            elif ext_result.get('skipped'):
                results['extension'] = {'success': True, 'skipped': True, 'message': '后缀无需修复'}
        elif needs_ext_fix and not fix_extension:
            # 需要修复但用户禁用了
            results['extension'] = {'success': False, 'skipped': True,
                                    'message': f'后缀不匹配但已禁用修复'}
        else:
            # 后缀正确，直接复制（如果需要输出到不同目录）
            if output_dir != os.path.dirname(filepath):
                actual_path = os.path.join(output_dir, os.path.basename(filepath))
                actual_path = get_unique_filename(actual_path)
                shutil.copy2(filepath, actual_path)
            results['extension'] = {'success': True, 'skipped': True, 'message': '后缀正确'}

        # ============================================================
        # Phase 2: 时间修复（基于已修正后缀的文件）
        # ============================================================
        if fix_time and os.path.exists(actual_path):
            # 重新检测格式（后缀可能已修改，需要用新格式的方法写时间）
            current_format = FormatDetector.detect_by_header(actual_path)
            if not current_format:
                current_format = FormatDetector.detect_by_extension(actual_path)
            logger.info(f"时间修复阶段，文件格式: {current_format}, 路径: {os.path.basename(actual_path)}")

            time_info = RepairEngine.extract_time_info(actual_path, time_source)
            file_times = RepairEngine.get_file_times_info(actual_path)

            # 获取最佳时间
            photo_dt = time_info['best_match']
            if photo_dt is None:
                photo_dt = file_times['modified']
                time_info['source'] = 'file_modified'
                logger.info(f"未找到拍摄时间，使用文件修改时间: {photo_dt}")

            if photo_dt:
                ext = os.path.splitext(actual_path)[1].lower()
                original_name = os.path.splitext(os.path.basename(actual_path))[0]

                # 生成新文件名
                rename_meta = MetadataReader.read_metadata(actual_path)
                rename_meta['datetime'] = photo_dt
                new_filename = generate_renamed_filename(original_name, rename_format, rename_meta, 1, ext)
                new_filepath = get_unique_filename(os.path.join(output_dir, new_filename))

                try:
                    shutil.copy2(actual_path, new_filepath)

                    # 写入元数据时间
                    time_metadata = {
                        'datetime': photo_dt,
                        'datetime_original': photo_dt,
                        'datetime_digitized': photo_dt,
                        'creation_time': photo_dt
                    }
                    write_result = MetadataWriter.write_metadata(new_filepath, time_metadata, copy_mode=False)
                    if write_result['success']:
                        logger.info(f"元数据时间写入成功: {os.path.basename(new_filepath)}")
                    else:
                        logger.warning(f"元数据时间写入失败: {os.path.basename(new_filepath)}, {write_result.get('message')}")

                    # 设置文件系统时间（创建时间 + 修改时间）
                    set_file_times(new_filepath, photo_dt, set_created=True)

                    # 删除中间文件
                    if actual_path != filepath and os.path.exists(actual_path) and os.path.exists(new_filepath):
                        try:
                            os.remove(actual_path)
                        except Exception:
                            logger.debug(f"中间文件清理失败: {actual_path}", exc_info=True)

                    results['time'] = {
                        'success': True,
                        'new_path': new_filepath,
                        'datetime': photo_dt,
                        'source': time_info['source'],
                        'message': '时间修复成功'
                    }
                    actual_path = new_filepath

                except Exception as e:
                    logger.error(f"时间修复失败: {actual_path}, {e}")
                    results['time'] = {'success': False, 'message': str(e)}
            else:
                results['time'] = {'success': False, 'message': '无法获取时间信息'}

        # ============================================================
        # 判断结果
        # ============================================================
        ext_ok = (not fix_extension) or (results['extension'] and results['extension'].get('success'))
        time_ok = (not fix_time) or (results['time'] and results['time'].get('success'))
        operation_success = ext_ok and time_ok

        return {
            'success': operation_success,
            'details': results,
            'output_path': actual_path,
            'message': '修复完成' if operation_success else '部分修复失败'
        }

    @staticmethod
    def batch_repair(
        file_list: List[str],
        output_dir: str = None,
        fix_extension: bool = True,
        fix_time: bool = True,
        time_source: str = 'auto',
        rename_format: str = '{datetime}',
        progress_callback: Callable = None,
        unprocessed_dir: str = None
    ) -> Dict[str, Any]:
        """
        批量修复

        Args:
            file_list: 文件列表
            output_dir: 输出目录
            fix_extension: 是否修复后缀
            fix_time: 是否修复时间
            time_source: 时间来源
            rename_format: 重命名格式
            progress_callback: 进度回调
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
                filepath=filepath,
                output_dir=output_dir,
                fix_extension=fix_extension,
                fix_time=fix_time,
                time_source=time_source,
                rename_format=rename_format,
                unprocessed_dir=unprocessed_dir
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
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        批量修复后缀

        Args:
            file_list: 文件列表
            output_dir: 输出目录
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
