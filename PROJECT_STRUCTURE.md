# King_photo 项目结构说明书

## 目录

- [项目概述](#项目概述)
- [目录结构](#目录结构)
- [核心模块详解](#核心模块详解)
  - [core/ 目录](#core-目录)
  - [ui/ 目录](#ui-目录)
  - [utils/ 目录](#utils-目录)
- [入口文件](#入口文件)
- [配置和资源](#配置和资源)
- [测试代码](#测试代码)
- [模块依赖关系](#模块依赖关系)
- [关键类和函数速查](#关键类和函数速查)

---

## 项目概述

**项目名称**: King_photo - 图片元信息编辑与修复工具  
**项目类型**: Python桌面GUI应用  
**技术栈**: Python 3.9+ / tkinter + ttkbootstrap / Pillow / piexif / lxml / exiftool  
**版本**: v1.3.0

### 核心功能
1. 图片元信息查看与编辑（EXIF、XMP、IPTC）
2. 批量重命名（支持20+变量）
3. 文件修复（后缀修复、时间修复）
4. 格式支持：JPEG、PNG、GIF、WebP、TIFF、HEIC、RAW、AVIF、SVG等
5. **统一API层**：编程方式访问所有功能（v1.3.0新增）
6. **插件系统**：动态扩展格式和功能支持（v1.3.0新增）

---

## 目录结构

```
King_photo/
├── src/                          # 源代码目录
│   ├── __init__.py               # 包初始化
│   ├── main.py                   # 程序入口
│   │
│   ├── core/                     # 核心业务逻辑 ⬅ 实现 I* 接口
│   │   ├── __init__.py
│   │   ├── format_detector.py    # 格式检测器 (IFormatDetector)
│   │   ├── metadata_reader.py    # 元数据读取引擎 (IMetadataReader)
│   │   ├── metadata_writer.py    # 元数据写入引擎 (IMetadataWriter)
│   │   ├── exif_handler.py       # EXIF处理
│   │   ├── xmp_handler.py        # XMP处理
│   │   ├── repair_engine.py      # 修复引擎 (IRepairEngine)
│   │   └── file_processor.py     # 文件处理器 (IFileProcessor)
│   │
│   ├── ui/                       # 用户界面 ⬅ 通过 get_api() 访问
│   │   ├── __init__.py
│   │   ├── app.py                # 主应用窗口
│   │   ├── folder_view.py        # 文件夹模式视图
│   │   ├── single_view.py        # 单图片模式视图
│   │   ├── batch_dialog.py       # 批量操作对话框
│   │   └── widgets.py            # 自定义UI组件
│   │
│   ├── api/                      # 统一API层（v1.3.0新增）
│   │   ├── __init__.py           # API模块初始化 + 公共导出
│   │   ├── interfaces.py         # 核心接口定义（ABC抽象类）
│   │   ├── plugin_interfaces.py  # 插件接口定义（IFormat/IFunction/IExtension）
│   │   ├── unified_api.py        # KingPhotoAPI 统一入口（get_api/reset_api）
│   │   └── plugin_manager.py     # 插件管理器（加载/注册/管理）
│   │
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── constants.py          # 常量定义
│       ├── helpers.py            # 辅助函数
│       ├── exiftool_wrapper.py   # ExifTool封装
│       ├── config_manager.py     # 配置管理器
│       ├── config_center.py      # 统一配置中心（v1.3.0新增）
│       ├── error_handler.py      # 统一错误处理（v1.3.0新增）
│       ├── logging_config.py     # 日志配置
│       └── error_report.py       # 错误报告
│
├── plugins/                      # 插件目录（v1.3.0新增）
│   ├── formats/                  # 格式插件（PNG、HEIC、WebP、JPEG）
│   ├── functions/                # 功能插件（批量重命名、批量修复、批量导出）
│   ├── extensions/               # 扩展插件（水印等）
│   └── plugin_config.json        # 插件配置文件
│
├── assets/                       # 资源文件
│   └── icons/                    # 图标资源
│
├── config/                       # 配置文件目录
│   └── settings.json             # 用户配置
│
├── logs/                         # 日志文件目录
│   └── king_photo_YYYY-MM-DD.log
│
├── tests/                        # 测试代码
│   ├── __init__.py
│   ├── conftest.py               # pytest配置和共享fixtures
│   ├── api/                      # API层测试（v1.3.0新增）
│   │   ├── __init__.py
│   │   ├── test_unified_api.py   # KingPhotoAPI测试（39个）
│   │   └── test_plugin_manager.py # PluginManager测试（18个）
│   ├── plugins/                  # 插件测试（v1.3.0新增）
│   │   ├── __init__.py
│   │   ├── test_format_plugins.py    # 格式插件接口测试
│   │   └── test_function_plugins.py  # 功能插件接口测试
│   ├── test_format_detector.py
│   ├── test_metadata_reader.py
│   ├── test_metadata_writer.py
│   ├── test_repair_engine.py
│   ├── test_helpers.py
│   └── test_data/                # 测试数据
│
├── run.py                        # 启动脚本
├── build.py                      # 打包脚本
├── api_example.py                # API使用示例（v1.3.0新增）
├── test_program.py               # 程序测试脚本
├── requirements.txt              # 依赖列表
├── README.md                     # 项目说明
├── PLUGIN_DOC.md                 # 插件开发文档（v1.3.0新增）
├── DEVELOPMENT_RULES.md          # 开发规则
└── PROJECT_STRUCTURE.md          # 项目结构说明书（本文件）
```

---

## 核心模块详解

### core/ 目录

核心业务逻辑层，不包含任何UI代码。

#### 1. format_detector.py - 格式检测器

**职责**: 通过文件头魔数检测真实文件格式

**主要类**:
- `FormatDetector`: 格式检测器类

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `detect_by_header(filepath)` | 通过文件头检测格式 | `Optional[str]` |
| `detect_by_extension(filepath)` | 通过扩展名检测格式 | `Optional[str]` |
| `get_real_format(filepath)` | 获取真实格式 | `Tuple[Optional[str], bool]` |
| `is_truly_image(filepath)` | 检查是否为真正的图片 | `Tuple[bool, str]` |
| `is_video_file(filepath)` | 检查是否为视频文件 | `Tuple[bool, str]` |
| `get_format_info(filepath)` | 获取格式详细信息 | `dict` |

**依赖**: `constants.FILE_SIGNATURES`, `constants.SUPPORTED_FORMATS`

**代码行数**: ~250行

---

#### 2. metadata_reader.py - 元数据读取引擎

**职责**: 统一的元信息读取接口，支持所有格式

**主要类**:
- `MetadataReader`: 元数据读取器

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `read_metadata(filepath)` | 读取完整元信息 | `Dict[str, Any]` |
| `get_datetime(filepath)` | 快速获取拍摄时间 | `Optional[datetime]` |
| `get_summary(filepath)` | 获取元信息摘要 | `Dict[str, Any]` |
| `get_editable_fields(filepath)` | 获取可编辑字段 | `Dict[str, Any]` |

**内部方法**:
- `_read_exif()`: 读取EXIF信息
- `_read_xmp()`: 读取XMP信息
- `_read_with_exiftool()`: 使用ExifTool读取
- `_get_image_size()`: 获取图片尺寸

**依赖**: `format_detector`, `exif_handler`, `xmp_handler`, `exiftool_wrapper`

**代码行数**: ~300行

---

#### 3. metadata_writer.py - 元数据写入引擎

**职责**: 统一的元信息写入接口

**主要类**:
- `MetadataWriter`: 元数据写入器

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `write_metadata(filepath, metadata, copy_mode, output_dir)` | 写入元信息 | `Dict[str, Any]` |
| `write_metadata_from_filetime(filepath, copy_mode, output_dir)` | 将文件时间复制到EXIF | `Dict[str, Any]` |
| `batch_write_metadata(file_list, metadata, ...)` | 批量写入元信息 | `Dict[str, Any]` |

**内部方法**:
- `_write_exif()`: 写入EXIF（带回退）
- `_write_exif_with_piexif()`: 使用piexif写入
- `_write_exif_with_exiftool_fallback()`: 使用ExifTool回退写入
- `_write_with_exiftool()`: 使用ExifTool写入

**依赖**: `format_detector`, `exif_handler`, `xmp_handler`, `exiftool_wrapper`

**代码行数**: ~550行

---

#### 4. exif_handler.py - EXIF处理

**职责**: EXIF格式数据的读写处理

**主要类**:
- `ExifHandler`: EXIF处理器

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `read_exif(filepath)` | 读取EXIF数据 | `Dict[str, Any]` |
| `write_exif(filepath, metadata)` | 写入EXIF数据 | `bool` |
| `get_datetime(filepath)` | 获取EXIF时间 | `Optional[datetime]` |
| `has_exif(filepath)` | 检查是否有EXIF | `bool` |

**依赖**: `piexif`, `exiftool_wrapper`

**代码行数**: ~350行

---

#### 5. xmp_handler.py - XMP处理

**职责**: XMP格式数据的读写处理（PNG、SVG、WebP等）

**主要类**:
- `XmpHandler`: XMP处理器

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `read_xmp_from_png(filepath)` | 从PNG读取XMP | `Dict[str, Any]` |
| `read_xmp_from_file(filepath)` | 从文件读取XMP | `Dict[str, Any]` |
| `write_xmp(filepath, metadata)` | 写入XMP（自动路由） | `bool` |
| `write_xmp_to_png(filepath, metadata)` | 写入XMP到PNG | `bool` |
| `write_xmp_to_svg(filepath, metadata)` | 写入XMP到SVG | `bool` |
| `write_xmp_to_webp(filepath, metadata)` | 写入XMP到WebP | `bool` |
| `get_datetime(xmp_data)` | 从XMP数据获取时间 | `Optional[datetime]` |

**依赖**: `lxml`, `Pillow`, `exiftool_wrapper`

**代码行数**: ~450行

---

#### 6. repair_engine.py - 修复引擎

**职责**: 文件后缀修复、时间信息提取和修复

**主要类**:
- `RepairEngine`: 修复引擎

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `check_file_extension(filepath)` | 检查文件后缀 | `Dict[str, Any]` |
| `fix_extension(filepath, output_dir)` | 修复文件后缀 | `Dict[str, Any]` |
| `extract_time_info(filepath, time_source)` | 提取时间信息 | `Dict[str, Any]` |
| `repair(filepath, ...)` | 完整修复流程 | `Dict[str, Any]` |
| `batch_repair(file_list, ...)` | 批量修复 | `Dict[str, Any]` |
| `batch_repair_extension(file_list, ...)` | 批量修复后缀 | `Dict[str, Any]` |

**依赖**: `format_detector`, `metadata_reader`, `metadata_writer`, `helpers`

**代码行数**: ~670行

---

#### 7. file_processor.py - 文件处理器

**职责**: 文件批量处理和文件夹操作

**主要类**:
- `FileProcessor`: 文件处理器

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `get_image_files(folder_path)` | 获取文件夹中的图片 | `List[str]` |
| `process_files(file_list, operation)` | 批量处理文件 | `Dict[str, Any]` |

**代码行数**: ~150行

---

### ui/ 目录

用户界面层，使用tkinter + ttkbootstrap。UI层现在通过统一API访问核心模块，不再直接导入Core层。

#### 1. app.py - 主应用窗口

**职责**: 主窗口、菜单、工具栏、模式切换

**主要类**:
- `MainWindow`: 主窗口类

**关键方法**:
| 方法 | 功能 |
|------|------|
| `_create_menu()` | 创建菜单栏 |
| `_create_toolbar()` | 创建工具栏 |
| `_create_statusbar()` | 创建状态栏 |
| `_open_folder()` | 打开文件夹 |
| `_open_single_image()` | 打开单张图片 |
| `_batch_rename()` | 批量重命名 |
| `_batch_edit_metadata()` | 批量编辑元信息 |
| `_repair_with_dialog()` | 修复对话框 |

**依赖**: `folder_view`, `single_view`, `api`, `config_manager`

**代码行数**: ~600行

---

#### 2. folder_view.py - 文件夹模式视图

**职责**: 文件夹模式下的缩略图网格显示

**主要类**:
- `FolderView`: 文件夹视图

**关键方法**:
| 方法 | 功能 |
|------|------|
| `load_folder(folder_path)` | 加载文件夹 |
| `_create_thumbnail_grid()` | 创建缩略图网格 |
| `_select_all()` | 全选 |
| `_invert_selection()` | 反选 |
| `get_selected_files()` | 获取选中的文件 |

**依赖**: `widgets.ThumbnailWidget`

**代码行数**: ~400行

---

#### 3. single_view.py - 单图片模式视图

**职责**: 单张图片的预览和编辑

**主要类**:
- `SingleView`: 单图片视图

**关键方法**:
| 方法 | 功能 |
|------|------|
| `load_image(filepath)` | 加载图片 |
| `_show_preview()` | 显示预览 |
| `_show_metadata()` | 显示元数据 |
| `_save_metadata()` | 保存元数据 |
| `_repair_image()` | 修复图片 |

**依赖**: `widgets.ImagePreviewWidget`, `widgets.MetadataEditorWidget`, `metadata_reader`, `metadata_writer`

**代码行数**: ~500行

---

#### 4. batch_dialog.py - 批量操作对话框

**职责**: 批量操作的对话框界面

**主要类**:
- `RenameDialog`: 重命名对话框
- `RepairDialog`: 修复对话框
- `BatchMetadataDialog`: 批量元数据编辑对话框

**关键特性**:
- 使用Canvas + Scrollbar实现可滚动内容
- 支持进度显示和取消操作
- 响应式布局

**依赖**: `repair_engine`, `metadata_writer`

**代码行数**: ~800行

---

#### 5. widgets.py - 自定义UI组件

**职责**: 可复用的UI组件

**主要类**:
| 类名 | 功能 |
|------|------|
| `ThumbnailWidget` | 缩略图组件 |
| `ImagePreviewWidget` | 图片预览组件 |
| `MetadataEditorWidget` | 元数据编辑器 |
| `ProgressDialog` | 进度对话框 |
| `ScrollableFrame` | 可滚动框架 |

**关键特性**:
- `ThumbnailWidget`: 支持异步加载、错误显示、选择状态
- `MetadataEditorWidget`: 格式自适应字段显示、按类别分组
- `ProgressDialog`: 支持取消操作、进度回调

**代码行数**: ~700行

---

### api/ 目录（v1.3.0 新增）

统一API层，提供编程接口和插件系统。

#### 1. unified_api.py - 统一API入口

**职责**: 提供所有功能的统一编程访问接口

**主要类**:
- `KingPhotoAPI`: 统一API入口

**辅助函数**:
- `get_api(config_path, plugin_dir)`: 获取API单例实例
- `reset_api()`: 重置API单例

**API分类**:
| 分类 | 方法 | 功能 |
|------|------|------|
| 格式检测 | `detect_format()`, `is_supported()`, `get_supported_formats()` | 文件格式检测 |
| 元数据读取 | `read_metadata()`, `get_datetime()`, `get_summary()`, `get_editable_fields()`, `read_exif()`, `read_xmp()` | 读取元信息 |
| 元数据写入 | `write_metadata()`, `write_metadata_from_filetime()`, `batch_write_metadata()`, `write_exif()`, `write_xmp()`, `copy_filetime_to_exif()` | 写入元信息 |
| 修复 | `check_file_extension()`, `fix_extension()`, `extract_time_info()`, `repair_file()`, `batch_repair()`, `batch_repair_extension()` | 文件修复 |
| 文件处理 | `get_image_files()`, `rename_files()`, `copy_files()`, `move_files()`, `delete_files()` | 文件操作 |
| 插件管理 | `register_plugin()`, `get_plugins()`, `enable_plugin()`, `disable_plugin()` | 插件管理 |
| 配置管理 | `get_config()`, `set_config()`, `save_config()`, `load_config()` | 配置操作 |
| 工具函数 | `format_file_size()`, `format_datetime()`, `parse_datetime()`, `get_unique_filename()`, `sanitize_filename()` | 实用工具 |

**依赖**: 延迟导入 `core/` 和 `utils/` 模块，通过 `_ensure_initialized()` 触发初始化

**代码行数**: ~770行

---

#### 2. interfaces.py - 核心接口定义

**职责**: 使用Python ABC定义核心模块的抽象接口

**接口列表**:
| 接口名 | 职责 | 抽象方法数 |
|--------|------|------------|
| `IFormatDetector` | 格式检测接口 | 5 |
| `IMetadataReader` | 元数据读取接口 | 6 |
| `IMetadataWriter` | 元数据写入接口 | 5 |
| `IRepairEngine` | 修复引擎接口 | 5 |
| `IFileProcessor` | 文件处理接口 | 6 |

**代码行数**: ~200行

---

#### 3. plugin_interfaces.py - 插件接口定义

**职责**: 定义三种插件类型的抽象接口

**接口列表**:
| 接口名 | 职责 | 核心方法 |
|--------|------|----------|
| `IFormatPlugin` | 格式插件（扩展新格式支持） | `read_metadata()`, `write_metadata()`, `get_datetime()` |
| `IFunctionPlugin` | 功能插件（扩展新功能） | `execute()`, `get_parameters()` |
| `IExtensionPlugin` | 扩展插件（拦截/增强现有功能） | `before_execute()`, `after_execute()`, `on_error()` |

**代码行数**: ~170行

---

#### 4. plugin_manager.py - 插件管理器

**职责**: 插件的加载、注册、管理和生命周期

**主要类**:
- `PluginManager`: 插件管理器

**关键方法**:
| 方法 | 功能 |
|------|------|
| `load_plugins(plugin_dir)` | 从目录加载所有插件 |
| `register_format_plugin(plugin)` | 注册格式插件 |
| `register_function_plugin(plugin)` | 注册功能插件 |
| `register_extension_plugin(plugin)` | 注册扩展插件 |
| `get_format_plugin(name)` | 按名称获取格式插件 |
| `get_format_plugin_by_file(filepath)` | 按文件查找格式插件 |
| `get_all_plugins()` | 获取所有已注册插件 |
| `enable_plugin(name)` | 启用插件 |
| `disable_plugin(name)` | 禁用插件 |

**代码行数**: ~400行

---

### plugins/ 目录（v1.3.0 新增）

#### 格式插件 (plugins/formats/)

| 文件 | 插件类 | 支持的格式 |
|------|--------|-----------|
| `jpeg_plugin.py` | JPEGFormatPlugin | .jpg, .jpeg |
| `png_plugin.py` | PNGFormatPlugin | .png |
| `heic_plugin.py` | HEICFormatPlugin | .heic, .heif |
| `webp_plugin.py` | WebPFormatPlugin | .webp |

#### 功能插件 (plugins/functions/)

| 文件 | 插件类 | 功能 |
|------|--------|------|
| `batch_rename_plugin.py` | BatchRenamePlugin | 批量重命名 |
| `batch_repair_plugin.py` | BatchRepairPlugin | 批量修复 |
| `batch_export_plugin.py` | BatchExportPlugin | 批量导出 |

#### 扩展插件 (plugins/extensions/)

| 文件 | 插件类 | 功能 |
|------|--------|------|
| `watermark_plugin.py` | WatermarkPlugin | 水印扩展 |

---

### utils/ 目录

通用工具函数层，无业务逻辑。

#### 1. constants.py - 常量定义

**职责**: 所有常量定义

**主要常量**:
| 常量名 | 功能 |
|--------|------|
| `SUPPORTED_FORMATS` | 支持的格式定义（扩展名、EXIF/XMP支持、是否需要ExifTool） |
| `FILE_SIGNATURES` | 文件头魔数签名 |
| `EXIF_TIME_FIELDS` | EXIF时间字段优先级 |
| `XMP_TIME_FIELDS` | XMP时间字段 |
| `EXIF_FIELDS` | EXIF字段定义（标签ID、名称、可编辑性） |
| `XMP_FIELDS` | XMP字段定义 |
| `RENAME_VARIABLES` | 重命名变量映射 |
| `TIME_PATTERNS` | 时间格式正则表达式 |
| `ALL_EXTENSIONS` | 所有支持的扩展名列表 |

**代码行数**: ~200行

---

#### 2. helpers.py - 辅助函数

**职责**: 通用辅助函数

**主要函数**:
| 函数名 | 功能 | 返回值 |
|--------|------|--------|
| `get_file_extension(filepath)` | 获取文件扩展名 | `str` |
| `is_supported_image(filepath)` | 检查是否支持的图片 | `bool` |
| `get_image_files_in_folder(folder)` | 获取文件夹中的图片 | `List[str]` |
| `format_file_size(size_bytes)` | 格式化文件大小 | `str` |
| `format_datetime(dt)` | 格式化日期时间 | `str` |
| `parse_datetime(dt_str)` | 解析日期时间字符串 | `Optional[datetime]` |
| `extract_time_from_filename(filename)` | 从文件名提取时间 | `Optional[datetime]` |
| `generate_renamed_filename(...)` | 生成重命名文件名 | `str` |
| `sanitize_filename(filename)` | 清理文件名非法字符 | `str` |
| `set_file_times(filepath, dt, ...)` | 设置文件时间 | `bool` |
| `get_file_times(filepath)` | 获取文件时间信息 | `dict` |
| `ensure_output_folder(path)` | 确保输出文件夹存在 | `str` |
| `get_unique_filename(filepath)` | 获取唯一文件名 | `str` |

**代码行数**: ~350行

---

#### 3. exiftool_wrapper.py - ExifTool封装

**职责**: ExifTool命令行工具封装

**主要类**:
- `ExifToolWrapper`: ExifTool封装类

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `read_metadata(filepath)` | 读取元信息 | `Dict[str, Any]` |
| `write_metadata(filepath, metadata)` | 写入元信息 | `bool` |
| `copy_filetime_to_exif(filepath)` | 复制文件时间到EXIF | `bool` |
| `fix_filename_extension(filepath)` | 修复文件扩展名 | `bool` |
| `rename_by_modification_time(filepath)` | 根据修改时间重命名 | `bool` |
| `get_datetime(filepath)` | 获取拍摄时间 | `Optional[datetime]` |
| `get_basic_info(filepath)` | 获取基本信息 | `Dict[str, Any]` |

**关键特性**:
- 单例模式（`get_exiftool()`）
- 短路径支持（`_get_short_path()`处理中文路径）
- charset选项（`-charset filename=utf8 -charset utf8`）

**代码行数**: ~450行

---

#### 4. config_manager.py - 配置管理器

**职责**: JSON配置文件管理

**主要类**:
- `ConfigManager`: 配置管理器

**关键方法**:
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `get(key, default)` | 获取配置项 | `Any` |
| `set(key, value)` | 设置配置项 | `None` |
| `save()` | 保存配置 | `None` |
| `load()` | 加载配置 | `None` |

**配置层级**: 使用点号分隔的层级（如`window.width`）

**代码行数**: ~200行

---

#### 5. config_center.py - 统一配置中心（v1.3.0新增）

**职责**: 统一配置管理，支持观察者模式和配置验证

**主要类**:
- `ConfigCenter`: 统一配置中心

**关键方法**:
| 方法 | 功能 |
|------|------|
| `get(key, default)` | 获取配置项（支持点号分隔层级） |
| `set(key, value)` | 设置配置项 |
| `save()` | 保存配置到文件 |
| `load()` | 从文件加载配置 |
| `add_observer(observer)` | 添加配置观察者 |
| `remove_observer(observer)` | 移除配置观察者 |
| `notify_observers(key, value)` | 通知配置变更 |

**代码行数**: ~200行

---

#### 6. error_handler.py - 统一错误处理（v1.3.0新增）

**职责**: 层次化错误类体系

**错误类层级**:
```
KingPhotoError (基类)
├── FormatError         # 格式检测错误
├── MetadataError       # 元数据读写错误
├── FileError           # 文件操作错误
├── RepairError         # 修复错误
├── PluginError         # 插件错误
│   ├── PluginLoadError
│   ├── PluginExecutionError
│   └── PluginDependencyError
├── ConfigError         # 配置错误
└── ExifToolError       # ExifTool错误
```

**代码行数**: ~100行

---

#### 7. logging_config.py - 日志配置

**职责**: 统一日志配置

**主要类**:
- `CategorizedLogStorage`: 分类日志存储

**关键特性**:
- 按级别分类存储
- 退出时按优先级写入（ERROR→WARNING→INFO→DEBUG）
- 每次运行覆盖日志文件

**代码行数**: ~150行

---

#### 8. error_report.py - 错误报告

**职责**: 错误汇总和导出

**主要类**:
- `ErrorReport`: 错误报告

**关键方法**:
| 方法 | 功能 |
|------|------|
| `generate_error_report_from_batch_result(result)` | 从批量结果生成报告 |
| `show_error_report_dialog(parent, report)` | 显示错误报告对话框 |
| `export_to_file(report, filepath)` | 导出到文件 |

**代码行数**: ~250行

---

## 入口文件

### run.py - 启动脚本

**功能**: 程序入口点

**代码内容**:
```python
import sys
import os

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == '__main__':
    main()
```

### src/main.py - 主模块

**功能**: 初始化应用程序

**主要功能**:
1. 配置日志系统
2. 注册HEIC格式支持（pillow_heif）
3. 创建并启动主窗口

---

## 配置和资源

### config/settings.json

**功能**: 用户配置持久化

**配置项示例**:
```json
{
  "window": {
    "width": 1200,
    "height": 800
  },
  "paths": {
    "last_folder": "",
    "output_dir": ""
  },
  "rename": {
    "default_format": "{datetime}"
  },
  "repair": {
    "default_time_source": "auto",
    "fix_extension": true,
    "fix_time": true
  }
}
```

### assets/icons/

**功能**: 图标资源文件

---

## 测试代码

### tests/ 目录

**测试文件**:
| 文件名 | 测试内容 | 测试数 |
|--------|----------|--------|
| `api/test_unified_api.py` | KingPhotoAPI全面测试 | 39 |
| `api/test_plugin_manager.py` | PluginManager测试 | 18 |
| `plugins/test_format_plugins.py` | 格式插件接口一致性 | 参数化 |
| `plugins/test_function_plugins.py` | 功能插件接口一致性 | 参数化 |
| `test_format_detector.py` | 格式检测器测试 | ~20 |
| `test_metadata_reader.py` | 元数据读取测试 | ~15 |
| `test_metadata_writer.py` | 元数据写入测试 | ~15 |
| `test_repair_engine.py` | 修复引擎测试 | ~15 |
| `test_helpers.py` | 辅助函数测试 | ~10 |

**测试配置**: `conftest.py` 提供共享 fixtures（`sample_jpg`, `sample_png`, `tmp_output_dir` 等）

**测试数据**: `test/` 目录包含各种格式的真实图片（jpg/png/jpeg/webp/gif等）

---

## 模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                          UI层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  app.py  │  │folder_view│  │single_view│  │batch_dialog│  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │          │
│       └──────────────┴──────────────┴──────────────┘          │
│                          │                                    │
│                    widgets.py                                 │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       API层                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │               unified_api.py (KingPhotoAPI)            │ │
│  │               plugin_manager.py (PluginManager)        │ │
│  │               interfaces.py (抽象接口)                  │ │
│  │               plugin_interfaces.py (插件接口)           │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        Core层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │format_   │  │metadata_ │  │metadata_ │  │repair_   │   │
│  │detector  │  │reader    │  │writer    │  │engine    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │          │
│       └──────────────┴──────────────┴──────────────┘          │
│                          │                                    │
│         ┌────────────────┼────────────────┐                  │
│         ▼                ▼                ▼                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │exif_     │  │xmp_      │  │file_     │                  │
│  │handler   │  │handler   │  │processor │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       Utils层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │constants │  │helpers   │  │exiftool_ │  │config_   │   │
│  │          │  │          │  │wrapper   │  │manager   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │logging_  │  │error_    │                                │
│  │config    │  │report    │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

**依赖规则**:
1. **UI层** → 只能导入API层和Utils层
2. **API层** → 可以导入Core层和Utils层
3. **Core层** → 只能导入Utils层
4. **Utils层** → 不能导入Core层、API层或UI层

---

## 关键类和函数速查

### 格式检测
```python
# 格式检测器
from src.core.format_detector import FormatDetector

# 检测格式
format_name = FormatDetector.detect_by_header(filepath)  # 通过文件头
format_name = FormatDetector.detect_by_extension(filepath)  # 通过扩展名
real_format, is_consistent = FormatDetector.get_real_format(filepath)  # 获取真实格式

# 格式验证
is_image, msg = FormatDetector.is_truly_image(filepath)
is_video, msg = FormatDetector.is_video_file(filepath)
format_info = FormatDetector.get_format_info(filepath)
```

### 元数据读取
```python
# 元数据读取器
from src.core.metadata_reader import MetadataReader

# 读取元数据
metadata = MetadataReader.read_metadata(filepath)
dt = MetadataReader.get_datetime(filepath)
summary = MetadataReader.get_summary(filepath)
editable_fields = MetadataReader.get_editable_fields(filepath)
```

### 元数据写入
```python
# 元数据写入器
from src.core.metadata_writer import MetadataWriter

# 写入元数据
result = MetadataWriter.write_metadata(filepath, metadata, copy_mode=True)
result = MetadataWriter.write_metadata_from_filetime(filepath)
results = MetadataWriter.batch_write_metadata(file_list, metadata)
```

### 修复引擎
```python
# 修复引擎
from src.core.repair_engine import RepairEngine

# 检查和修复
check_result = RepairEngine.check_file_extension(filepath)
ext_result = RepairEngine.fix_extension(filepath, output_dir)
time_info = RepairEngine.extract_time_info(filepath, time_source='auto')

# 完整修复
result = RepairEngine.repair(filepath, rename_format='{datetime}', output_dir=output_dir)

# 批量修复
results = RepairEngine.batch_repair(file_list, rename_format='{datetime}')
results = RepairEngine.batch_repair_extension(file_list)
```

### 统一API（推荐使用）
```python
# 推荐：通过统一API访问所有功能
from src.api import KingPhotoAPI, get_api

api = KingPhotoAPI()  # 或 get_api() 全局单例

# 格式检测
format_info = api.detect_format(filepath)
is_supported = api.is_supported(filepath)

# 元数据读写
metadata = api.read_metadata(filepath)
dt = api.get_datetime(filepath)
api.write_metadata(filepath, {"title": "test"}, copy_mode=True)

# 修复
api.repair_file(filepath, fix_extension=True, time_source='auto')
api.batch_repair(file_list, output_dir=output_dir)

# 插件管理
api.register_plugin(MyPlugin())
plugins = api.get_plugins()
```

### 插件开发
```python
from src.api.plugin_interfaces import IFormatPlugin

class MyFormatPlugin(IFormatPlugin):
    @property
    def format_name(self): return "MYFMT"
    @property
    def extensions(self): return [".myfmt"]
    @property
    def magic_numbers(self): return [b"MYFM"]
    @property
    def description(self): return "My format plugin"
    
    def read_metadata(self, filepath): ...
    def write_metadata(self, filepath, metadata): ...
    def get_datetime(self, filepath): ...

# 注册插件
api = get_api()
api.register_plugin(MyFormatPlugin())
```

### ExifTool封装
```python
from src.utils.exiftool_wrapper import get_exiftool
et = get_exiftool()
if et.is_available:
    metadata = et.read_metadata(filepath)
```

### 工具函数
```python
from src.utils.helpers import (
    extract_time_from_filename, set_file_times,
    get_unique_filename, sanitize_filename,
    format_file_size, format_datetime
)
from src.utils.config_manager import get_config_manager
config = get_config_manager()
config.get('window.width', 1200)
```

---

## 代码统计

| 模块 | 文件数 | 代码行数（估计） |
|------|--------|------------------|
| core/ | 7 | ~2,700行 |
| ui/ | 5 | ~3,000行 |
| api/ | 4 | ~1,500行 |
| plugins/ | 8 | ~500行 |
| utils/ | 8 | ~1,800行 |
| 入口/测试 | 15 | ~2,000行 |
| **总计** | **47** | **~11,500行** |

---

## 使用说明

### 快速定位代码

1. **查看格式检测逻辑**: `src/core/format_detector.py`
2. **查看元数据读取**: `src/core/metadata_reader.py`
3. **查看元数据写入**: `src/core/metadata_writer.py`
4. **查看修复流程**: `src/core/repair_engine.py`
5. **查看UI主窗口**: `src/ui/app.py`
6. **查看缩略图组件**: `src/ui/widgets.py` → `ThumbnailWidget`
7. **查看ExifTool集成**: `src/utils/exiftool_wrapper.py`
8. **查看常量定义**: `src/utils/constants.py`
9. **查看API接口**: `src/api/unified_api.py` (v1.3.0)
10. **查看插件接口**: `src/api/plugin_interfaces.py` (v1.3.0)
11. **查看插件开发文档**: `PLUGIN_DOC.md` (v1.3.0)

### 添加新功能

1. **添加新格式支持（插件方式—推荐）**:
   - 创建 `plugins/formats/myformat_plugin.py` 实现 `IFormatPlugin`
   - 通过 `PluginManager` 自动加载

2. **添加新格式支持（传统方式）**:
   - 修改 `constants.py` 添加格式定义
   - 修改 `format_detector.py` 添加检测逻辑

3. **添加新UI功能**:
   - 修改 `app.py` 添加菜单/工具栏
   - 在 `widgets.py` 中创建新组件
   - 使用 `batch_dialog.py` 模式创建对话框

4. **添加新的A元数据字段**:
   - 修改 `constants.py` 添加字段定义
   - 修改 `exif_handler.py` 和 `xmp_handler.py` 添加处理
   - 修改 `metadata_writer.py` 添加写入支持

---

**文档版本**: 1.0  
**最后更新**: 2026-05-29  
**维护者**: King_photo 开发团队
