"""
King_photo - EXIF处理模块
处理JPEG、TIFF等格式的EXIF元信息
"""

import io
import struct
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

import piexif
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from ..utils.constants import EXIF_FIELDS, EXIF_TIME_FIELDS


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
            pass

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
        try:
            exif_dict = piexif.load(filepath)

            # 写入支持的字段
            field_mapping = {
                'artist': (piexif.ImageIFD.Artist, "0th"),
                'copyright': (piexif.ImageIFD.Copyright, "0th"),
                'description': (piexif.ImageIFD.ImageDescription, "0th"),
                'make': (piexif.ImageIFD.Make, "0th"),
                'model': (piexif.ImageIFD.Model, "0th"),
                'software': (piexif.ImageIFD.Software, "0th"),
                'datetime': (piexif.ImageIFD.DateTime, "0th"),
                'datetime_original': (piexif.ExifIFD.DateTimeOriginal, "Exif"),
                'datetime_digitized': (piexif.ExifIFD.DateTimeDigitized, "Exif"),
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

        except Exception:
            return False

    @staticmethod
    def get_datetime(filepath: str) -> Optional[datetime]:
        """快速获取拍摄时间"""
        try:
            exif_dict = piexif.load(filepath)
            exif_ifd = exif_dict.get("Exif", {})

            return ExifHandler._get_datetime(exif_ifd)

        except Exception:
            return None

    @staticmethod
    def has_exif(filepath: str) -> bool:
        """检查文件是否包含EXIF数据"""
        try:
            exif_dict = piexif.load(filepath)
            return bool(exif_dict.get("0th")) or bool(exif_dict.get("Exif"))
        except Exception:
            return False
