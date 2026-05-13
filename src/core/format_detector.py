"""
King_photo - 格式检测模块
通过文件头魔数检测真实文件格式
"""

import os
from typing import Optional, Tuple
from ..utils.constants import FILE_SIGNATURES, SUPPORTED_FORMATS


class FormatDetector:
    """文件格式检测器"""

    @staticmethod
    def detect_by_header(filepath: str) -> Optional[str]:
        """通过文件头检测真实格式"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(32)  # 读取前32字节

            if not header:
                return None

            # 检查各种格式的魔数
            for format_name, signatures in FILE_SIGNATURES.items():
                for sig in signatures:
                    if header.startswith(sig):
                        # 特殊处理WebP（需要检查WEBP标记）
                        if format_name == 'WebP' and len(header) >= 12:
                            if header[8:12] != b'WEBP':
                                continue
                        return format_name

            return None

        except Exception:
            return None

    @staticmethod
    def detect_by_extension(filepath: str) -> Optional[str]:
        """通过扩展名检测格式"""
        ext = os.path.splitext(filepath)[1].lower()

        for format_name, (extensions, _, _, _) in SUPPORTED_FORMATS.items():
            if ext in extensions:
                return format_name

        return None

    @staticmethod
    def get_real_format(filepath: str) -> Tuple[Optional[str], bool]:
        """获取真实格式，返回 (格式名, 是否与扩展名一致)"""
        header_format = FormatDetector.detect_by_header(filepath)
        ext_format = FormatDetector.detect_by_extension(filepath)

        # 优先使用文件头检测结果
        real_format = header_format or ext_format

        # 检查是否与扩展名一致
        is_consistent = (header_format is None or header_format == ext_format)

        return real_format, is_consistent

    @staticmethod
    def get_correct_extension(filepath: str) -> Optional[str]:
        """获取正确的文件扩展名"""
        format_name = FormatDetector.detect_by_header(filepath)

        if format_name and format_name in SUPPORTED_FORMATS:
            extensions = SUPPORTED_FORMATS[format_name][0]
            return extensions[0] if extensions else None

        return None

    @staticmethod
    def needs_exiftool(filepath: str) -> bool:
        """检查是否需要exiftool处理"""
        format_name = FormatDetector.detect_by_extension(filepath)

        if format_name and format_name in SUPPORTED_FORMATS:
            return SUPPORTED_FORMATS[format_name][3]

        return False

    @staticmethod
    def supports_exif(filepath: str) -> bool:
        """检查是否支持EXIF"""
        format_name = FormatDetector.detect_by_extension(filepath)

        if format_name and format_name in SUPPORTED_FORMATS:
            return SUPPORTED_FORMATS[format_name][1]

        return False

    @staticmethod
    def supports_xmp(filepath: str) -> bool:
        """检查是否支持XMP"""
        format_name = FormatDetector.detect_by_extension(filepath)

        if format_name and format_name in SUPPORTED_FORMATS:
            return SUPPORTED_FORMATS[format_name][2]

        return False

    @staticmethod
    def is_supported(filepath: str) -> bool:
        """检查文件是否为支持的图片格式"""
        ext = os.path.splitext(filepath)[1].lower()
        format_name = FormatDetector.detect_by_extension(filepath)
        return format_name is not None

    @staticmethod
    def get_format_info(filepath: str) -> dict:
        """获取格式详细信息"""
        format_name, is_consistent = FormatDetector.get_real_format(filepath)

        if format_name is None:
            return {
                'format': 'Unknown',
                'supports_exif': False,
                'supports_xmp': False,
                'needs_exiftool': False,
                'is_consistent': True,
            }

        supports_exif = False
        supports_xmp = False
        needs_exiftool = False

        if format_name in SUPPORTED_FORMATS:
            _, supports_exif, supports_xmp, needs_exiftool = SUPPORTED_FORMATS[format_name]

        return {
            'format': format_name,
            'supports_exif': supports_exif,
            'supports_xmp': supports_xmp,
            'needs_exiftool': needs_exiftool,
            'is_consistent': is_consistent,
        }
