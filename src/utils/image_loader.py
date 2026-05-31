"""
统一图片加载器 — 多格式支持 + 智能降级
"""
import logging
import os
from io import BytesIO
from typing import Optional, Tuple, Callable, Dict

from PIL import Image

logger = logging.getLogger(__name__)

# ============================================================
# 可选依赖检测
# ============================================================
_available = {
    'pillow_heif': False,
    'pillow_avif': False,
    'pillow_jxl':  False,
    'cairosvg':    False,
    'rawpy':       False,
}

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    _available['pillow_heif'] = True
    logger.info("pillow-heif 已加载，支持 HEIC/HEIF 预览")
except ImportError:
    logger.info("pillow-heif 未安装，HEIC/HEIF 预览受限")

try:
    from pillow_avif import AvifImagePlugin
    _available['pillow_avif'] = True
    logger.info("pillow-avif-plugin 已加载，支持 AVIF 预览")
except ImportError:
    logger.info("pillow-avif-plugin 未安装，AVIF 预览受限")

try:
    import pillow_jxl
    _available['pillow_jxl'] = True
    logger.info("pillow-jxl-plugin 已加载，支持 JPEG XL 预览")
except ImportError:
    logger.info("pillow-jxl-plugin 未安装，JPEG XL 预览受限")

try:
    import cairosvg
    _available['cairosvg'] = True
    logger.info("cairosvg 已加载，支持 SVG 预览")
except ImportError:
    logger.info("cairosvg 未安装，SVG 预览受限")

try:
    import rawpy
    _available['rawpy'] = True
    logger.info("rawpy 已加载，支持 RAW 格式预览")
except ImportError:
    logger.info("rawpy 未安装，RAW 格式预览受限")

# ============================================================
# 格式→扩展名
# ============================================================
RAW_EXTENSIONS = {'.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.pef', '.raf', '.srw'}

# ============================================================
# 加载器注册表（插件可扩展）
# ============================================================
_loaders: Dict[str, Callable] = {}

def register_loader(format_name: str, loader: Callable):
    """注册自定义格式加载器（供插件使用）"""
    _loaders[format_name.upper()] = loader
    logger.info(f"已注册自定义加载器: {format_name}")

# ============================================================
# 核心 API
# ============================================================
def get_available_formats() -> Dict[str, bool]:
    """返回各格式的加载能力"""
    return {
        'JPEG': True, 'PNG': True, 'GIF': True, 'BMP': True,
        'TIFF': True, 'ICO': True, 'WebP': True,
        'HEIC': _available['pillow_heif'],
        'AVIF': _available['pillow_avif'],
        'JXL':  _available['pillow_jxl'],
        'SVG':  _available['cairosvg'],
        'RAW':  _available['rawpy'],
        'PSD':  True,
    }

