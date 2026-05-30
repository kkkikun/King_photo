"""
King_photo - 常量定义
"""

# 支持的图片格式及其扩展名
SUPPORTED_FORMATS = {
    # 格式名称: (扩展名列表, 是否支持EXIF, 是否支持XMP, 是否需要exiftool)
    'JPEG': (['.jpg', '.jpeg'], True, True, False),
    'PNG': (['.png'], False, True, False),
    'GIF': (['.gif'], False, False, False),
    'WebP': (['.webp'], True, True, False),
    'TIFF': (['.tif', '.tiff'], True, True, False),
    'HEIF': (['.heif', '.heic'], True, True, True),
    'RAW_CR2': (['.cr2'], True, True, True),
    'RAW_NEF': (['.nef'], True, True, True),
    'RAW_ARW': (['.arw'], True, True, True),
    'RAW_DNG': (['.dng'], True, True, True),
    'SVG': (['.svg'], False, True, False),
    'AVIF': (['.avif'], True, True, True),
    'JPEG_XL': (['.jxl'], True, True, True),
    'BMP': (['.bmp'], False, False, False),
    'ICO': (['.ico'], False, False, False),
    'PSD': (['.psd'], True, True, True),
    'MOV': (['.mov', '.mp4', '.m4v'], False, False, False),
}

# 所有支持的扩展名列表
ALL_EXTENSIONS = []
for format_info in SUPPORTED_FORMATS.values():
    ALL_EXTENSIONS.extend(format_info[0])

# 文件头魔数 (Magic Numbers)
FILE_SIGNATURES = {
    'JPEG': [b'\xff\xd8\xff'],
    'PNG': [b'\x89PNG\r\n\x1a\n'],
    'GIF': [b'GIF87a', b'GIF89a'],
    'WebP': [b'RIFF'],  # 需要进一步检查WEBP标记
    'TIFF': [b'II\x2a\x00', b'MM\x00\x2a'],
    'BMP': [b'BM'],
    'PSD': [b'8BPS'],
    'ICO': [b'\x00\x00\x01\x00'],
    'SVG': [b'<?xml', b'<svg'],
    'HEIF': [b'\x00\x00\x00\x18ftypheic', b'\x00\x00\x00\x18ftypheif',
             b'\x00\x00\x00\x1cmif1heic', b'\x00\x00\x00\x20ftypmif1'],
    'AVIF': [b'\x00\x00\x00\x20ftypavif', b'\x00\x00\x00\x1cftypavis'],
    'CR2': [b'II\x2a\x00\x10\x00\x00\x00CR'],
    'NEF': [b'MM\x00\x2a'],
    'ARW': [b'II\x2a\x00'],
    'DNG': [b'II\x2a\x00', b'MM\x00\x2a'],
    # 视频格式（非图片，用于检测误标记的文件）
    'MOV': [b'\x00\x00\x00\x14ftypqt  ', b'\x00\x00\x00\x18ftypmp4 ', b'\x00\x00\x00\x1cftypmp41'],
    'MP4': [b'\x00\x00\x00\x18ftypmp4 ', b'\x00\x00\x00\x1cftypmp41', b'\x00\x00\x00\x20ftypisom'],
    'AVI': [b'RIFF'],
    'WMV': [b'\x30\x26\xab\x75\x9e\x7b\xcf\x11'],
}

# EXIF时间字段优先级
EXIF_TIME_FIELDS = [
    36867,  # DateTimeOriginal
    36868,  # DateTimeDigitized
    306,    # DateTime
]

# XMP时间字段（优先级从高到低）
XMP_TIME_FIELDS = [
    'photoshop:DateCreated',       # 拍摄时间/创建时间（PNG等纯XMP格式的标准字段）
    'exif:DateTimeOriginal',       # 原始拍摄时间（EXIF格式在XMP中的映射）
    'exif:DateTimeDigitized',      # 数字化时间
    'xmp:CreateDate',              # XMP创建时间
    'xmp:ModifyDate',              # XMP修改时间
]

# EXIF字段定义 (标签ID, 名称, 是否可编辑)
EXIF_FIELDS = {
    # 基本信息
    'Make': (271, '相机品牌', True),
    'Model': (272, '相机型号', True),
    'Software': (305, '软件', True),
    'DateTime': (306, '修改时间', True),
    'Artist': (315, '作者', True),
    'Copyright': (33432, '版权', True),

    # 拍摄参数
    'ExposureTime': (33434, '曝光时间', False),
    'FNumber': (33437, '光圈', False),
    'ISOSpeedRatings': (34855, 'ISO', False),
    'FocalLength': (37386, '焦距', False),
    'LensModel': (42036, '镜头型号', True),

    # 图片信息
    'ImageWidth': (256, '图片宽度', False),
    'ImageLength': (257, '图片高度', False),
    'Orientation': (274, '方向', False),

    # 时间信息
    'DateTimeOriginal': (36867, '拍摄时间', True),
    'DateTimeDigitized': (36868, '数字化时间', True),

    # 描述信息
    'ImageDescription': (270, '图片描述', True),
    'XPTitle': (40091, '标题', True),
    'XPComment': (40092, '评论', True),
    'XPAuthor': (40093, '作者', True),
    'XPKeywords': (40094, '关键词', True),
}

