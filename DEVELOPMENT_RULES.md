# King_photo 项目开发规则

## 目录

1. [项目架构规则](#项目架构规则)
2. [代码风格规则](#代码风格规则)
3. [错误处理规则](#错误处理规则)
4. [文件操作规则](#文件操作规则)
5. [UI开发规则](#ui开发规则)
6. [元数据处理规则](#元数据处理规则)
7. [测试规则](#测试规则)
8. [依赖管理规则](#依赖管理规则)
9. [性能优化规则](#性能优化规则)
10. [安全规则](#安全规则)
11. [项目结构查询规则](#项目结构查询规则)

---

## 项目架构规则

### 1.1 模块职责分离

项目采用三层架构，严格遵守职责分离原则：

```
src/
├── core/      # 核心业务逻辑（无UI依赖）
├── ui/        # 用户界面（不包含业务逻辑）
└── utils/     # 通用工具函数（无业务逻辑）
```

**规则：**
- `core/` 模块不得导入 `ui/` 模块的任何内容
- `ui/` 模块可以导入 `core/` 和 `utils/` 模块
- `utils/` 模块不得导入 `core/` 或 `ui/` 模块
- `core/` 模块之间的依赖应通过接口而非具体实现

### 1.2 单一职责原则

每个模块和类应有明确的单一职责：

| 模块 | 职责 |
|------|------|
| `format_detector.py` | 文件格式检测，不处理文件内容 |
| `metadata_reader.py` | 元数据读取，不修改文件 |
| `metadata_writer.py` | 元数据写入，不读取元数据 |
| `repair_engine.py` | 修复流程编排，调用其他模块 |
| `exif_handler.py` | EXIF格式处理 |
| `xmp_handler.py` | XMP格式处理 |
| `exiftool_wrapper.py` | ExifTool命令行封装 |

### 1.3 依赖注入模式

使用依赖注入降低模块间耦合：

```python
# 好的做法：通过参数传入依赖
def repair_file(filepath, format_detector, metadata_reader, metadata_writer):
    format_info = format_detector.get_format_info(filepath)
    metadata = metadata_reader.read_metadata(filepath)
    # ...

# 不好的做法：直接实例化依赖
def repair_file(filepath):
    detector = FormatDetector()
    reader = MetadataReader()
    # ...
```

---

## 代码风格规则

### 2.1 命名约定

| 类型 | 规则 | 示例 |
|------|------|------|
| 类名 | PascalCase | `RepairEngine`, `FormatDetector` |
| 函数名 | snake_case | `read_metadata`, `fix_extension` |
| 变量名 | snake_case | `file_path`, `output_dir` |
| 常量名 | UPPER_SNAKE_CASE | `FILE_SIGNATURES`, `SUPPORTED_FORMATS` |
| 私有方法 | 前缀下划线 | `_write_exif`, `_get_short_path` |
| 模块名 | 小写下划线 | `metadata_reader.py`, `exif_handler.py` |

### 2.2 类型提示

所有公共函数必须添加类型提示：

```python
from typing import Optional, Dict, Any, List, Tuple

def read_metadata(filepath: str) -> Dict[str, Any]:
    """读取图片元信息"""
    pass

def get_real_format(filepath: str) -> Tuple[Optional[str], bool]:
    """获取真实格式"""
    pass
```

### 2.3 文档字符串

所有公共类和函数必须添加文档字符串：

```python
class RepairEngine:
    """修复引擎
    
    处理文件后缀错误、时间信息提取和修复
    """
    
    @staticmethod
    def repair(
        filepath: str,
        rename_format: str = '{datetime}',
        output_dir: str = None,
        fix_extension: bool = True,
        fix_time: bool = True,
        time_source: str = 'auto'
    ) -> Dict[str, Any]:
        """
        修复文件

        Args:
            filepath: 源文件路径
            rename_format: 重命名格式
            output_dir: 输出目录
            fix_extension: 是否修复后缀
            fix_time: 是否修复时间
            time_source: 时间来源 ('auto', 'metadata', 'modified', 'created')

        Returns:
            操作结果字典，包含以下字段：
            - success: bool 是否成功
            - details: dict 详细结果
            - output_path: str 输出文件路径
            - message: str 操作消息
        """
        pass
```

### 2.4 导入顺序

遵循PEP 8导入顺序：

```python
# 1. 标准库导入
import os
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# 2. 第三方库导入
from PIL import Image
import piexif

# 3. 本地模块导入
from .format_detector import FormatDetector
from ..utils.helpers import get_file_times
```

---

## 错误处理规则

### 3.1 异常处理原则

**规则：**
- 不允许使用裸`except`（`except Exception`是可接受的）
- 不允许使用`except: pass`
- 必须记录异常信息到日志
- 根据上下文决定是恢复、传播还是忽略异常

```python
# 正确的做法
try:
    result = some_operation()
except FileNotFoundError as e:
    logger.error(f"文件不存在: {filepath}, 错误: {str(e)}")
    return {'success': False, 'message': '文件不存在'}
except PermissionError as e:
    logger.error(f"权限不足: {filepath}, 错误: {str(e)}")
    return {'success': False, 'message': '权限不足'}
except Exception as e:
    logger.error(f"未知错误: {filepath}, 错误: {str(e)}")
    return {'success': False, 'message': f'操作失败: {str(e)}'}

# 错误的做法
try:
    result = some_operation()
except:
    pass  # 禁止！
```

### 3.2 日志记录规则

**日志级别使用规范：**

| 级别 | 使用场景 |
|------|----------|
| `DEBUG` | 调试信息，如变量值、中间状态 |
| `INFO` | 正常操作信息，如文件处理成功 |
| `WARNING` | 警告信息，如格式不匹配但可处理 |
| `ERROR` | 错误信息，操作失败但程序可继续 |
| `CRITICAL` | 严重错误，程序可能无法继续 |

**日志记录格式：**

```python
logger = logging.getLogger(__name__)

# 包含上下文信息
logger.info(f"成功处理文件: {filepath}")
logger.warning(f"文件格式不匹配: {filepath}, 文件头: {header_format}, 扩展名: {ext_format}")
logger.error(f"处理失败: {filepath}, 错误: {str(e)}")
```

### 3.3 错误返回格式

统一使用字典格式返回错误：

```python
{
    'success': bool,           # 是否成功
    'message': str,            # 用户友好的消息
    'error_type': str,         # 错误类型（用于程序判断）
    'error_detail': str,       # 详细错误信息（用于调试）
    'skipped': bool,           # 是否跳过（非错误）
}
```

**错误类型常量：**

```python
ERROR_TYPES = {
    'file_not_found': '文件不存在',
    'permission_denied': '权限不足',
    'format_mismatch': '格式不匹配',
    'metadata_read_failed': '元数据读取失败',
    'metadata_write_failed': '元数据写入失败',
    'exiftool_not_available': 'ExifTool不可用',
    'invalid_format': '无效格式',
}
```

---

## 文件操作规则

### 4.1 复制模式优先

**规则：** 默认使用复制模式处理文件，不修改原文件。

```python
def write_metadata(filepath, metadata, copy_mode=True, output_dir=None):
    """
    写入元信息
    
    Args:
        copy_mode: 是否复制模式（True=复制后修改，False=直接修改原文件）
    """
    if copy_mode:
        output_path = os.path.join(output_dir, os.path.basename(filepath))
        output_path = get_unique_filename(output_path)
        shutil.copy2(filepath, output_path)
    else:
        output_path = filepath
```

### 4.2 文件路径处理

**规则：**
- 始终使用`os.path`或`pathlib`处理路径，避免字符串拼接
- 处理中文路径时使用短路径（Windows 8.3格式）
- 始终验证路径存在性和可访问性

```python
# 正确的做法
import os
from pathlib import Path

def process_file(filepath):
    # 验证文件存在
    if not os.path.exists(filepath):
        return {'success': False, 'message': '文件不存在'}
    
    # 获取绝对路径
    abs_path = os.path.abspath(filepath)
    
    # 处理中文路径（Windows）
    if os.name == 'nt':
        short_path = _get_short_path(abs_path)
    
    # 使用pathlib
    path = Path(filepath)
    filename = path.stem
    extension = path.suffix
```

### 4.3 唯一文件名生成

**规则：** 生成输出文件名时，自动处理重名冲突。

```python
def get_unique_filename(filepath: str) -> str:
    """获取唯一的文件名（如果文件已存在则添加序号）"""
    if not os.path.exists(filepath):
        return filepath
    
    base, ext = os.path.splitext(filepath)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"
```

### 4.4 文件时间属性处理

**规则：**
- 修改文件后，必须恢复或设置正确的时间属性
- Windows系统需要特殊处理创建时间
- 时间戳使用正确的时区处理

```python
def set_file_times(filepath: str, dt: datetime, set_created: bool = False) -> bool:
    """
    设置文件的时间信息
    
    Args:
        filepath: 文件路径
        dt: 要设置的时间
        set_created: 是否同时设置创建时间（仅Windows）
    """
    try:
        # 使用dt.timestamp()获取正确的UTC时间戳（已处理时区）
        timestamp = dt.timestamp()
        os.utime(filepath, (timestamp, timestamp))
        
        # Windows系统设置创建时间
        if set_created and os.name == 'nt':
            # 使用Windows API设置创建时间
            _set_windows_creation_time(filepath, dt)
        
        return True
    except Exception as e:
        logger.error(f"设置文件时间失败: {filepath}, 错误: {str(e)}")
        return False
```

---

## UI开发规则

### 5.1 线程安全规则

**规则：** 所有UI更新必须在主线程执行。

```python
# 正确的做法：使用self.after()调度UI更新
def _load_thumbnail_async(self):
    def load_task():
        try:
            image = Image.open(self.filepath)
            # ... 处理图片
            
            # 使用self.after()在主线程更新UI
            self.after(0, lambda: self._update_image(image))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
    
    # 在后台线程执行
    thread = threading.Thread(target=load_task)
    thread.daemon = True
    thread.start()

# 错误的做法：直接在后台线程更新UI
def _load_thumbnail_async(self):
    def load_task():
        image = Image.open(self.filepath)
        self.image_label.configure(image=image)  # 禁止！非线程安全
```

### 5.2 批量操作模式

**规则：** 批量操作必须支持进度显示和取消功能。

```python
class ProgressDialog:
    """进度对话框"""
    
    def __init__(self, parent, title, total):
        self.cancel_event = threading.Event()
        self.total = total
        
    def update_progress(self, current, filename):
        """更新进度（线程安全）"""
        self.parent.after(0, lambda: self._update_ui(current, filename))
        
    def is_cancelled(self):
        """检查是否已取消"""
        return self.cancel_event.is_set()
        
    def cancel(self):
        """取消操作"""
        self.cancel_event.set()

def batch_operation(file_list, progress_dialog):
    """批量操作模板"""
    for i, filepath in enumerate(file_list):
        # 检查取消
        if progress_dialog.is_cancelled():
            break
        
        # 更新进度
        progress_dialog.update_progress(i + 1, filepath)
        
        # 执行操作
        result = process_file(filepath)
```

### 5.3 可滚动对话框

**规则：** 所有对话框必须支持滚动，避免内容被截断。

```python
class ScrollableDialog(tk.Toplevel):
    """可滚动对话框基类"""
    
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        
        # 创建Canvas和Scrollbar
        self.main_canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        
        # 配置滚动
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 绑定鼠标滚轮
        self.main_canvas.bind("<MouseWheel>", lambda e: self.main_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))
        
        # 布局
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 设置窗口大小
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = int(screen_width * 0.5)
        height = int(screen_height * 0.6)
        self.geometry(f"{width}x{height}")
        self.minsize(600, 500)
```

### 5.4 配置管理

**规则：** 使用配置管理器持久化用户设置。

```python
from ..utils.config_manager import get_config_manager

class MainWindow:
    def __init__(self):
        self.config = get_config_manager()
        
        # 加载配置
        width = self.config.get('window.width', 1200)
        height = self.config.get('window.height', 800)
        
        # 保存配置
        self.config.set('window.width', self.root.winfo_width())
        self.config.set('window.height', self.root.winfo_height())
```

---

## 元数据处理规则

### 6.1 格式检测优先

**规则：** 处理文件前，必须先检测真实格式。

```python
def process_image(filepath):
    """处理图片前的格式检测"""
    
    # 1. 检测真实格式
    format_info = FormatDetector.get_format_info(filepath)
    
    # 2. 验证是否为真正的图片
    is_image, msg = FormatDetector.is_truly_image(filepath)
    if not is_image:
        return {'success': False, 'message': f'不是图片: {msg}'}
    
    # 3. 检查格式一致性
    if not format_info['is_consistent']:
        logger.warning(f"格式不匹配: {filepath}")
    
    # 4. 根据格式选择处理方式
    if format_info['needs_exiftool']:
        return _process_with_exiftool(filepath)
    elif format_info['supports_exif']:
        return _process_with_piexif(filepath)
    elif format_info['supports_xmp']:
        return _process_with_xmp(filepath)
    else:
        return {'success': False, 'message': '不支持的格式'}
```

### 6.2 回退机制

**规则：** 实现多层回退机制，确保最大兼容性。

```python
def write_exif(filepath, metadata):
    """写入EXIF，带回退机制"""
    
    # 第一层：尝试piexif（快速，支持JPEG/TIFF）
    try:
        success = _write_with_piexif(filepath, metadata)
        if success:
            return True
    except Exception as e:
        logger.warning(f"piexif写入失败: {filepath}")
    
    # 第二层：尝试exiftool（通用，支持所有格式）
    try:
        et = get_exiftool()
        if et.is_available:
            success = _write_with_exiftool(filepath, metadata)
            if success:
                return True
    except Exception as e:
        logger.warning(f"exiftool写入失败: {filepath}")
    
    # 第三层：尝试复制文件时间到EXIF
    try:
        success = _copy_filetime_to_exif(filepath)
        if success:
            return True
    except Exception as e:
        logger.warning(f"复制时间失败: {filepath}")
    
    return False
```

### 6.3 EXIF/XMP字段映射

**规则：** 统一使用内部字段名，自动映射到不同格式的标准字段名。

```python
# 内部字段名到EXIF标签的映射
EXIF_FIELD_MAPPING = {
    'datetime': 'DateTimeOriginal',
    'datetime_original': 'DateTimeOriginal',
    'datetime_digitized': 'DateTimeDigitized',
    'make': 'Make',
    'model': 'Model',
    'artist': 'Artist',
    'copyright': 'Copyright',
    'description': 'ImageDescription',
}

# 内部字段名到XMP字段的映射
XMP_FIELD_MAPPING = {
    'datetime': 'exif:DateTimeOriginal',
    'datetime_original': 'exif:DateTimeOriginal',
    'datetime_digitized': 'exif:DateTimeDigitized',
    'make': 'tiff:Make',
    'model': 'tiff:Model',
    'artist': 'dc:creator',
    'copyright': 'dc:rights',
    'description': 'dc:description',
}

# 内部字段名到ExifTool标签的映射
EXIFTOOL_FIELD_MAPPING = {
    'datetime': 'DateTimeOriginal',
    'datetime_original': 'DateTimeOriginal',
    'datetime_digitized': 'CreateDate',
    'make': 'Make',
    'model': 'Model',
    'artist': 'Artist',
    'copyright': 'Copyright',
    'description': 'ImageDescription',
}
```

### 6.4 时间处理规则

**规则：** 统一时间格式处理，避免时区问题。

```python
# 时间格式常量
EXIF_TIME_FORMAT = "%Y:%m:%d %H:%M:%S"  # EXIF标准格式
ISO_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"    # ISO 8601格式
DISPLAY_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # 显示格式

def convert_exif_to_iso(exif_time: str) -> str:
    """将EXIF时间格式转换为ISO 8601格式"""
    try:
        dt = datetime.strptime(exif_time, EXIF_TIME_FORMAT)
        return dt.strftime(ISO_TIME_FORMAT)
    except ValueError:
        return exif_time

def get_best_time(filepath: str, time_source: str = 'auto') -> Optional[datetime]:
    """获取最佳时间信息"""
    if time_source == 'metadata':
        return MetadataReader.get_datetime(filepath)
    elif time_source == 'modified':
        return get_file_times(filepath)['modified']
    elif time_source == 'created':
        return get_file_times(filepath)['created']
    else:  # auto
        # 优先级：元数据 > 文件名 > 文件修改时间
        dt = MetadataReader.get_datetime(filepath)
        if dt:
            return dt
        
        dt = extract_time_from_filename(filepath)
        if dt:
            return dt
        
        return get_file_times(filepath)['modified']
```

---

## 测试规则

### 7.1 测试组织

**规则：** 测试文件与源文件结构对应。

```
tests/
├── __init__.py
├── test_format_detector.py
├── test_metadata_reader.py
├── test_metadata_writer.py
├── test_repair_engine.py
├── test_helpers.py
└── test_data/           # 测试数据
    ├── sample.jpg
    ├── sample.png
    └── corrupted.jpg
```

### 7.2 测试命名规范

**规则：** 测试函数名应清晰描述测试内容。

```python
class TestFormatDetector:
    """格式检测器测试"""
    
    def test_detect_jpeg_by_header(self):
        """测试通过文件头检测JPEG格式"""
        pass
    
    def test_detect_png_by_extension(self):
        """测试通过扩展名检测PNG格式"""
        pass
    
    def test_format_mismatch_detection(self):
        """测试格式不匹配检测"""
        pass
    
    def test_video_file_detection(self):
        """测试视频文件检测"""
        pass
```

### 7.3 测试覆盖率要求

**规则：**
- 核心模块（`core/`）测试覆盖率应达到80%以上
- 关键函数（格式检测、元数据读写）测试覆盖率应达到90%以上
- 边界情况和异常处理必须有测试

### 7.4 测试数据管理

**规则：** 使用真实图片文件进行测试，确保测试的准确性。

```python
import pytest
import os

@pytest.fixture
def sample_jpeg():
    """JPEG测试样本"""
    return os.path.join('tests', 'test_data', 'sample.jpg')

@pytest.fixture
def sample_png():
    """PNG测试样本"""
    return os.path.join('tests', 'test_data', 'sample.png')

@pytest.fixture
def corrupted_jpeg():
    """损坏的JPEG测试样本"""
    return os.path.join('tests', 'test_data', 'corrupted.jpg')

def test_read_jpeg_metadata(sample_jpeg):
    """测试读取JPEG元数据"""
    metadata = MetadataReader.read_metadata(sample_jpeg)
    assert 'datetime' in metadata
    assert metadata['format'] == 'JPEG'
```

---

## 依赖管理规则

### 8.1 依赖版本固定

**规则：** 使用固定版本号，避免兼容性问题。

```txt
# requirements.txt
Pillow>=9.0.0
piexif>=1.1.3
lxml>=4.9.0
ttkbootstrap>=1.10.0
```

### 8.2 外部工具集成

**规则：** 外部工具必须有可用性检查和优雅降级。

```python
class ExifToolWrapper:
    """ExifTool命令行工具封装"""
    
    def __init__(self):
        self.exiftool_path = self._find_exiftool()
        self._available = self.exiftool_path is not None
    
    @property
    def is_available(self) -> bool:
        """检查exiftool是否可用"""
        return self._available
    
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
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None

def process_with_exiftool(filepath, metadata):
    """使用exiftool处理，带可用性检查"""
    et = get_exiftool()
    
    if not et.is_available:
        logger.warning("ExifTool不可用，跳过处理")
        return {'success': False, 'message': 'ExifTool不可用'}
    
    return et.write_metadata(filepath, metadata)
```

### 8.3 可选依赖处理

**规则：** 可选依赖必须有导入检查和功能降级。

```python
# 可选依赖处理示例
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False
    logger.info("pillow-heif未安装，HEIF格式支持有限")

def open_image(filepath):
    """打开图片，处理可选格式支持"""
    try:
        return Image.open(filepath)
    except Exception as e:
        if not HEIF_SUPPORT and filepath.lower().endswith(('.heic', '.heif')):
            logger.warning("需要安装pillow-heif以支持HEIF格式")
        raise
```

---

## 性能优化规则

### 9.1 异步加载

**规则：** 耗时操作必须异步执行，避免阻塞UI。

```python
class ThumbnailWidget:
    """缩略图组件"""
    
    # 异步加载阈值
    ASYNC_THRESHOLD = 20
    
    def load_thumbnails(self, file_list):
        """根据文件数量选择同步或异步加载"""
        if len(file_list) > self.ASYNC_THRESHOLD:
            self._load_thumbnails_async(file_list)
        else:
            self._load_thumbnails_sync(file_list)
    
    def _load_thumbnails_async(self, file_list):
        """异步加载缩略图"""
        def load_task():
            for i, filepath in enumerate(file_list):
                try:
                    self._load_single_thumbnail(filepath)
                except Exception as e:
                    logger.warning(f"加载缩略图失败: {filepath}")
        
        thread = threading.Thread(target=load_task)
        thread.daemon = True
        thread.start()
```

### 9.2 缓存机制

**规则：** 对频繁访问的数据实现缓存。

```python
from functools import lru_cache

class FormatDetector:
    """格式检测器"""
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def detect_by_header(filepath: str) -> Optional[str]:
        """通过文件头检测格式（带缓存）"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(32)
            # ... 检测逻辑
        except Exception:
            return None
```

### 9.3 批量处理优化

**规则：** 批量操作应提供进度反馈和优化处理。

```python
def batch_process(file_list, process_func, progress_callback=None):
    """批量处理模板"""
    results = []
    total = len(file_list)
    
    for i, filepath in enumerate(file_list):
        # 更新进度
        if progress_callback:
            progress_callback(i + 1, total, filepath)
        
        # 处理文件
        try:
            result = process_func(filepath)
            results.append({'file': filepath, 'result': result})
        except Exception as e:
            results.append({'file': filepath, 'error': str(e)})
    
    return results
```

---

## 安全规则

### 10.1 输入验证

**规则：** 所有用户输入必须验证。

```python
def validate_rename_format(format_string: str) -> Tuple[bool, str]:
    """验证重命名格式"""
    # 检查非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        if char in format_string:
            return False, f"格式包含非法字符: {char}"
    
    # 检查长度
    if len(format_string) > 200:
        return False, "格式过长"
    
    # 检查变量有效性
    valid_variables = ['{datetime}', '{date}', '{time}', '{original}', ...]
    # ... 验证逻辑
    
    return True, "格式有效"
```

### 10.2 路径安全

**规则：** 防止路径遍历攻击。

```python
def safe_path_join(base_path, relative_path):
    """安全的路径拼接"""
    # 获取绝对路径
    abs_base = os.path.abspath(base_path)
    abs_path = os.path.abspath(os.path.join(base_path, relative_path))
    
    # 验证路径在基础目录内
    if not abs_path.startswith(abs_base):
        raise ValueError("路径遍历攻击尝试")
    
    return abs_path
```

### 10.3 文件操作安全

**规则：** 文件操作前必须验证权限和状态。

```python
def safe_file_operation(filepath, operation):
    """安全的文件操作"""
    # 检查文件存在
    if not os.path.exists(filepath):
        return {'success': False, 'message': '文件不存在'}
    
    # 检查文件权限
    if not os.access(filepath, os.R_OK):
        return {'success': False, 'message': '文件不可读'}
    
    # 检查文件是否被占用（Windows）
    if os.name == 'nt':
        try:
            with open(filepath, 'r+b'):
                pass
        except IOError:
            return {'success': False, 'message': '文件被占用'}
    
    # 执行操作
    return operation(filepath)
```

---

## 项目结构查询规则

### 11.1 项目结构说明书优先查询

**规则：** 在开始任何开发任务前，必须首先查询项目结构说明书。

**说明书位置：** `PROJECT_STRUCTURE.md`

**查询流程：**
1. 首先读取 `PROJECT_STRUCTURE.md` 了解项目整体结构
2. 根据任务类型定位到相关模块
3. 只在需要详细实现时才读取具体源文件

**优势：**
- 减少重复的代码探索时间
- 快速定位相关模块和函数
- 理解模块间依赖关系
- 避免重复造轮子

### 11.2 结构说明书内容

项目结构说明书包含以下信息：

| 章节 | 内容 |
|------|------|
| 项目概述 | 项目类型、技术栈、核心功能 |
| 目录结构 | 完整的目录树和文件说明 |
| 核心模块详解 | 每个模块的职责、关键类和方法 |
| 入口文件 | 程序启动流程 |
| 配置和资源 | 配置文件、资源目录说明 |
| 模块依赖关系 | 可视化的依赖关系图 |
| 关键类和函数速查 | 常用代码片段和示例 |
| 代码统计 | 各模块代码行数统计 |

### 11.3 快速定位指南

根据开发任务类型，快速定位到相关模块：

| 任务类型 | 相关模块 | 说明书章节 |
|----------|----------|------------|
| 添加新格式支持 | `format_detector.py`, `constants.py` | core/ 目录 |
| 修改元数据处理 | `metadata_reader.py`, `metadata_writer.py` | core/ 目录 |
| 修复文件功能 | `repair_engine.py` | core/ 目录 |
| UI界面修改 | `app.py`, `widgets.py`, `batch_dialog.py` | ui/ 目录 |
| ExifTool集成 | `exiftool_wrapper.py` | utils/ 目录 |
| 配置管理 | `config_manager.py` | utils/ 目录 |
| 日志系统 | `logging_config.py` | utils/ 目录 |
| 添加新功能 | 参考"添加新功能"章节 | 附录 |

### 11.4 更新说明书规则

**规则：** 当项目结构发生重大变化时，必须更新项目结构说明书。

**需要更新的情况：**
- 新增或删除模块
- 模块职责发生重大变化
- 关键API接口变更
- 依赖关系调整

**更新流程：**
1. 修改相关源代码
2. 更新 `PROJECT_STRUCTURE.md` 中的对应章节
3. 更新依赖关系图（如有变化）
4. 更新代码统计信息

### 11.5 使用示例

**场景：需要添加新的图片格式支持**

```python
# 步骤1：查询项目结构说明书
# 读取 PROJECT_STRUCTURE.md 中的"核心模块详解"部分
# 了解需要修改的模块：format_detector.py, constants.py, metadata_reader.py, metadata_writer.py

# 步骤2：定位到具体模块
# 根据说明书中的"关键类和函数速查"找到相关函数

# 步骤3：实施修改
# 1. 修改 constants.py 添加格式定义
# 2. 修改 format_detector.py 添加检测逻辑
# 3. 修改 metadata_reader.py 添加读取支持
# 4. 修改 metadata_writer.py 添加写入支持

# 步骤4：更新说明书
# 如果新增了重要的类或函数，更新 PROJECT_STRUCTURE.md
```

**场景：需要修改UI界面**

```python
# 步骤1：查询项目结构说明书
# 读取 PROJECT_STRUCTURE.md 中的"ui/ 目录"部分
# 了解UI架构：app.py（主窗口）、widgets.py（组件）、batch_dialog.py（对话框）

# 步骤2：定位到具体组件
# 根据说明书中的"关键类和函数速查"找到相关组件

# 步骤3：实施修改
# 参考说明书中的代码示例和最佳实践
```

---

## 附录

### A. 常用代码模板

#### 新增文件格式支持

1. 在 `constants.py` 中添加格式定义
2. 在 `format_detector.py` 中添加检测逻辑
3. 在 `metadata_reader.py` 中添加读取支持
4. 在 `metadata_writer.py` 中添加写入支持
5. 添加测试用例

#### 新增UI组件

1. 创建组件类，继承适当的基类
2. 实现线程安全的UI更新
3. 添加配置支持
4. 添加滚动支持（如需要）
5. 编写文档字符串

### B. 问题排查清单

- [ ] 检查日志文件获取详细错误信息
- [ ] 验证文件格式是否正确检测
- [ ] 确认ExifTool是否可用（特殊格式）
- [ ] 检查文件权限和路径有效性
- [ ] 验证元数据字段映射是否正确
- [ ] 测试回退机制是否正常工作

### C. 参考资源

- [EXIF标准](https://www.exif.org/Exif2-2.PDF)
- [XMP规范](https://www.adobe.com/devnet/xmp.html)
- [ExifTool文档](https://exiftool.org/)
- [Pillow文档](https://pillow.readthedocs.io/)
- [piexif文档](https://github.com/hMatoba/piexif)

---

**文档版本**: 1.0  
**最后更新**: 2026-05-29  
**维护者**: King_photo 开发团队