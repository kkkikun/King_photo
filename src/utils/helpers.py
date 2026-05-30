"""
King_photo - 工具函数
"""

import logging
import os
import re
from datetime import datetime
from typing import Optional, List

from .constants import ALL_EXTENSIONS, TIME_PATTERNS

# 获取日志记录器
logger = logging.getLogger(__name__)


def get_file_extension(filepath: str) -> str:
    """获取文件扩展名（小写）"""
    return os.path.splitext(filepath)[1].lower()


def is_supported_image(filepath: str) -> bool:
    """检查文件是否为支持的图片格式"""
    ext = get_file_extension(filepath)
    return ext in ALL_EXTENSIONS


def get_image_files_in_folder(folder_path: str) -> List[str]:
    """获取文件夹中所有支持的图片文件"""
    image_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            filepath = os.path.join(root, file)
            if is_supported_image(filepath):
                image_files.append(filepath)
    return sorted(image_files)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    if dt is None:
        return "未知"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """解析日期时间字符串"""
    if not dt_str:
        return None

    # 清理字符串
    dt_str = dt_str.strip()

    # 常见格式
    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%Y%m%d%H%M%S",
        "%Y%m%d_%H%M%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    return None


def extract_time_from_filename(filename: str) -> Optional[datetime]:
    """从文件名中提取时间信息"""
    # 移除扩展名
    name = os.path.splitext(filename)[0]

    # 1. 先尝试标准日期格式
    for pattern, fmt in TIME_PATTERNS:
        match = re.search(pattern, name)
        if match:
            try:
                if fmt == 'timestamp':
                    timestamp = int(match.group(1))
                    # 判断是秒级还是毫秒级时间戳
                    if timestamp > 9999999999:  # 毫秒级
                        timestamp = timestamp / 1000
                    return datetime.fromtimestamp(timestamp)
                else:
                    groups = match.groups()
                    if len(groups) == 6:
                        dt_str = f"{groups[0]}{groups[1]}{groups[2]}_{groups[3]}{groups[4]}{groups[5]}"
                        dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                        # 验证年份在合理范围内
                        if 2000 <= dt.year <= 2100:
                            return dt
                    elif len(groups) == 3:
                        dt_str = f"{groups[0]}{groups[1]}{groups[2]}"
                        dt = datetime.strptime(dt_str, "%Y%m%d")
                        # 验证年份在合理范围内
                        if 2000 <= dt.year <= 2100:
                            return dt
            except (ValueError, OverflowError, OSError):
                continue

    # 2. 尝试提取13位毫秒级时间戳（常见于微信、QQ等）
    # 匹配模式：任意前缀_数字 或 mmexport数字 或纯数字
    # 使用负向断言(?<!\d)和(?!\d)确保匹配完整的数字，避免部分匹配
    timestamp_patterns = [
        r'(?:mmexport|img_|Image_|Cache_|comment_)?(?<!\d)(\d{13})(?!\d)',  # 13位毫秒时间戳
        r'(?:mmexport|img_|Image_|Cache_|comment_)?(?<!\d)(\d{10})(?!\d)',  # 10位秒时间戳
        r'_(?<!\d)(\d{13})(?!\d)',  # 下划线后跟13位数字
        r'_(?<!\d)(\d{10})(?!\d)',  # 下划线后跟10位数字
        r'^(?<!\d)(\d{13})(?!\d)$',  # 纯13位数字
        r'^(?<!\d)(\d{10})(?!\d)$',  # 纯10位数字
    ]

    for pattern in timestamp_patterns:
        match = re.search(pattern, name)
        if match:
            try:
                timestamp = int(match.group(1))
                # 判断是秒级还是毫秒级时间戳
                if timestamp > 9999999999:  # 毫秒级
                    timestamp = timestamp / 1000
                # 验证时间戳是否合理（1990-2030年）
                # 1990-01-01 00:00:00 UTC = 631152000
                # 2030-01-01 00:00:00 UTC = 1893456000
                if 631152000 <= timestamp <= 1893456000:
                    return datetime.fromtimestamp(timestamp)
            except (ValueError, OverflowError, OSError):
                continue

    # 3. 尝试提取带负号ID的格式（如 img_-1083997888_1647742406658）
    match = re.search(r'img_-?\d+_(\d{13})', name)
    if match:
        try:
            timestamp = int(match.group(1)) / 1000
            # 验证时间戳是否合理（1990-2030年）
            if 631152000 <= timestamp <= 1893456000:
                return datetime.fromtimestamp(timestamp)
        except (ValueError, OverflowError, OSError):
            pass

    return None


