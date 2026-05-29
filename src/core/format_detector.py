"""
King_photo - 格式检测模块
通过文件头魔数检测真实文件格式
"""

import logging
import os
from typing import Optional, Tuple, Dict, Any
from ..utils.constants import FILE_SIGNATURES, SUPPORTED_FORMATS
from ..api.interfaces import IFormatDetector

# 获取日志记录器
logger = logging.getLogger(__name__)


class FormatDetector(IFormatDetector):
    """文件格式检测器，实现IFormatDetector接口"""
    
    # 动态注册的格式配置
    _custom_formats: Dict[str, Dict[str, Any]] = {}

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

        except Exception as e:
            logger.debug(f"文件头检测失败: {filepath}, 错误: {str(e)}")
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
        # 如果文件头检测到格式，必须与扩展名格式一致
        # 如果文件头检测不到格式，则认为一致（因为无法判断）
        if header_format is not None:
            is_consistent = (header_format == ext_format)
        else:
            # 文件头检测不到格式，检查扩展名是否有效
            is_consistent = (ext_format is not None)

        return real_format, is_consistent

    @staticmethod
    def get_correct_extension(filepath: str) -> Optional[str]:
        """获取正确的文件扩展名"""
        # 首先尝试文件头检测
        format_name = FormatDetector.detect_by_header(filepath)
        
        # 如果文件头检测不到，使用扩展名检测
        if not format_name:
            format_name = FormatDetector.detect_by_extension(filepath)

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
    def is_truly_image(filepath: str) -> Tuple[bool, str]:
        """
        检查文件是否真的是图片格式，而不是被错误标记的视频或其他文件
        
        Args:
            filepath: 文件路径
        
        Returns:
            (是否为真正的图片, 真实格式或错误信息)
        """
        try:
            # 检查文件头
            header_format = FormatDetector.detect_by_header(filepath)
            ext_format = FormatDetector.detect_by_extension(filepath)
            
            # 如果文件头检测到视频格式，返回错误
            video_formats = ['MOV', 'MP4', 'AVI', 'WMV']
            if header_format in video_formats:
                return False, f"文件实际上是{header_format}视频，不是图片"
            
            # 如果文件头检测到图片格式，检查是否与扩展名一致
            if header_format:
                if header_format == ext_format:
                    return True, header_format
                else:
                    # 文件头格式与扩展名不一致，但仍然是图片格式
                    # 返回True，让修复引擎处理后缀修复
                    return True, f"文件头格式为{header_format}，但扩展名标记为{ext_format or '未知'}"
            
            # 如果文件头检测不到格式，但扩展名是支持的图片格式
            if ext_format:
                return True, ext_format
            
            # 无法识别格式
            return False, "无法识别文件格式"
            
        except Exception as e:
            logger.debug(f"检查文件是否为图片失败: {filepath}, 错误: {str(e)}")
            return False, f"检查失败: {str(e)}"
    
    @staticmethod
    def is_video_file(filepath: str) -> Tuple[bool, str]:
        """
        检查文件是否是视频文件
        
        Args:
            filepath: 文件路径
        
        Returns:
            (是否为视频, 视频格式或错误信息)
        """
        try:
            # 检查文件头
            header_format = FormatDetector.detect_by_header(filepath)
            ext_format = FormatDetector.detect_by_extension(filepath)
            
            # 视频格式列表
            video_formats = ['MOV', 'MP4', 'AVI', 'WMV']
            
            # 检查文件头是否为视频格式
            if header_format in video_formats:
                return True, header_format
            
            # 检查扩展名是否为视频格式
            video_extensions = ['.mov', '.mp4', '.avi', '.wmv', '.mkv', '.flv', '.webm']
            ext = os.path.splitext(filepath)[1].lower()
            if ext in video_extensions:
                return True, ext[1:].upper()
            
            return False, "不是视频文件"
            
        except Exception as e:
            logger.debug(f"检查文件是否为视频失败: {filepath}, 错误: {str(e)}")
            return False, f"检查失败: {str(e)}"
    
    @staticmethod
    def get_file_type_category(filepath: str) -> str:
        """
        获取文件类型分类
        
        Args:
            filepath: 文件路径
        
        Returns:
            文件类型分类: 'image', 'video', 'unknown'
        """
        # 检查是否为图片
        is_image, _ = FormatDetector.is_truly_image(filepath)
        if is_image:
            return 'image'
        
        # 检查是否为视频
        is_video, _ = FormatDetector.is_video_file(filepath)
        if is_video:
            return 'video'
        
        return 'unknown'

    @staticmethod
    def get_format_info(filepath: str) -> dict:
        """获取格式详细信息"""
        format_name, is_consistent = FormatDetector.get_real_format(filepath)
        
        # 获取扩展名
        ext = os.path.splitext(filepath)[1].lower()
        
        # 检查是否为图片或视频
        is_image, _ = FormatDetector.is_truly_image(filepath)
        is_video, _ = FormatDetector.is_video_file(filepath)

        if format_name is None:
            return {
                'format': 'Unknown',
                'extension': ext,
                'is_image': is_image,
                'is_video': is_video,
                'exif_support': False,
                'xmp_support': False,
                'need_exiftool': False,
                'is_consistent': is_consistent,
            }

        supports_exif = False
        supports_xmp = False
        needs_exiftool = False

        if format_name in SUPPORTED_FORMATS:
            _, supports_exif, supports_xmp, needs_exiftool = SUPPORTED_FORMATS[format_name]
        elif format_name in FormatDetector._custom_formats:
            # 使用自定义格式配置
            config = FormatDetector._custom_formats[format_name]
            supports_exif = config.get('exif_support', False)
            supports_xmp = config.get('xmp_support', False)
            needs_exiftool = config.get('need_exiftool', False)

        return {
            'format': format_name,
            'extension': ext,
            'is_image': is_image,
            'is_video': is_video,
            'exif_support': supports_exif,
            'xmp_support': supports_xmp,
            'need_exiftool': needs_exiftool,
            'is_consistent': is_consistent,
        }
    
    @staticmethod
    def register_format(format_name: str, format_config: Dict[str, Any]) -> None:
        """
        注册新格式（插件机制）
        
        Args:
            format_name: 格式名称
            format_config: 格式配置，包含：
                - extensions: 扩展名列表
                - magic_numbers: 文件头魔数列表
                - exif_support: 是否支持EXIF
                - xmp_support: 是否支持XMP
                - need_exiftool: 是否需要ExifTool
        """
        # 验证配置格式
        required_keys = ['extensions', 'exif_support', 'xmp_support', 'need_exiftool']
        for key in required_keys:
            if key not in format_config:
                raise ValueError(f"格式配置缺少必要字段: {key}")
        
        # 存储格式配置
        FormatDetector._custom_formats[format_name] = format_config
        
        # 更新常量中的SUPPORTED_FORMATS
        from ..utils.constants import SUPPORTED_FORMATS, FILE_SIGNATURES, ALL_EXTENSIONS
        
        # 添加到SUPPORTED_FORMATS
        extensions = format_config['extensions']
        exif_support = format_config['exif_support']
        xmp_support = format_config['xmp_support']
        need_exiftool = format_config['need_exiftool']
        
        SUPPORTED_FORMATS[format_name] = (extensions, exif_support, xmp_support, need_exiftool)
        
        # 添加到ALL_EXTENSIONS
        ALL_EXTENSIONS.extend(extensions)
        
        # 如果提供了魔数，添加到FILE_SIGNATURES
        if 'magic_numbers' in format_config:
            FILE_SIGNATURES[format_name] = format_config['magic_numbers']
        
        logger.info(f"已注册新格式: {format_name}")
    
    @staticmethod
    def get_supported_formats() -> Dict[str, Dict[str, Any]]:
        """
        获取所有支持的格式
        
        Returns:
            格式字典，键为格式名称，值为格式配置
        """
        from ..utils.constants import SUPPORTED_FORMATS
        
        formats = {}
        
        # 添加内置格式
        for format_name, (extensions, exif_support, xmp_support, need_exiftool) in SUPPORTED_FORMATS.items():
            formats[format_name] = {
                'extensions': extensions,
                'exif_support': exif_support,
                'xmp_support': xmp_support,
                'need_exiftool': need_exiftool,
                'is_custom': False
            }
        
        # 添加自定义格式
        for format_name, config in FormatDetector._custom_formats.items():
            formats[format_name] = {
                **config,
                'is_custom': True
            }
        
        return formats
