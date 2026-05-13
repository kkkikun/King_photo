"""
King_photo - 工具函数
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

from .constants import ALL_EXTENSIONS, TIME_PATTERNS


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
                        return datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                    elif len(groups) == 3:
                        dt_str = f"{groups[0]}{groups[1]}{groups[2]}"
                        return datetime.strptime(dt_str, "%Y%m%d")
            except (ValueError, OverflowError, OSError):
                continue

    # 2. 尝试提取13位毫秒级时间戳（常见于微信、QQ等）
    # 匹配模式：任意前缀_数字 或 mmexport数字 或纯数字
    timestamp_patterns = [
        r'(?:mmexport|img_|Image_|Cache_|comment_)?(\d{13})',  # 13位毫秒时间戳
        r'(?:mmexport|img_|Image_|Cache_|comment_)?(\d{10})',  # 10位秒时间戳
        r'_(\d{13})',  # 下划线后跟13位数字
        r'_(\d{10})',  # 下划线后跟10位数字
        r'^(\d{13})$',  # 纯13位数字
        r'^(\d{10})$',  # 纯10位数字
    ]

    for pattern in timestamp_patterns:
        match = re.search(pattern, name)
        if match:
            try:
                timestamp = int(match.group(1))
                # 判断是秒级还是毫秒级时间戳
                if timestamp > 9999999999:  # 毫秒级
                    timestamp = timestamp / 1000
                # 验证时间戳是否合理（2000-2100年）
                if 946684800 <= timestamp <= 4102444800:
                    return datetime.fromtimestamp(timestamp)
            except (ValueError, OverflowError, OSError):
                continue

    # 3. 尝试提取带负号ID的格式（如 img_-1083997888_1647742406658）
    match = re.search(r'img_-?\d+_(\d{13})', name)
    if match:
        try:
            timestamp = int(match.group(1)) / 1000
            if 946684800 <= timestamp <= 4102444800:
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


def set_file_times(filepath: str, dt: datetime) -> bool:
    """设置文件的修改时间和访问时间"""
    try:
        timestamp = dt.timestamp()
        os.utime(filepath, (timestamp, timestamp))
        return True
    except Exception:
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
