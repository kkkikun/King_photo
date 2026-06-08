# King_photo API 接口文档

**版本**: v1.7.1  
**最后更新**: 2026-06-08  
**项目版本**: v1.7.1

---

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [API参考](#api参考)
  - [格式检测API](#格式检测api)
  - [元数据读取API](#元数据读取api)
  - [元数据写入API](#元数据写入api)
  - [修复API](#修复api)
  - [文件处理API](#文件处理api)
  - [插件管理API](#插件管理api)
  - [配置管理API](#配置管理api)
  - [工具函数API](#工具函数api)
- [插件系统](#插件系统)
- [错误处理](#错误处理)
- [示例代码](#示例代码)

---

## 概述

King_photo API 是一个统一的图片元信息编辑与修复工具的编程接口。它提供了完整的图片处理功能，包括格式检测、元数据读写、文件修复、批量操作等。

### 主要特性

- **统一入口**: 通过 `KingPhotoAPI` 类访问所有功能
- **插件扩展**: 支持格式插件、功能插件和扩展插件
- **延迟初始化**: 按需加载核心模块，提高启动速度
- **线程安全**: 支持多线程环境下的并发访问
- **错误处理**: 完善的异常处理和错误报告机制

### 技术栈

- Python 3.9+
- Pillow (PIL)
- piexif
- lxml
- ExifTool (外部工具)

---

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from src.api import get_api

# 获取API实例（单例模式）
api = get_api()

# 检测文件格式
format_info = api.detect_format("image.jpg")
print(f"格式: {format_info['format']}")

# 读取元数据
metadata = api.read_metadata("image.jpg")
print(f"拍摄时间: {metadata['datetime']}")
print(f"文件大小: {metadata['filesize']} 字节")

# 写入元数据
new_metadata = {
    "title": "测试图片",
    "author": "King_photo",
    "description": "这是一个测试图片"
}
result = api.write_metadata("image.jpg", new_metadata, copy_mode=True)
if result["success"]:
    print(f"写入成功: {result['output_path']}")
```

### 使用单例模式

```python
from src.api import get_api, reset_api

# 获取单例实例
api = get_api()

# 重置单例（用于测试）
reset_api()
```

---

## API参考

### 格式检测API

#### `detect_format(filepath)`

检测文件格式。

**参数**:
- `filepath` (str): 文件路径

**返回**: `Dict[str, Any]`
```python
{
    "format": str,           # 格式名称，如 "JPEG", "PNG"
    "extension": str,        # 扩展名，如 ".jpg"
    "is_image": bool,        # 是否为图片
    "is_video": bool,        # 是否为视频
    "exif_support": bool,    # 是否支持EXIF
    "xmp_support": bool,     # 是否支持XMP
    "need_exiftool": bool,   # 是否需要ExifTool
    "plugin": str            # 使用的插件名称（如果有）
}
```

**示例**:
```python
api = get_api()
format_info = api.detect_format("photo.jpg")
print(format_info["format"])  # "JPEG"
print(format_info["exif_support"])  # True
```

#### `is_supported(filepath)`

检查文件是否支持。

**参数**:
- `filepath` (str): 文件路径

**返回**: `bool` - 是否支持

**示例**:
```python
if api.is_supported("image.heic"):
    print("HEIC格式受支持")
```

#### `get_supported_formats()`

获取所有支持的格式。

**返回**: `Dict[str, Dict[str, Any]]` - 格式字典

**示例**:
```python
formats = api.get_supported_formats()
for format_name, info in formats.items():
    print(f"{format_name}: {info['extensions']}")
```

### 元数据读取API

#### `read_metadata(filepath)`

读取完整元信息。

**参数**:
- `filepath` (str): 图片路径

**返回**: `Dict[str, Any]`
```python
{
    "filepath": str,         # 文件路径
    "filename": str,         # 文件名
    "extension": str,        # 扩展名
    "filesize": int,         # 文件大小（字节）
    "format": str,           # 格式信息
    "width": int,            # 宽度
    "height": int,           # 高度
    "datetime": datetime,    # 拍摄时间
    "exif": Dict,            # EXIF数据
    "xmp": Dict,             # XMP数据
    "file_created": datetime,# 文件创建时间
    "file_modified": datetime,# 文件修改时间
    "plugin": str            # 使用的插件（如果有）
}
```

**示例**:
```python
metadata = api.read_metadata("photo.jpg")
print(f"拍摄时间: {metadata['datetime']}")
print(f"尺寸: {metadata['width']}x{metadata['height']}")
```

#### `get_datetime(filepath)`

快速获取拍摄时间。

**参数**:
- `filepath` (str): 图片路径

**返回**: `Optional[datetime]` - 拍摄时间，如果无法获取则返回 `None`

**示例**:
```python
dt = api.get_datetime("photo.jpg")
if dt:
    print(f"拍摄时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
```

#### `get_metadata_summary(filepath)`

获取元信息摘要。

**参数**:
- `filepath` (str): 图片路径

**返回**: `Dict[str, Any]` - 摘要字典

#### `get_editable_fields(filepath)`

获取可编辑字段。

**参数**:
- `filepath` (str): 图片路径

**返回**: `Dict[str, Any]` - 可编辑字段字典，按类别分组

**示例**:
```python
fields = api.get_editable_fields("photo.jpg")
print("可编辑字段:")
for category, field_list in fields.items():
    print(f"  {category}: {field_list}")
```

#### `read_exif(filepath)`

读取EXIF数据。

**参数**:
- `filepath` (str): 图片路径

**返回**: `Dict[str, Any]` - EXIF数据字典

#### `read_xmp(filepath)`

读取XMP数据。

**参数**:
- `filepath` (str): 图片路径

**返回**: `Dict[str, Any]` - XMP数据字典

### 元数据写入API

#### `write_metadata(filepath, metadata, copy_mode=False, output_dir=None)`

写入元信息。

**参数**:
- `filepath` (str): 图片路径
- `metadata` (Dict[str, Any]): 元数据字典
- `copy_mode` (bool): 是否复制模式（保留原文件）
- `output_dir` (str): 输出目录（copy_mode=True时使用）

**返回**: `Dict[str, Any]`
```python
{
    "success": bool,         # 是否成功
    "message": str,          # 结果消息
    "output_path": str,      # 输出文件路径
    "modified_fields": list  # 修改的字段列表
}
```

**示例**:
```python
metadata = {
    "title": "风景照片",
    "author": "King_photo",
    "copyright": "© 2026 King_photo",
    "description": "美丽的风景"
}

# 直接修改原文件
result = api.write_metadata("photo.jpg", metadata)

# 复制模式（推荐）
result = api.write_metadata("photo.jpg", metadata, copy_mode=True, output_dir="output")
if result["success"]:
    print(f"保存到: {result['output_path']}")
```

#### `write_metadata_from_filetime(filepath, copy_mode=False, output_dir=None)`

将文件时间复制到EXIF。

**参数**:
- `filepath` (str): 图片路径
- `copy_mode` (bool): 是否复制模式
- `output_dir` (str): 输出目录

**返回**: `Dict[str, Any]` - 操作结果字典

**示例**:
```python
# 将文件修改时间写入EXIF
result = api.write_metadata_from_filetime("photo.jpg", copy_mode=True)
```

#### `batch_write_metadata(file_list, metadata, copy_mode=False, output_dir=None, progress_callback=None)`

批量写入元信息。

**参数**:
- `file_list` (List[str]): 文件列表
- `metadata` (Dict[str, Any]): 元数据字典
- `copy_mode` (bool): 是否复制模式
- `output_dir` (str): 输出目录
- `progress_callback`: 进度回调函数

**返回**: `Dict[str, Any]`
```python
{
    "total": int,        # 总文件数
    "success": int,      # 成功数
    "failed": int,       # 失败数
    "skipped": int,      # 跳过数
    "details": list      # 详细结果列表
}
```

**示例**:
```python
files = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
metadata = {"author": "King_photo"}

def progress(current, total):
    print(f"进度: {current}/{total}")

result = api.batch_write_metadata(files, metadata, progress_callback=progress)
print(f"成功: {result['success']}, 失败: {result['failed']}")
```

#### `write_exif(filepath, metadata)`

写入EXIF数据。

**参数**:
- `filepath` (str): 图片路径
- `metadata` (Dict[str, Any]): EXIF数据字典

**返回**: `bool` - 是否成功

#### `write_xmp(filepath, metadata)`

写入XMP数据。

**参数**:
- `filepath` (str): 图片路径
- `metadata` (Dict[str, Any]): XMP数据字典

**返回**: `bool` - 是否成功

#### `copy_filetime_to_exif(filepath)`

复制文件时间到EXIF。

**参数**:
- `filepath` (str): 图片路径

**返回**: `bool` - 是否成功

### 修复API

#### `check_file_extension(filepath)`

检查文件后缀。

**参数**:
- `filepath` (str): 文件路径

**返回**: `Dict[str, Any]`
```python
{
    "filepath": str,           # 文件路径
    "current_extension": str,  # 当前扩展名
    "real_format": str,        # 真实格式
    "need_fix": bool,          # 是否需要修复
    "confidence": float        # 置信度
}
```

**示例**:
```python
check = api.check_file_extension("image.png")
if check["need_fix"]:
    print(f"文件后缀错误: 实际是 {check['real_format']}")
```

#### `fix_extension(filepath, output_dir=None)`

修复文件后缀。

**参数**:
- `filepath` (str): 文件路径
- `output_dir` (str): 输出目录

**返回**: `Dict[str, Any]`
```python
{
    "success": bool,        # 是否成功
    "original_path": str,   # 原始路径
    "new_path": str,        # 新路径
    "old_extension": str,   # 旧扩展名
    "new_extension": str    # 新扩展名
}
```

#### `extract_time_info(filepath, time_source='auto')`

提取时间信息。

**参数**:
- `filepath` (str): 文件路径
- `time_source` (str): 时间来源 ('auto', 'filename', 'metadata', 'filetime')

**返回**: `Dict[str, Any]`
```python
{
    "datetime": datetime,  # 提取的时间
    "source": str,         # 时间来源
    "confidence": float    # 置信度
}
```

#### `repair_file(filepath, output_dir=None, fix_extension=True, fix_time=True, time_source='auto', rename_format=None)`

完整修复流程。

**参数**:
- `filepath` (str): 文件路径
- `output_dir` (str): 输出目录
- `fix_extension` (bool): 是否修复扩展名
- `fix_time` (bool): 是否修复时间
- `time_source` (str): 时间来源
- `rename_format` (str): 重命名格式

**返回**: `Dict[str, Any]` - 修复结果字典

**示例**:
```python
result = api.repair_file(
    "broken_image.jpg",
    output_dir="repaired",
    fix_extension=True,
    fix_time=True,
    time_source='auto'
)
if result["success"]:
    print(f"修复成功: {result['output_path']}")
```

#### `batch_repair(file_list, output_dir=None, fix_extension=True, fix_time=True, time_source='auto', rename_format=None, progress_callback=None)`

批量修复文件。

**参数**:
- `file_list` (List[str]): 文件列表
- `output_dir` (str): 输出目录
- `fix_extension` (bool): 是否修复扩展名
- `fix_time` (bool): 是否修复时间
- `time_source` (str): 时间来源
- `rename_format` (str): 重命名格式
- `progress_callback`: 进度回调函数

**返回**: `Dict[str, Any]` - 批量修复结果字典

#### `batch_repair_extension(file_list, output_dir=None, progress_callback=None)`

批量修复后缀。

**参数**:
- `file_list` (List[str]): 文件列表
- `output_dir` (str): 输出目录
- `progress_callback`: 进度回调函数

**返回**: `Dict[str, Any]` - 批量修复结果字典

### 文件处理API

#### `get_image_files(folder_path, recursive=False)`

获取文件夹中的图片文件。

**参数**:
- `folder_path` (str): 文件夹路径
- `recursive` (bool): 是否递归查找子文件夹

**返回**: `List[str]` - 图片文件路径列表

**示例**:
```python
files = api.get_image_files("photos/", recursive=True)
print(f"找到 {len(files)} 个图片文件")
```

#### `rename_files(file_list, pattern, output_dir=None, **kwargs)`

批量重命名文件。

**参数**:
- `file_list` (List[str]): 文件列表
- `pattern` (str): 重命名模式
- `output_dir` (str): 输出目录
- `**kwargs`: 额外参数

**返回**: `Dict[str, Any]` - 重命名结果字典

**重命名模式变量**:
- `{datetime}`: 拍摄时间 (20240101_120000)
- `{date}`: 拍摄日期 (20240101)
- `{time}`: 拍摄时间 (120000)
- `{year}`: 年份 (2024)
- `{month}`: 月份 (01)
- `{day}`: 日期 (01)
- `{hour}`: 小时 (12)
- `{minute}`: 分钟 (00)
- `{second}`: 秒 (00)
- `{filename}`: 原文件名
- `{extension}`: 扩展名
- `{index}`: 序号 (001)
- `{width}`: 宽度
- `{height}`: 高度

**示例**:
```python
files = api.get_image_files("photos/")
result = api.rename_files(files, "{date}_{time}_{index}", output_dir="renamed")
print(f"重命名 {result['success']} 个文件")
```

#### `copy_files(file_list, output_dir, preserve_structure=True)`

批量复制文件。

**参数**:
- `file_list` (List[str]): 文件列表
- `output_dir` (str): 输出目录
- `preserve_structure` (bool): 是否保持目录结构

**返回**: `Dict[str, Any]` - 复制结果字典

#### `move_files(file_list, output_dir, preserve_structure=True)`

批量移动文件。

**参数**:
- `file_list` (List[str]): 文件列表
- `output_dir` (str): 输出目录
- `preserve_structure` (bool): 是否保持目录结构

**返回**: `Dict[str, Any]` - 移动结果字典

#### `delete_files(file_list, backup=False, backup_dir=None)`

批量删除文件。

**参数**:
- `file_list` (List[str]): 文件列表
- `backup` (bool): 是否备份
- `backup_dir` (str): 备份目录

**返回**: `Dict[str, Any]` - 删除结果字典

### 插件管理API

#### `register_plugin(plugin)`

注册插件。

**参数**:
- `plugin`: 插件实例（必须实现 `IFormatPlugin`、`IFunctionPlugin` 或 `IExtensionPlugin`）

**示例**:
```python
from src.api.plugin_interfaces import IFormatPlugin

class MyFormatPlugin(IFormatPlugin):
    # 实现接口方法...
    pass

api = get_api()
api.register_plugin(MyFormatPlugin())
```

#### `get_plugins()`

获取所有已注册插件。

**返回**: `List[Dict[str, Any]]`
```python
[
    {
        "type": str,          # 插件类型: "format", "function", "extension"
        "name": str,          # 插件名称
        "description": str,   # 插件描述
        "class": str          # 插件类名
    },
    ...
]
```

#### `get_all_plugin_info()`

获取所有插件完整信息（含启用/禁用状态）。

**返回**: `List[Dict[str, Any]]` - 插件信息列表

#### `enable_plugin(plugin_name)`

启用插件。

**参数**:
- `plugin_name` (str): 插件名称

**返回**: `bool` - 是否成功

#### `disable_plugin(plugin_name)`

禁用插件。

**参数**:
- `plugin_name` (str): 插件名称

**返回**: `bool` - 是否成功

### 配置管理API

#### `get_config(key, default=None)`

获取配置项。

**参数**:
- `key` (str): 配置键
- `default`: 默认值

**返回**: 配置值

**示例**:
```python
window_width = api.get_config("window.width", 1200)
theme = api.get_config("theme", "darkly")
```

#### `set_config(key, value)`

设置配置项。

**参数**:
- `key` (str): 配置键
- `value`: 配置值

**示例**:
```python
api.set_config("window.width", 1400)
api.set_config("theme", "cosmo")
```

#### `save_config()`

保存配置到文件。

#### `load_config()`

从文件加载配置。

### 工具函数API

#### `format_file_size(size_bytes)`

格式化文件大小。

**参数**:
- `size_bytes` (int): 文件大小（字节）

**返回**: `str` - 格式化后的文件大小字符串

**示例**:
```python
size_str = api.format_file_size(1024 * 1024)  # "1.0 MB"
```

#### `format_datetime(dt, format_str=None)`

格式化日期时间。

**参数**:
- `dt` (datetime): 日期时间对象
- `format_str` (str): 格式字符串

**返回**: `str` - 格式化后的日期时间字符串

#### `parse_datetime(dt_str)`

解析日期时间字符串。

**参数**:
- `dt_str` (str): 日期时间字符串

**返回**: `Optional[datetime]` - 日期时间对象

#### `get_unique_filename(filepath)`

获取唯一文件名。

**参数**:
- `filepath` (str): 文件路径

**返回**: `str` - 唯一文件名

#### `sanitize_filename(filename)`

清理文件名非法字符。

**参数**:
- `filename` (str): 文件名

**返回**: `str` - 清理后的文件名

---

## 插件系统

### 插件类型

1. **格式插件 (IFormatPlugin)**: 添加新的文件格式支持
2. **功能插件 (IFunctionPlugin)**: 添加新的功能
3. **扩展插件 (IExtensionPlugin)**: 增强现有功能

### 插件接口

#### IFormatPlugin

```python
class IFormatPlugin(ABC):
    @property
    def format_name(self) -> str: ...          # 格式名称
    @property
    def extensions(self) -> List[str]: ...     # 支持的扩展名
    @property
    def magic_numbers(self) -> List[bytes]: ...# 文件头魔数
    @property
    def description(self) -> str: ...          # 格式描述
    
    def read_metadata(self, filepath: str) -> Dict[str, Any]: ...  # 读取元数据
    def write_metadata(self, filepath: str, metadata: Dict[str, Any]) -> bool: ...  # 写入元数据
    def get_datetime(self, filepath: str) -> Optional[datetime]: ...  # 获取拍摄时间
    def is_available(self) -> bool: ...        # 检查是否可用
    def get_capabilities(self) -> Dict[str, bool]: ...  # 获取能力
```

#### IFunctionPlugin

```python
class IFunctionPlugin(ABC):
    @property
    def plugin_name(self) -> str: ...          # 插件名称
    @property
    def plugin_type(self) -> str: ...          # 插件类型
    @property
    def description(self) -> str: ...          # 插件描述
    @property
    def version(self) -> str: ...              # 版本号
    
    def execute(self, file_list: List[str], **kwargs) -> Dict[str, Any]: ...  # 执行功能
    def get_parameters(self) -> Dict[str, Dict[str, Any]]: ...  # 获取参数定义
    def is_available(self) -> bool: ...        # 检查是否可用
```

#### IExtensionPlugin

```python
class IExtensionPlugin(ABC):
    @property
    def extension_name(self) -> str: ...       # 扩展名称
    @property
    def target_module(self) -> Union[str, List[str]]: ...  # 目标模块
    @property
    def description(self) -> str: ...          # 扩展描述
    @property
    def priority(self) -> int: ...             # 优先级
    
    def before_execute(self, *args, **kwargs) -> Any: ...  # 执行前钩子
    def after_execute(self, result: Any, *args, **kwargs) -> Any: ...  # 执行后钩子
    def on_error(self, error: Exception, *args, **kwargs) -> Any: ...  # 错误处理钩子
    def is_enabled(self) -> bool: ...          # 检查是否启用
```

### 插件目录结构

```
plugins/
├── formats/                  # 格式插件
│   ├── jpeg_plugin.py
│   ├── png_plugin.py
│   ├── heic_plugin.py
│   └── webp_plugin.py
├── functions/                # 功能插件
│   ├── batch_rename_plugin.py
│   ├── batch_repair_plugin.py
│   └── batch_export_plugin.py
├── extensions/               # 扩展插件
│   └── watermark_plugin.py
└── plugin_config.json        # 插件配置
```

### 插件配置

插件配置文件 `plugin_config.json`:

```json
{
  "enabled_plugins": {
    "jpeg_plugin": true,
    "png_plugin": true,
    "watermark_plugin": false
  },
  "plugin_settings": {
    "watermark_plugin": {
      "watermark_text": "© King_photo",
      "position": "bottom-right"
    }
  }
}
```

---

## 错误处理

### 异常类型

```python
from src.utils.error_handler import KingPhotoError, FormatError, MetadataError, PluginError

try:
    result = api.write_metadata("photo.jpg", metadata)
except FormatError as e:
    print(f"格式错误: {e}")
except MetadataError as e:
    print(f"元数据错误: {e}")
except PluginError as e:
    print(f"插件错误: {e}")
except KingPhotoError as e:
    print(f"King_photo错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 错误返回格式

所有写入/修复操作返回统一格式：

```python
{
    "success": bool,         # 是否成功
    "message": str,          # 结果消息
    "error_type": str,       # 错误类型
    "error_detail": str,     # 错误详情
    "skipped": bool          # 是否跳过
}
```

---

## 示例代码

### 完整示例

```python
import os
from src.api import get_api

def main():
    # 获取API实例
    api = get_api()
    
    # 1. 检测文件格式
    print("=== 格式检测 ===")
    format_info = api.detect_format("test.jpg")
    print(f"格式: {format_info['format']}")
    print(f"支持EXIF: {format_info['exif_support']}")
    
    # 2. 读取元数据
    print("\n=== 读取元数据 ===")
    metadata = api.read_metadata("test.jpg")
    print(f"拍摄时间: {metadata['datetime']}")
    print(f"尺寸: {metadata['width']}x{metadata['height']}")
    print(f"文件大小: {api.format_file_size(metadata['filesize'])}")
    
    # 3. 写入元数据
    print("\n=== 写入元数据 ===")
    new_metadata = {
        "title": "测试图片",
        "author": "King_photo",
        "copyright": "© 2026 King_photo"
    }
    result = api.write_metadata("test.jpg", new_metadata, copy_mode=True)
    if result["success"]:
        print(f"写入成功: {result['output_path']}")
    
    # 4. 修复文件
    print("\n=== 修复文件 ===")
    check = api.check_file_extension("broken.png")
    if check["need_fix"]:
        repair_result = api.repair_file("broken.png", output_dir="repaired")
        print(f"修复结果: {repair_result['success']}")
    
    # 5. 批量操作
    print("\n=== 批量操作 ===")
    files = api.get_image_files("photos/")
    if files:
        batch_result = api.batch_write_metadata(
            files[:5],
            {"author": "King_photo"},
            progress_callback=lambda c, t: print(f"进度: {c}/{t}")
        )
        print(f"批量写入: 成功{batch_result['success']}个")

if __name__ == "__main__":
    main()
```

### 批量重命名示例

```python
from src.api import get_api

api = get_api()

# 获取所有图片文件
files = api.get_image_files("photos/", recursive=True)

# 按拍摄时间重命名
result = api.rename_files(
    files,
    "{date}_{time}_{index}",
    output_dir="renamed"
)

print(f"重命名完成: {result['success']}个文件")
```

### 批量修复示例

```python
from src.api import get_api

api = get_api()

# 获取所有需要修复的文件
files = api.get_image_files("broken_photos/")
files_to_repair = []

for file in files:
    check = api.check_file_extension(file)
    if check["need_fix"]:
        files_to_repair.append(file)

# 批量修复
if files_to_repair:
    result = api.batch_repair(
        files_to_repair,
        output_dir="repaired",
        fix_extension=True,
        fix_time=True
    )
    print(f"修复完成: {result['success']}个文件")
```

---

## 附录

### 支持的图片格式

| 格式 | EXIF | XMP | IPTC | 说明 |
|------|------|-----|------|------|
| JPEG/JPG | ✅ | ✅ | ✅ | 完整支持 |
| PNG | ❌ | ✅ | ❌ | XMP命名空间 |
| GIF | ❌ | ❌ | ❌ | 基本信息 |
| WebP | ✅ | ✅ | ❌ | RIFF容器 |
| TIFF/TIF | ✅ | ✅ | ✅ | 完整支持 |
| HEIF/HEIC | ✅ | ✅ | ❌ | 需要ExifTool |
| RAW(CR2/NEF/ARW/DNG) | ✅ | ✅ | ❌ | 需要ExifTool |
| AVIF | ✅ | ✅ | ❌ | 需要ExifTool |
| JPEG XL | ✅ | ✅ | ❌ | 需要ExifTool |
| SVG | ❌ | ✅ | ❌ | XML属性 |
| BMP | ❌ | ❌ | ❌ | 仅文件信息 |
| ICO | ❌ | ❌ | ❌ | 仅文件信息 |
| PSD | ✅ | ✅ | ❌ | 需要ExifTool |

### 配置项参考

| 配置键 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `window.width` | int | 1200 | 窗口宽度 |
| `window.height` | int | 800 | 窗口高度 |
| `theme` | str | "darkly" | 主题名称 |
| `copy_mode` | bool | true | 默认复制模式 |
| `auto_repair` | bool | false | 自动修复 |
| `thumbnail_size` | int | 150 | 缩略图大小 |
| `max_recent_files` | int | 10 | 最近文件数 |

---

**文档版本**: 1.0  
**最后更新**: 2026-06-08  
**维护者**: King_photo 开发团队