# XMP字段定义（参考: https://www.exiftool.org/TagNames/XMP.html）
XMP_FIELDS = {
    # 时间相关
    'xmp:CreateDate': '创建时间',          # 文件创建时间
    'xmp:ModifyDate': '修改时间',          # 文件修改时间
    'exif:DateTimeOriginal': '拍摄时间',    # 原始拍摄时间
    'exif:DateTimeDigitized': '数字化时间', # 数字化时间
    'photoshop:DateCreated': '创建日期',    # Photoshop创建日期
    # 描述相关（dc命名空间）
    'dc:title': '标题',
    'dc:description': '描述',
    'dc:creator': '创建者',
    'dc:subject': '关键词',
    'dc:rights': '版权',
    # 相机信息（tiff命名空间 - PNG/WebP等纯XMP格式使用）
    'tiff:Make': '相机品牌',
    'tiff:Model': '相机型号',
    'tiff:Software': '软件',
    'tiff:Orientation': '方向',
    # 拍摄参数（exif命名空间 - 在XMP中映射EXIF字段）
    'exif:LensModel': '镜头型号',
    'exif:FNumber': '光圈',
    'exif:ExposureTime': '曝光时间',
    'exif:ISOSpeedRatings': 'ISO',
    'exif:FocalLength': '焦距',
    # 其他
    'xmp:CreatorTool': '创建工具',
    'xmp:Rating': '评分',
    'photoshop:City': '城市',
    'photoshop:Country': '国家',
}

# 重命名变量映射
RENAME_VARIABLES = {
    # 时间类
    '{date}': '拍摄日期 (20240101)',
    '{time}': '拍摄时间 (120000)',
    '{datetime}': '完整日期时间 (20240101_120000)',
    '{year}': '年份 (2024)',
    '{month}': '月份 (01)',
    '{day}': '日期 (01)',
    '{hour}': '小时 (12)',
    '{minute}': '分钟 (00)',
    '{second}': '秒 (00)',
    '{timestamp}': 'Unix时间戳',

    # 文件类
    '{original}': '原文件名',
    '{ext}': '文件扩展名',
    '{seq}': '序号 (001)',
    '{seq:N}': '指定位数序号 (N=位数)',

    # 相机类
    '{camera}': '相机型号',
    '{make}': '相机品牌',
    '{lens}': '镜头型号',
    '{width}': '图片宽度',
    '{height}': '图片高度',
    '{orientation}': '方向',

    # 描述类
    '{title}': '图片标题',
    '{desc}': '图片描述',
    '{artist}': '作者',
    '{copyright}': '版权信息',
}

# 默认重命名格式（不包含原文件名）
DEFAULT_RENAME_FORMAT = '{datetime}'

# 时间格式正则表达式
TIME_PATTERNS = [
    # 20240101_120000
    (r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', '%Y%m%d_%H%M%S'),
    # 20240101120000
    (r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', '%Y%m%d%H%M%S'),
    # 2024-01-01 12:00:00
    (r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})', '%Y-%m-%d %H:%M:%S'),
    # 2024-01-01_12-00-00
    (r'(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})', '%Y-%m-%d_%H-%M-%S'),
    # 2024.01.01_12.00.00
    (r'(\d{4})\.(\d{2})\.(\d{2})_(\d{2})\.(\d{2})\.(\d{2})', '%Y.%m.%d_%H.%M.%S'),
    # 20240101 (仅日期)
    (r'^(\d{4})(\d{2})(\d{2})$', '%Y%m%d'),
    # Unix时间戳 (10位或13位数字)
    (r'^(\d{10})$', 'timestamp'),
    (r'^(\d{13})$', 'timestamp'),
]

# ===== 元数据字段映射 =====
# 内部字段名 → ExifTool标签名（metadata_writer + exif_handler 共用）
INTERNAL_TO_EXIFTOOL = {
    'artist': 'Artist',
    'copyright': 'Copyright',
    'description': 'ImageDescription',
    'make': 'Make',
    'model': 'Model',
    'software': 'Software',
    'title': 'Title',
    'keywords': 'Keywords',
    'lens': 'LensModel',
    'orientation': 'Orientation',
    'exposure_time': 'ExposureTime',
    'fnumber': 'FNumber',
    'iso': 'ISO',
    'focal_length': 'FocalLength',
    'datetime': 'DateTimeOriginal',
    'datetime_original': 'DateTimeOriginal',
    'datetime_digitized': 'DateTimeDigitized',
    'creation_time': 'CreateDate',
}

# 内部字段名 → IPTC标签名
INTERNAL_TO_IPTC = {
    'title': 'Title',
    'description': 'Description',
    'author': 'Author',
    'copyright': 'Copyright',
    'keywords': 'Keywords',
}

# 可通过 piexif 写入的字段名集合（恒等映射，仅需验证）
PIEIXF_VALID_FIELDS = {
    'artist', 'copyright', 'description', 'make', 'model',
    'software', 'lens', 'orientation', 'exposure_time',
    'fnumber', 'iso', 'focal_length',
}
