"""
King_photo - ExifTool 封装
用于处理特殊格式图片（HEIC、RAW、PSD等）的元信息
"""

import json
import os
import subprocess
import shutil
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class ExifToolWrapper:
    """ExifTool命令行工具封装"""

    def __init__(self):
        self.exiftool_path = self._find_exiftool()
        self._available = self.exiftool_path is not None

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
            cmd = [
                self.exiftool_path,
                '-json',
                '-G',  # 显示分组名
                '-n',  # 数值格式
                filepath
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                if data:
                    return data[0]

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            pass

        return {}

    def write_metadata(self, filepath: str, metadata: Dict[str, str]) -> bool:
        """写入元信息"""
        if not self._available:
            return False

        try:
            cmd = [self.exiftool_path, '-overwrite_original']

            for key, value in metadata.items():
                cmd.append(f'-{key}={value}')

            cmd.append(filepath)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            return result.returncode == 0

        except Exception:
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
