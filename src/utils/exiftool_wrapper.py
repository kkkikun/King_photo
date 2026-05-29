"""
King_photo - ExifTool 封装
用于处理特殊格式图片（HEIC、RAW、PSD等）的元信息
"""

import json
import logging
import os
import subprocess
import shutil
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

# 获取日志记录器
logger = logging.getLogger(__name__)


class ExifToolWrapper:
    """ExifTool命令行工具封装"""

    def __init__(self):
        self.exiftool_path = self._find_exiftool()
        self._available = self.exiftool_path is not None

    def _build_exiftool_args(self, metadata: Dict[str, str] = None, extra_args: list = None) -> List[str]:
        """构建ExifTool参数列表（不含文件路径和exiftool路径）
        
        这些参数将通过 argfile 传递给 ExifTool，避免命令行编码问题。
        """
        args = ['-overwrite_original']
        
        # 添加charset选项
        args.extend(['-charset', 'filename=utf8'])
        args.extend(['-charset', 'utf8'])
        
        # 添加元数据参数
        if metadata:
            for key, value in metadata.items():
                args.append(f'-{key}={value}')
        
        # 添加额外参数
        if extra_args:
            args.extend(extra_args)
        
        return args

    def _run_exiftool(self, args: List[str], filepath: str, log_prefix: str = "") -> bool:
        """通过argfile运行ExifTool，彻底避免命令行中文编码问题
        
        将所有参数和文件路径写入UTF-8编码的临时文件，通过 -@ argfile 传递给ExifTool。
        这样ExifTool直接从文件读取UTF-8编码的参数，不经过Windows命令行编码转换。
        
        Args:
            args: ExifTool参数列表（不含文件路径）
            filepath: 要处理的文件路径
            log_prefix: 日志前缀，用于区分不同的操作类型
            
        Returns:
            bool: 是否成功
        """
        argfile_path = None
        try:
            # 创建临时argfile，使用UTF-8编码
            fd, argfile_path = tempfile.mkstemp(suffix='.txt', prefix='exiftool_args_')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                # 写入所有参数，每行一个
                for arg in args:
                    f.write(f'{arg}\n')
                # 写入文件路径（最后一行）
                f.write(filepath)
            
            # 构建ExifTool命令：exiftool -@ argfile
            cmd = [self.exiftool_path, '-@', argfile_path]
            
            logger.info(f"ExifTool {log_prefix}命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                logger.warning(f"ExifTool {log_prefix}失败: {filepath}, 错误: {result.stderr}")
            else:
                logger.debug(f"ExifTool {log_prefix}成功: {filepath}")
            
            return result.returncode == 0

        except Exception as e:
            logger.error(f"ExifTool {log_prefix}异常: {filepath}, 错误: {str(e)}")
            return False
        finally:
            # 清理临时文件
            if argfile_path and os.path.exists(argfile_path):
                try:
                    os.unlink(argfile_path)
                except OSError:
                    pass

    def _find_exiftool(self) -> Optional[str]:
        """查找exiftool可执行文件"""
        # 1. 检查系统PATH
        exiftool = shutil.which('exiftool')
        if exiftool:
            return exiftool

        # 2. 检查常见安装位置
        common_paths = [
            r'C:\Program Files\exiftool\exiftool.exe',
            r'C:\Program Files (x86)\exiftool\exiftool.exe',
            r'C:\exiftool\exiftool.exe',
            os.path.expanduser(r'~\exiftool\exiftool.exe'),
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    @property
    def is_available(self) -> bool:
        """检查exiftool是否可用"""
        return self._available

    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        """读取图片元信息"""
        if not self._available:
            return {}

        try:
            # 构建参数列表
            args = self._build_exiftool_args(
                extra_args=['-json', '-G', '-n']
            )

            # 通过argfile运行，获取原始输出
            argfile_path = None
            try:
                fd, argfile_path = tempfile.mkstemp(suffix='.txt', prefix='exiftool_args_')
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    for arg in args:
                        f.write(f'{arg}\n')
                    f.write(filepath)
                
                cmd = [self.exiftool_path, '-@', argfile_path]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding='utf-8',
                    errors='replace'
                )

                if result.returncode == 0 and result.stdout:
                    data = json.loads(result.stdout)
                    if data:
                        return data[0]

            finally:
                if argfile_path and os.path.exists(argfile_path):
                    try:
                        os.unlink(argfile_path)
                    except OSError:
                        pass

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.error(f"ExifTool读取元信息失败: {filepath}, 错误: {str(e)}")

        return {}

    def write_metadata(self, filepath: str, metadata: Dict[str, str]) -> bool:
        """写入元信息"""
        if not self._available:
            return False

        try:
            # 获取文件扩展名
            ext = os.path.splitext(filepath)[1].lower()
            
            # 对于PNG文件，使用指定XMP命名空间的命令
            if ext == '.png':
                logger.info(f"PNG文件，使用XMP命名空间命令: {filepath}")
                return self._write_metadata_for_png(filepath, metadata)
            
            # 构建参数列表
            args = self._build_exiftool_args(metadata=metadata)
            
            return self._run_exiftool(args, filepath, log_prefix="写入")

        except Exception as e:
            logger.error(f"ExifTool写入元信息失败: {filepath}, 错误: {str(e)}")
            return False
    
    def _write_metadata_for_png(self, filepath: str, metadata: Dict[str, str]) -> bool:
        """为PNG文件写入元信息，使用指定XMP命名空间的命令"""
        try:
            # 构建PNG特定的元数据
            png_metadata = {}
            
            # 字段映射：内部名 -> ExifTool XMP命名空间标签名
            # PNG文件使用XMP格式，需要指定命名空间
            field_mapping = {
                'CreateDate': 'XMP-xmp:CreateDate',
                'ModifyDate': 'XMP-xmp:ModifyDate',
                'DateTimeOriginal': 'XMP-exif:DateTimeOriginal',
                'DateTimeDigitized': 'XMP-exif:DateTimeDigitized',
                # 添加photoshop:DateCreated映射，这是PNG等纯XMP格式的标准拍摄时间字段
                'DateCreated': 'XMP-photoshop:DateCreated',
            }
            
            for key, value in metadata.items():
                if key in field_mapping:
                    png_metadata[field_mapping[key]] = value
                else:
                    png_metadata[key] = value
            
            # 特殊处理时间字段：同时写入多个XMP命名空间字段，确保兼容性
            # 确保Windows资源管理器能正确显示拍摄时间
            if 'DateTimeOriginal' in metadata:
                value = metadata['DateTimeOriginal']
                # 添加XMP-photoshop:DateCreated字段（PNG标准拍摄时间字段）
                png_metadata['XMP-photoshop:DateCreated'] = value
            
            # 处理CreateDate：同时写入XMP-xmp:CreateDate和XMP-photoshop:DateCreated
            if 'CreateDate' in metadata:
                value = metadata['CreateDate']
                # 确保XMP-xmp:CreateDate字段（标准创建时间）
                png_metadata['XMP-xmp:CreateDate'] = value
                # 同时添加XMP-photoshop:DateCreated字段（PNG标准拍摄时间字段）
                png_metadata['XMP-photoshop:DateCreated'] = value
            
            # 构建参数列表
            args = self._build_exiftool_args(metadata=png_metadata)
            
            return self._run_exiftool(args, filepath, log_prefix="PNG写入")
            
        except Exception as e:
            logger.error(f"ExifTool写入PNG元信息失败: {filepath}, 错误: {str(e)}")
            return False

    def copy_filetime_to_exif(self, filepath: str) -> bool:
        """将文件修改时间复制到EXIF DateTimeOriginal"""
        if not self._available:
            return False

        try:
            # 获取文件扩展名
            ext = os.path.splitext(filepath)[1].lower()
            
            # 对于JPG/JPEG文件，使用DateTimeOriginal<FileModifyDate模式
            if ext in ['.jpg', '.jpeg']:
                args = self._build_exiftool_args(
                    extra_args=['-DateTimeOriginal<FileModifyDate', '-m']
                )
                result = self._run_exiftool(args, filepath, log_prefix="复制时间到EXIF")
                if result:
                    logger.info(f"成功将文件修改时间复制到EXIF DateTimeOriginal: {filepath}")
                return result
            
            # 对于PNG文件，将文件修改时间复制到XMP时间字段
            elif ext == '.png':
                args = self._build_exiftool_args(
                    extra_args=['-XMP-xmp:ModifyDate<FileModifyDate', '-XMP-xmp:CreateDate<FileModifyDate', '-m']
                )
                result = self._run_exiftool(args, filepath, log_prefix="复制时间到PNG XMP")
                if result:
                    logger.info(f"成功将文件修改时间复制到PNG XMP时间字段: {filepath}")
                return result
            
            # 对于其他格式，尝试通用方法
            else:
                args = self._build_exiftool_args(
                    extra_args=['-DateTimeOriginal<FileModifyDate', '-m']
                )
                return self._run_exiftool(args, filepath, log_prefix="复制时间")

        except Exception as e:
            logger.error(f"ExifTool复制文件时间失败: {filepath}, 错误: {str(e)}")
            return False

    def fix_filename_extension(self, filepath: str) -> bool:
        """修复文件扩展名"""
        if not self._available:
            return False

        try:
            # 构建参数列表
            args = self._build_exiftool_args(
                extra_args=['-FileName<%f.$FileTypeExtension', '-m']
            )
            
            result = self._run_exiftool(args, filepath, log_prefix="修复扩展名")
            if result:
                logger.info(f"成功修复文件扩展名: {filepath}")
            return result

        except Exception as e:
            logger.error(f"ExifTool修复文件扩展名失败: {filepath}, 错误: {str(e)}")
            return False

    def rename_by_modification_time(self, filepath: str) -> bool:
        """根据修改时间重命名文件"""
        if not self._available:
            return False

        try:
            # 构建参数列表
            args = self._build_exiftool_args(
                extra_args=['-FileName<FileModifyDate.$FileTypeExtension', '-m']
            )
            
            result = self._run_exiftool(args, filepath, log_prefix="按时间重命名")
            if result:
                logger.info(f"成功根据修改时间重命名文件: {filepath}")
            return result

        except Exception as e:
            logger.error(f"ExifTool根据修改时间重命名文件失败: {filepath}, 错误: {str(e)}")
            return False

    def get_datetime(self, filepath: str) -> Optional[datetime]:
        """获取拍摄时间"""
        metadata = self.read_metadata(filepath)

        # 按优先级查找时间字段
        time_fields = [
            'EXIF:DateTimeOriginal',
            'EXIF:DateTimeDigitized',
            'EXIF:DateTime',
            'XMP:CreateDate',
            'XMP:ModifyDate',
            'QuickTime:CreateDate',
            'QuickTime:ModifyDate',
        ]

        for field in time_fields:
            if field in metadata:
                dt_str = metadata[field]
                dt = self._parse_datetime(dt_str)
                if dt:
                    return dt

        return None

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """解析时间字符串"""
        if not dt_str or dt_str == '0000:00:00 00:00:00':
            return None

        formats = [
            '%Y:%m:%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def get_basic_info(self, filepath: str) -> Dict[str, Any]:
        """获取基本信息"""
        metadata = self.read_metadata(filepath)

        info = {
            'width': metadata.get('File:ImageWidth', 0),
            'height': metadata.get('File:ImageHeight', 0),
            'make': metadata.get('EXIF:Make', ''),
            'model': metadata.get('EXIF:Model', ''),
            'software': metadata.get('EXIF:Software', ''),
            'artist': metadata.get('EXIF:Artist', ''),
            'copyright': metadata.get('EXIF:Copyright', ''),
            'description': metadata.get('EXIF:ImageDescription', ''),
            'lens': metadata.get('EXIF:LensModel', ''),
            'fnumber': metadata.get('EXIF:FNumber', ''),
            'exposure': metadata.get('EXIF:ExposureTime', ''),
            'iso': metadata.get('EXIF:ISO', ''),
            'focal_length': metadata.get('EXIF:FocalLength', ''),
        }

        return info


# 全局单例
_exiftool_instance = None


def get_exiftool() -> ExifToolWrapper:
    """获取ExifTool单例"""
    global _exiftool_instance
    if _exiftool_instance is None:
        _exiftool_instance = ExifToolWrapper()
    return _exiftool_instance