def generate_renamed_filename(
    original_name: str,
    rename_format: str,
    metadata: dict,
    sequence: int = 1,
    ext: str = '.jpg'
) -> str:
    """根据格式生成新文件名"""
    # 获取变量值
    dt = metadata.get('datetime')
    if dt is None:
        dt = datetime.now()

    variables = {
        '{date}': dt.strftime('%Y%m%d'),
        '{time}': dt.strftime('%H%M%S'),
        '{datetime}': dt.strftime('%Y%m%d_%H%M%S'),
        '{year}': dt.strftime('%Y'),
        '{month}': dt.strftime('%m'),
        '{day}': dt.strftime('%d'),
        '{hour}': dt.strftime('%H'),
        '{minute}': dt.strftime('%M'),
        '{second}': dt.strftime('%S'),
        '{timestamp}': str(int(dt.timestamp())),
        '{original}': original_name,
        '{ext}': ext,
        '{seq}': f'{sequence:03d}',
        '{camera}': metadata.get('camera', 'Unknown'),
        '{make}': metadata.get('make', 'Unknown'),
        '{lens}': metadata.get('lens', 'Unknown'),
        '{width}': str(metadata.get('width', 0)),
        '{height}': str(metadata.get('height', 0)),
        '{orientation}': metadata.get('orientation', 'Unknown'),
        '{title}': metadata.get('title', ''),
        '{desc}': metadata.get('description', ''),
        '{artist}': metadata.get('artist', ''),
        '{copyright}': metadata.get('copyright', ''),
    }

    # 替换变量
    result = rename_format
    for var, value in variables.items():
        result = result.replace(var, str(value))

    # 处理 {seq:N} 格式
    seq_match = re.search(r'\{seq:(\d+)\}', result)
    if seq_match:
        n = int(seq_match.group(1))
        result = result.replace(seq_match.group(0), f'{sequence:0{n}d}')

    # 清理非法字符
    result = sanitize_filename(result)

    return result + ext


def sanitize_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    # Windows非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')

    # 移除首尾空格和点
    filename = filename.strip(' .')

    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]

    return filename


def set_file_times(filepath: str, dt: datetime, set_created: bool = False, preserve_created: bool = None) -> bool:
    """
    设置文件的时间信息
    
    Args:
        filepath: 文件路径
        dt: 要设置的时间
        set_created: 是否同时设置创建时间（仅Windows）
        preserve_created: 是否保留原始创建时间（与set_created相反，如果设置此参数则忽略set_created）
    
    Returns:
        是否设置成功
    """
    try:
        timestamp = dt.timestamp()
        os.utime(filepath, (timestamp, timestamp))
        
        # 处理preserve_created参数：如果设置则忽略set_created
        if preserve_created is not None:
            set_created = not preserve_created
        
        # 在Windows系统上，尝试设置创建时间
        if set_created and os.name == 'nt':
            try:
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
                    filepath,
                    GENERIC_WRITE,
                    FILE_SHARE_READ | FILE_SHARE_WRITE,
                    None,
                    OPEN_EXISTING,
                    FILE_ATTRIBUTE_NORMAL,
                    None
                )
                
                if file_handle == -1:
                    logger.warning(f"无法打开文件以设置创建时间: {filepath}")
                    return True  # 至少修改时间设置成功了
                
                try:
                    # 转换为Windows FILETIME
                    # FILETIME是从1601年1月1日开始的100纳秒间隔数
                    # 使用dt.timestamp()获取正确的UTC时间戳（已处理时区）
                    unix_timestamp = int(dt.timestamp())
                    # 从1601年到1970年的100纳秒间隔数
                    epoc_diff = 116444736000000000
                    filetime = int((unix_timestamp * 10000000) + epoc_diff)
                    
                    # 设置文件时间
                    ctypes.windll.kernel32.SetFileTime(
                        file_handle,
                        ctypes.byref(ctypes.c_longlong(filetime)),  # 创建时间
                        None,  # 访问时间
                        None   # 修改时间
                    )
                    
                    logger.info(f"成功设置文件创建时间: {filepath}")
                finally:
                    kernel32.CloseHandle(file_handle)
                    
            except ImportError:
                logger.warning("ctypes模块不可用，无法设置创建时间")
            except Exception as e:
                logger.warning(f"设置创建时间失败: {filepath}, 错误: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"设置文件时间失败: {filepath}, 错误: {str(e)}")
        return False


def get_file_times(filepath: str) -> dict:
    """获取文件的时间信息"""
    stat = os.stat(filepath)
    return {
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'accessed': datetime.fromtimestamp(stat.st_atime),
    }


def ensure_output_folder(output_path: str) -> str:
    """确保输出文件夹存在"""
    os.makedirs(output_path, exist_ok=True)
    return output_path


def get_unique_filename(filepath: str) -> str:
    """获取唯一的文件名（如果文件已存在则添加序号）"""
    if not os.path.exists(filepath):
        return filepath

    base, ext = os.path.splitext(filepath)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"


def truncate_string(s: str, max_length: int = 50) -> str:
    """截断字符串"""
    if len(s) <= max_length:
        return s
    return s[:max_length-3] + '...'
