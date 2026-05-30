"""
King_photo - EXIF处理模块
处理JPEG、TIFF等格式的EXIF元信息
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

import piexif
from PIL import Image

from ..utils.constants import EXIF_TIME_FIELDS, INTERNAL_TO_EXIFTOOL

# 获取日志记录器
logger = logging.getLogger(__name__)


class ExifHandler:
    """EXIF元信息处理器"""

    @staticmethod
    def read_exif(filepath: str) -> Dict[str, Any]:
        """读取EXIF信息"""
        result = {}

        try:
            # 使用piexif读取
            exif_dict = piexif.load(filepath)

            # 读取基本信息
            if piexif.ImageIFD.Make in exif_dict.get("0th", {}):
                result['make'] = exif_dict["0th"][piexif.ImageIFD.Make].decode('utf-8', errors='ignore').strip('\x00')

            if piexif.ImageIFD.Model in exif_dict.get("0th", {}):
                result['model'] = exif_dict["0th"][piexif.ImageIFD.Model].decode('utf-8', errors='ignore').strip('\x00')

            if piexif.ImageIFD.Software in exif_dict.get("0th", {}):
                result['software'] = exif_dict["0th"][piexif.ImageIFD.Software].decode('utf-8', errors='ignore').strip('\x00')

            if piexif.ImageIFD.Artist in exif_dict.get("0th", {}):
                result['artist'] = exif_dict["0th"][piexif.ImageIFD.Artist].decode('utf-8', errors='ignore').strip('\x00')

            if piexif.ImageIFD.Copyright in exif_dict.get("0th", {}):
                result['copyright'] = exif_dict["0th"][piexif.ImageIFD.Copyright].decode('utf-8', errors='ignore').strip('\x00')

            if piexif.ImageIFD.ImageDescription in exif_dict.get("0th", {}):
                result['description'] = exif_dict["0th"][piexif.ImageIFD.ImageDescription].decode('utf-8', errors='ignore').strip('\x00')

            # 读取图片尺寸
            if piexif.ImageIFD.ImageWidth in exif_dict.get("0th", {}):
                result['width'] = exif_dict["0th"][piexif.ImageIFD.ImageWidth]

            if piexif.ImageIFD.ImageLength in exif_dict.get("0th", {}):
                result['height'] = exif_dict["0th"][piexif.ImageIFD.ImageLength]

            # 读取拍摄参数
            exif_ifd = exif_dict.get("Exif", {})

            if piexif.ExifIFD.ExposureTime in exif_ifd:
                exp = exif_ifd[piexif.ExifIFD.ExposureTime]
                if isinstance(exp, tuple):
                    result['exposure_time'] = f"{exp[0]}/{exp[1]}"
                else:
                    result['exposure_time'] = str(exp)

            if piexif.ExifIFD.FNumber in exif_ifd:
                fn = exif_ifd[piexif.ExifIFD.FNumber]
                if isinstance(fn, tuple):
                    result['fnumber'] = f"f/{fn[0]/fn[1]:.1f}"
                else:
                    result['fnumber'] = f"f/{fn}"

            if piexif.ExifIFD.ISOSpeedRatings in exif_ifd:
                result['iso'] = str(exif_ifd[piexif.ExifIFD.ISOSpeedRatings])

            if piexif.ExifIFD.FocalLength in exif_ifd:
                fl = exif_ifd[piexif.ExifIFD.FocalLength]
                if isinstance(fl, tuple):
                    result['focal_length'] = f"{fl[0]/fl[1]:.0f}mm"
                else:
                    result['focal_length'] = f"{fl}mm"

            if piexif.ExifIFD.LensModel in exif_ifd:
                result['lens'] = exif_ifd[piexif.ExifIFD.LensModel].decode('utf-8', errors='ignore').strip('\x00')

            # 读取时间信息
            result['datetime'] = ExifHandler._get_datetime(exif_ifd)

            # 读取方向
            if piexif.ImageIFD.Orientation in exif_dict.get("0th", {}):
                result['orientation'] = exif_dict["0th"][piexif.ImageIFD.Orientation]

        except Exception as e:
            logger.debug(f"使用piexif读取EXIF信息失败: {filepath}, 错误: {str(e)}")
            # 立即尝试使用exiftool作为回退
            try:
                from ..utils.exiftool_wrapper import get_exiftool
                et = get_exiftool()
                if et.is_available:
                    metadata = et.read_metadata(filepath)
                    if metadata:
                        # 转换exiftool的元数据格式
                        if 'EXIF:Make' in metadata:
                            result['make'] = metadata['EXIF:Make']
                        if 'EXIF:Model' in metadata:
                            result['model'] = metadata['EXIF:Model']
                        if 'EXIF:Software' in metadata:
                            result['software'] = metadata['EXIF:Software']
                        if 'EXIF:Artist' in metadata:
                            result['artist'] = metadata['EXIF:Artist']
                        if 'EXIF:Copyright' in metadata:
                            result['copyright'] = metadata['EXIF:Copyright']
                        if 'EXIF:ImageDescription' in metadata:
                            result['description'] = metadata['EXIF:ImageDescription']
                        if 'File:ImageWidth' in metadata:
                            result['width'] = metadata['File:ImageWidth']
                        if 'File:ImageHeight' in metadata:
                            result['height'] = metadata['File:ImageHeight']
                        if 'EXIF:ExposureTime' in metadata:
                            result['exposure_time'] = metadata['EXIF:ExposureTime']
                        if 'EXIF:FNumber' in metadata:
                            result['fnumber'] = f"f/{metadata['EXIF:FNumber']}"
                        if 'EXIF:ISO' in metadata:
                            result['iso'] = str(metadata['EXIF:ISO'])
                        if 'EXIF:FocalLength' in metadata:
                            result['focal_length'] = f"{metadata['EXIF:FocalLength']}mm"
                        if 'EXIF:LensModel' in metadata:
                            result['lens'] = metadata['EXIF:LensModel']
                        # 获取时间
                        dt = et.get_datetime(filepath)
                        if dt:
                            result['datetime'] = dt
                        if 'EXIF:Orientation' in metadata:
                            result['orientation'] = metadata['EXIF:Orientation']
                        logger.info(f"使用exiftool成功读取EXIF信息: {filepath}")
            except Exception as exiftool_error:
                logger.warning(f"使用exiftool读取EXIF也失败: {filepath}, 错误: {str(exiftool_error)}")

        return result

    @staticmethod
    def _get_datetime(exif_ifd: dict) -> Optional[datetime]:
        """从EXIF获取拍摄时间"""
        for tag_id in EXIF_TIME_FIELDS:
            if tag_id in exif_ifd:
                dt_str = exif_ifd[tag_id]
                if isinstance(dt_str, bytes):
                    dt_str = dt_str.decode('utf-8', errors='ignore')
                dt_str = dt_str.strip('\x00').strip()

                try:
                    return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    continue

        return None

    @staticmethod
    def write_exif(filepath: str, metadata: Dict[str, str]) -> bool:
        """写入EXIF信息"""
        # 检查文件是否真的是图片格式
        from .format_detector import FormatDetector
        is_image, image_check_msg = FormatDetector.is_truly_image(filepath)
        if not is_image:
            logger.warning(f"文件不是真正的图片格式: {filepath}, {image_check_msg}")
            return False
        
        # 对于PNG文件，直接使用exiftool写入，因为PNG不支持EXIF
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.png':
            # 尝试使用exiftool写入
            try:
                from ..utils.exiftool_wrapper import get_exiftool
                et = get_exiftool()
                if et.is_available:
                    # 转换字段名（内部名 -> ExifTool标签名）
                    et_metadata = {}
                    for key, value in metadata.items():
                        key_lower = key.lower()
                        if key_lower in INTERNAL_TO_EXIFTOOL:
                            if isinstance(value, datetime):
                                value = value.strftime("%Y:%m:%d %H:%M:%S")
                            et_metadata[INTERNAL_TO_EXIFTOOL[key_lower]] = str(value)
                    
                    # 对于PNG，需要设置ModifyDate字段（xmp:ModifyDate）
                    if 'DateTimeOriginal' in et_metadata:
                        et_metadata['ModifyDate'] = et_metadata['DateTimeOriginal']
                    
                    # 对于PNG，需要设置CreateDate字段（xmp:CreateDate）
                    if 'CreateDate' not in et_metadata and 'DateTimeOriginal' in et_metadata:
                        et_metadata['CreateDate'] = et_metadata['DateTimeOriginal']
                    
                    if et.write_metadata(filepath, et_metadata):
                        logger.info(f"使用exiftool成功写入EXIF信息: {filepath}")
                        return True
                    else:
                        # 如果exiftool写入失败，尝试使用copy_filetime_to_exif
                        if 'datetime_original' in metadata or 'datetime' in metadata:
                            return et.copy_filetime_to_exif(filepath)
                else:
                    logger.warning("ExifTool不可用，无法写入PNG EXIF信息")
            except Exception as exiftool_error:
                logger.warning(f"使用exiftool写入PNG EXIF也失败: {filepath}, 错误: {str(exiftool_error)}")
            return False
        
        # 对于其他文件（JPEG/TIFF等），尝试使用piexif
        try:
            exif_dict = piexif.load(filepath)

            # 写入支持的字段（EXIF标准字段映射）
            # 标签ID参考: https://exiftool.org/TagNames/EXIF.html
            field_mapping = {
                # IFD0 (主IFD) - 基本信息
                'artist': (piexif.ImageIFD.Artist, "0th"),           # Tag 315
                'copyright': (piexif.ImageIFD.Copyright, "0th"),     # Tag 33432
                'description': (piexif.ImageIFD.ImageDescription, "0th"),  # Tag 270
                'make': (piexif.ImageIFD.Make, "0th"),               # Tag 271
                'model': (piexif.ImageIFD.Model, "0th"),             # Tag 272
                'software': (piexif.ImageIFD.Software, "0th"),       # Tag 305
                'datetime': (piexif.ImageIFD.DateTime, "0th"),       # Tag 306 (EXIF规范中的DateTime)
                'orientation': (piexif.ImageIFD.Orientation, "0th"), # Tag 274
                # ExifIFD - 拍摄信息
                'datetime_original': (piexif.ExifIFD.DateTimeOriginal, "Exif"),   # Tag 36867 (拍摄时间)
                'datetime_digitized': (piexif.ExifIFD.DateTimeDigitized, "Exif"), # Tag 36868 (数字化时间)
                'lens': (piexif.ExifIFD.LensModel, "Exif"),         # Tag 42036
            }

            for key, value in metadata.items():
                key_lower = key.lower()
                if key_lower in field_mapping:
                    tag_id, ifd_name = field_mapping[key_lower]
                    if isinstance(value, str):
                        value = value.encode('utf-8')
                    exif_dict[ifd_name][tag_id] = value

            # 保存
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, filepath)

            return True

        except Exception as e:
            logger.debug(f"使用piexif写入EXIF信息失败: {filepath}, 错误: {str(e)}")
            # 立即尝试使用exiftool作为回退
            try:
                from ..utils.exiftool_wrapper import get_exiftool
                et = get_exiftool()
                if et.is_available:
                    # 转换字段名（内部名 -> ExifTool标签名）
                    et_metadata = {}
                    for key, value in metadata.items():
                        key_lower = key.lower()
                        if key_lower in INTERNAL_TO_EXIFTOOL:
                            if isinstance(value, datetime):
                                value = value.strftime("%Y:%m:%d %H:%M:%S")
                            et_metadata[INTERNAL_TO_EXIFTOOL[key_lower]] = str(value)
                    
                    if et.write_metadata(filepath, et_metadata):
                        logger.info(f"使用exiftool成功写入EXIF信息: {filepath}")
                        return True
                    else:
                        # 如果exiftool写入失败，尝试使用copy_filetime_to_exif
                        if 'datetime_original' in metadata or 'datetime' in metadata:
                            return et.copy_filetime_to_exif(filepath)
            except Exception as exiftool_error:
                logger.warning(f"使用exiftool写入EXIF也失败: {filepath}, 错误: {str(exiftool_error)}")
            
            return False

    @staticmethod
    def get_datetime(filepath: str) -> Optional[datetime]:
        """快速获取拍摄时间"""
        try:
            exif_dict = piexif.load(filepath)
            exif_ifd = exif_dict.get("Exif", {})

            return ExifHandler._get_datetime(exif_ifd)

        except Exception as e:
            logger.debug(f"使用piexif获取EXIF时间失败: {filepath}, 错误: {str(e)}")
            # 立即尝试使用exiftool
            try:
                from ..utils.exiftool_wrapper import get_exiftool
                et = get_exiftool()
                if et.is_available:
                    dt = et.get_datetime(filepath)
                    if dt:
                        return dt
            except Exception as exiftool_error:
                logger.debug(f"使用exiftool获取EXIF时间也失败: {filepath}, 错误: {str(exiftool_error)}")
            return None

    @staticmethod
    def has_exif(filepath: str) -> bool:
        """检查文件是否包含EXIF数据"""
        try:
            exif_dict = piexif.load(filepath)
            return bool(exif_dict.get("0th")) or bool(exif_dict.get("Exif"))
        except Exception as e:
            logger.debug(f"使用piexif检查EXIF数据失败: {filepath}, 错误: {str(e)}")
            # 立即尝试使用exiftool
            try:
                from ..utils.exiftool_wrapper import get_exiftool
                et = get_exiftool()
                if et.is_available:
                    metadata = et.read_metadata(filepath)
                    if metadata:
                        # 检查是否有EXIF相关字段
                        exif_fields = [k for k in metadata.keys() if k.startswith('EXIF:')]
                        if exif_fields:
                            return True
            except Exception as exiftool_error:
                logger.debug(f"使用exiftool检查EXIF数据也失败: {filepath}, 错误: {str(exiftool_error)}")
            return False