def load_image(filepath: str) -> Tuple[Optional[Image.Image], Optional[str]]:
    """
    统一图片加载（带回退链）
    
    Returns:
        (PIL.Image 对象, 错误信息)
        - 成功: (Image, None)
        - 失败: (None, "错误原因")
    """
    if not os.path.exists(filepath):
        return None, "文件不存在"
    
    ext = os.path.splitext(filepath)[1].lower()
    
    # Step 1: 尝试 PIL + 已注册的 opener
    try:
        img = Image.open(filepath)
        img.load()
        return img, None
    except Exception:
        pass
    
    # Step 2: 特殊格式专用加载
    # HEIC/HEIF（pillow-heif 如果未注册为 opener）
    if ext in ('.heic', '.heif'):
        if _available['pillow_heif']:
            try:
                heif_file = pillow_heif.read_heif(filepath)
                img = Image.frombytes(
                    heif_file.mode, heif_file.size,
                    heif_file.data, 'raw', heif_file.mode
                )
                return img, None
            except Exception:
                pass
        return None, "HEIC/HEIF 格式需安装 pillow-heif 库"
    
    # SVG → 渲染为位图
    if ext == '.svg':
        if _available['cairosvg']:
            try:
                png_data = cairosvg.svg2png(url=filepath)
                img = Image.open(BytesIO(png_data))
                return img, None
            except Exception:
                pass
        return None, "SVG 格式需安装 cairosvg 库"
    
    # RAW 格式
    if ext in RAW_EXTENSIONS:
        if _available['rawpy']:
            try:
                raw = rawpy.imread(filepath)
                rgb = raw.postprocess()
                img = Image.fromarray(rgb)
                return img, None
            except Exception:
                pass
        return None, "RAW 格式需安装 rawpy 库"
    
    # AVIF / JPEG XL（如已注册 opener，Step 1 应已处理）
    if ext == '.avif' and not _available['pillow_avif']:
        return None, "AVIF 格式需安装 pillow-avif-plugin 库"
    if ext == '.jxl' and not _available['pillow_jxl']:
        return None, "JPEG XL 格式需安装 pillow-jxl-plugin 库"
    
    # Step 3: 插件注册的自定义加载器
    ext_to_fmt = os.path.splitext(filepath)[1].upper().lstrip('.')
    for fmt, loader in _loaders.items():
        try:
            img = loader(filepath)
            if img:
                return img, None
        except Exception:
            continue
    
    return None, f"无法加载该格式文件 ({ext})"

def can_preview(filepath: str) -> Tuple[bool, str]:
    """检查文件是否可以预览"""
    img, err = load_image(filepath)
    if img:
        img.close()
        return True, "可预览"
    return False, err or "未知错误"

def load_thumbnail(filepath: str, size: Tuple[int, int] = (150, 150)) -> Tuple[Optional[Image.Image], Optional[str]]:
    """加载缩略图（自动缩放）"""
    img, err = load_image(filepath)
    if img:
        img.thumbnail(size, Image.Resampling.LANCZOS)
    return img, err

def get_load_error_display(filepath: str) -> str:
    """
    根据文件头和扩展名返回友好的错误显示文本
    """
    try:
        with open(filepath, 'rb') as f:
            header = f.read(16)
    except Exception:
        return "无法访问"
    
    if not header:
        return "空文件"
    
    # ftyp box 格式
    if len(header) >= 12 and header[4:8] == b'ftyp':
        brand = header[8:12]
        if brand in (b'heic', b'heix', b'heim', b'heis', b'hevc', b'hevx', b'heif'):
            return "HEIC图片"
        if brand in (b'avif', b'avis'):
            return "AVIF图片"
        if brand == b'mif1':
            if len(header) >= 20 and header[16:20] == b'avif':
                return "AVIF图片"
            return "HEIC图片"
        if brand in (b'qt  ', b'MSNV', b'mp42'):
            return "视频文件"
        if brand.startswith(b'mp4'):
            return "视频文件"
        return "多媒体文件"
    
    if header.startswith(b'\x89PNG'):
        return "PNG图片"
    if header.startswith(b'\xff\xd8\xff'):
        return "JPEG图片"
    if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return "GIF图片"
    if header.startswith(b'BM'):
        return "BMP图片"
    if header.startswith(b'RIFF'):
        if len(header) >= 12 and header[8:12] == b'WEBP':
            return "WebP图片"
        return "AVI视频"
    if header.startswith(b'\x1aE\xdf\xa3'):
        return "MKV视频"
    if header.startswith(b'<?xml') or header.startswith(b'<svg'):
        return "SVG图片"
    
    ext = os.path.splitext(filepath)[1].lower()
    for known_ext in ['.heic', '.heif', '.avif', '.jxl']:
        if ext == known_ext:
            return f"{known_ext.upper()[1:]}图片"
    for known_ext in ['.mov', '.mp4', '.avi', '.wmv', '.mkv']:
        if ext == known_ext:
            return "视频文件"
    
    return "未知格式"
