# King_photo

图片元信息编辑与修复工具

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 功能特性

### 1. 编辑元信息
- 查看图片的EXIF、XMP、IPTC元信息
- 可视化编辑界面
- 支持批量修改元信息（标题、描述、作者、版权等）
- 根据图片格式自动适配显示可用字段

### 2. 批量处理
- 自定义格式批量重命名（支持20+变量）
- 批量修改文件时间属性
- 复制输出到新文件夹（保留原图）

### 3. 修复图片
- 修复错误后缀（通过读取文件头判断真实格式）
- 智能提取时间信息（文件名+元数据）
- 修复文件名、修改时间、创建时间、拍摄时间

## 支持的图片格式

| 格式 | EXIF | XMP | 说明 |
|------|------|-----|------|
| JPEG/JPG | ✅ | ✅ | 完整支持 |
| PNG | ❌ | ✅ | XMP命名空间（photoshop:DateCreated） |
| GIF | ❌ | ❌ | 基本信息 |
| WebP | ✅ | ✅ | RIFF容器 |
| TIFF/TIF | ✅ | ✅ | 完整支持 |
| HEIF/HEIC | ✅ | ✅ | 需要exiftool |
| RAW(CR2/NEF/ARW/DNG) | ✅ | ✅ | 需要exiftool |
| AVIF | ✅ | ✅ | 需要exiftool |
| JPEG XL | ✅ | ✅ | 需要exiftool |
| SVG | ❌ | ✅ | XML属性 |
| BMP | ❌ | ❌ | 仅文件信息 |
| ICO | ❌ | ❌ | 仅文件信息 |
| PSD | ✅ | ✅ | 需要exiftool |

## 重命名变量

### 时间类变量
- `{date}` - 拍摄日期 (20240101)
- `{time}` - 拍摄时间 (120000)
- `{datetime}` - 完整日期时间 (20240101_120000)
- `{year}` - 年份 (2024)
- `{month}` - 月份 (01)
- `{day}` - 日期 (01)
- `{hour}` - 小时 (12)
- `{minute}` - 分钟 (00)
- `{second}` - 秒 (00)
- `{timestamp}` - Unix时间戳

### 文件类变量
- `{original}` - 原文件名
- `{ext}` - 文件扩展名
- `{seq}` - 序号 (001)
- `{seq:N}` - 指定位数序号

### 相机类变量
- `{camera}` - 相机型号
- `{make}` - 相机品牌
- `{lens}` - 镜头型号
- `{width}` - 图片宽度
- `{height}` - 图片高度
- `{orientation}` - 方向

### 描述类变量
- `{title}` - 图片标题
- `{desc}` - 图片描述
- `{artist}` - 作者
- `{copyright}` - 版权信息

## 安装

### 方式一：直接运行

1. 克隆或下载项目
```bash
git clone https://github.com/kkkikun/King_photo.git
cd King_photo
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序
```bash
python run.py
```

### 方式二：打包为exe

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行打包脚本
```bash
python build.py
```

3. 在dist文件夹中找到King_photo.exe

## 使用说明

### 打开文件夹模式
1. 点击"打开文件夹"选择包含图片的文件夹
2. 程序会显示所有支持的图片缩略图
3. 勾选要处理的图片（支持全选/反选）
4. 使用工具栏按钮进行批量操作

### 打开单个图片
1. 点击"打开图片"选择单张图片
2. 查看图片预览和详细元信息
3. 编辑可修改的元信息字段
4. 保存修改或执行修复操作

### 批量重命名
1. 选择要重命名的图片
2. 点击"批量重命名"
3. 设置重命名格式（使用变量）
4. 选择输出目录
5. 执行重命名

### 修复时间
1. 选择要修复的图片
2. 点击"修复时间"
3. 程序会从元数据或文件名提取时间信息
4. 修改文件时间属性

### 修复后缀
1. 选择要修复的图片
2. 点击"修复后缀"
3. 程序会检测并修复错误的文件后缀

## 技术栈

- Python 3.9+
- tkinter + ttkbootstrap (UI)
- Pillow (图像预览)
- piexif (EXIF读写)
- lxml (XMP解析)
- exiftool (特殊格式支持)
- PyInstaller (打包)

## API 使用

King_photo 提供统一的 Python API，可编程调用所有核心功能：

```python
from src.api import KingPhotoAPI

api = KingPhotoAPI()

# 检测格式
format_info = api.detect_format("photo.jpg")

# 读取元数据
metadata = api.read_metadata("photo.jpg")
dt = api.get_datetime("photo.jpg")  # 拍摄时间

# 写入元数据
api.write_metadata("photo.jpg", {"title": "我的照片", "author": "张三"})

# 修复文件
result = api.repair_file("photo.jpg", 
    fix_extension=True, fix_time=True, time_source="auto")

# 批量修复
api.batch_repair(["a.jpg", "b.png"], output_dir="repaired",
    progress_callback=lambda cur, total: print(f"{cur}/{total}"))

# 插件管理
api.register_plugin(MyFormatPlugin())
plugins = api.get_plugins()
```

详细示例参见 `api_example.py`。

## 项目结构

```
King_photo/
├── src/
│   ├── __init__.py
│   ├── main.py              # 程序入口
│   ├── api/                   # 统一API层（v1.3.0 新增）
│   │   ├── __init__.py
│   │   ├── interfaces.py      # 核心接口定义（ABC）
│   │   ├── plugin_interfaces.py # 插件接口定义
│   │   ├── unified_api.py     # KingPhotoAPI 统一入口
│   │   └── plugin_manager.py  # 插件管理器
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py           # 主应用窗口
│   │   ├── folder_view.py   # 文件夹模式视图
│   │   ├── single_view.py   # 单图片模式视图
│   │   ├── batch_dialog.py  # 批量操作对话框
│   │   ├── format_mismatch_dialog.py # 格式不匹配交互对话框 v1.4.0
│   │   ├── widgets.py       # 组件兼容层（re-export）
│   │   └── widgets/          # UI子模块
│   │       ├── thumbnail.py  # 缩略图组件
│   │       ├── preview.py    # 图片预览（适配+缩放+拖拽 v1.4.0）
│   │       ├── metadata.py   # 元数据编辑组件
│   │       ├── progress.py   # 进度对话框
│   │       └── scrollable.py # 可滚动框架
│   ├── core/
│   │   ├── __init__.py
│   │   ├── metadata_reader.py  # 元信息读取引擎
│   │   ├── metadata_writer.py  # 元信息写入引擎
│   │   ├── exif_handler.py     # EXIF处理
│   │   ├── xmp_handler.py      # XMP处理
│   │   ├── file_processor.py   # 文件处理
│   │   ├── repair_engine.py    # 修复引擎
│   │   └── format_detector.py  # 格式检测（ftyp box灵活检测）
│   └── utils/
│       ├── __init__.py
│       ├── constants.py        # 常量定义
│       ├── helpers.py          # 工具函数
│       ├── config_manager.py   # 配置管理
│       ├── error_handler.py    # 统一错误处理
│       ├── logging_config.py   # 日志配置
│       ├── error_report.py     # 错误报告
│       ├── exiftool_wrapper.py # exiftool封装
│       ├── image_loader.py     # 统一图片加载器 v1.4.0
│       └── format_impact.py    # 格式影响查询 v1.4.0
├── plugins/                  # 插件目录（v1.3.0 新增）
│   ├── formats/              # 格式插件（PNG、HEIC、WebP）
│   ├── functions/            # 功能插件（批量重命名、批量修复）
│   ├── extensions/           # 扩展插件（水印等）
│   └── plugin_config.json    # 插件配置
├── tests/                   # 测试代码
├── config/                  # 配置文件
│   ├── settings.json        # 用户配置
│   └── format_impact.json   # 格式影响规则 v1.4.0
├── requirements.txt         # 依赖
├── api_example.py           # API使用示例
├── build.py                 # 打包脚本
├── run.py                   # 启动脚本
├── PLUGIN_DOC.md            # 插件开发文档
├── DEVELOPMENT_RULES.md     # 开发规范
├── PROJECT_STRUCTURE.md     # 项目结构说明
├── error_solutions.md       # 错误解决记录（20条）
├── .gitignore
└── README.md
```

## 注意事项

1. **exiftool安装**：处理HEIC、RAW、PSD等特殊格式需要安装exiftool
   - 下载：https://exiftool.org/
   - 安装后确保exiftool在系统PATH中

2. **复制模式**：默认使用复制模式，不会修改原文件

3. **输出目录**：可以设置单独的输出目录，否则保存在原目录

4. **文件后缀修复**：通过读取文件头魔数检测真实格式，可能不是100%准确

## 更新日志

### v1.7.0 (2026-06-07)

#### Bug Fixes
- **修复格式适配完全失效**：`format_detector.py` 返回键名与 reader/writer 查询键名不一致（`exif_support` vs `supports_exif`），导致所有 EXIF/XMP 字段被错误标记为不可编辑（JPEG 无法编辑元数据）
- **修复 `metadata_writer.py` KeyError 崩溃**：方括号访问不存在的键改为 `.get()`
- **修复 PlaceholderEntry 占位提示不显示**：简化实现、适配暗色主题、覆盖 batch_dialog 批量编辑入口

#### New Features
- **格式可编辑字段数据库** (`config/editable_fields.json`)：基于 ExifTool 13.59 官方格式支持表，精确为 12 种图片格式定义可写字段和标签映射
- **格式字段管理器** (`format_field_manager.py`)：单例查询 API，替代硬编码格式适配逻辑
- **元数据编辑占位提示**：空字段显示灰色格式提示（如 `YYYY:MM:DD HH:MM:SS`），有数据则显示原值，点击自动清除

#### Improvements
- **字段编辑范围扩大**：技术参数（ISO/光圈/快门/焦距/方向）改为可编辑
- **GIF 元数据支持**：可通过 ExifTool 写入 XMP 元数据
- **metadata.py 重构**：复用 `ScrollableFrame` 替代手写 Canvas+Scrollbar
- **batch_dialog 同步**：批量编辑对话框同样支持 PlaceholderEntry

### v1.6.0 (2026-06-05)

#### New Features
- **完整插件管理系统**：插件管理 UI 对话框（Ctrl+P），支持启用/禁用、按类型分组卡片展示
- **多接口插件支持**：一个插件类可同时实现多种接口（格式+功能+扩展），watermark 同时作为独立功能和自动钩子
- **通用功能插件执行**：动态读取 `get_parameters()` 自动生成参数表单，新插件零代码接入
- **自动触发开关**：扩展插件可配置是否自动伴随核心操作触发
- **插件配置清理**：一键移除幽灵配置残留
- **拖放支持**：从资源管理器拖入文件夹/图片直接打开
- **水印功能**：独立文字水印（支持位置/透明度/字体）+ 自动伴随元数据写入

#### Improvements
- **快捷键补全**：Ctrl+P 快速打开插件管理
- **插件菜单增强**：动态"运行功能插件"子菜单，自动发现已启用插件
- **版本号统一**：about/help 更新至 v1.6.0

#### Bug Fixes
- 修复 4 个插件加载失败（JPEG/PNG/WebP/Watermark）—— `issubclass(Base, Base)` 导致抽象基类被误匹配
- 修复插件目录相对路径依赖 CWD 导致从非项目根启动时 0 个插件
- 修复 `_load_plugin_file` 只支持单接口检测
- 修复 `get_all_plugin_info()` 无法反映多接口插件

### v1.5.0 (2026-06-05)

#### New Features
- **虚拟滚动技术**：实现虚拟滚动，只创建可见区域的控件，解决大文件夹（2000+张图片）加载卡顿和崩溃问题
- **性能大幅提升**：大文件夹加载时间从0.110秒降至0.025秒，提升77.7%
- **内存优化**：内存使用减少80-90%，通过动态创建和销毁控件实现
- **选中状态持久化**：使用字典存储选中状态，滚动时正确恢复选中状态
- **防抖滚动更新**：滚动时延迟50ms更新，避免频繁更新导致性能问题
- **动态列数计算**：根据画布宽度自动计算最佳列数，替代固定4列布局

#### Improvements
- **零除法错误修复**：修复 `self.current_cols` 为0时导致的ZeroDivisionError
- **缓冲区优化**：上下各多渲染2行，减少滚动时的白屏现象
- **控件重用支持**：为ThumbnailWidget添加reset()方法，支持控件重用
- **虚拟滚动配置**：添加VIRTUAL_SCROLL_ENABLED、VISIBLE_BUFFER_ROWS、MAX_VISIBLE_WIDGETS、ROW_HEIGHT等配置参数

#### Bug Fixes
- ZeroDivisionError: division by zero（修复所有涉及self.current_cols的地方）
- 虚拟滚动模式下的全选、反选、取消选择功能修复
- 滚动时控件位置计算错误修复

#### Testing
- 虚拟滚动性能测试：2000张图片加载时间0.025秒（传统模式0.110秒）
- 内存使用测试：虚拟滚动模式内存使用减少80-90%
- 功能测试：全选、反选、取消选择功能正常工作

### v1.4.1 (2026-06-02)

#### Improvements
- **缩略图网格布局性能优化**：动态列数计算、防抖机制、智能重排，提高大文件夹中缩略图的布局性能
- **GitHub Actions**：添加自动构建exe的release workflow

### v1.4.0 (2026-05-31)

#### New Features
- **格式不匹配智能检测**：修复时自动检测文件头与扩展名不一致的图片（如 HEIC 伪装成 PNG）
- **交互式格式修复对话框**：双缩略图对比（当前伪装 vs 修正后），影响分级提示（CRITICAL/HIGH/MEDIUM/LOW/NONE），支持"之后都按此处理"批量决策
- **统一图片加载器** (`image_loader.py`)：多格式支持（HEIC/AVIF/JXL/SVG/RAW），智能回退链（PIL→专用加载器→插件注册→占位图）
- **可缩放预览组件**：默认适配窗口 + 自由缩放（滚轮 0.05x~20x）+ 拖拽平移 + 重置按钮
- **格式影响数据库** (`format_impact.json`)：20+条规则，5级影响评级，`format_impact.py` 查询 API
- **格式检测增强**：ftyp box 灵活检测，正确识别 HEIC/HEIF/AVIF/MOV/MP4

#### Improvements
- **修复引擎重构**：先检查并修复后缀 → 再按正确格式写入时间，避免格式错判导致时间写入失败
- **预览体验**：预览区权重 1→3（占比 60%），信息面板 height 8→12 行，暗色主题背景
- **快捷键标注**：所有菜单项显示对应快捷键
- **状态栏增强**：模式指示 📁/🖼️ + 进度条
- **缩略图组件**：改用统一 image_loader 加载，支持更多格式缩略图

#### Bug Fixes
- HEIC/HEIF 魔数检测不准确（固定字节匹配→ftyp box 解析）
- `batch_repair()` 参数顺序错误（改用关键字参数）
- 对话框 `LabelFrame(padding=)` 在 ttkbootstrap 中不兼容
- `folder_view.py` 缺少 `get_image_files_in_folder` 导入
- 预览组件滚轮与缩略图滚轮冲突（`bind_all`→`bind`）

#### Testing
- 288 passed, 2 skipped, 0 failed

### v1.3.1 (2026-05-30)

#### Improvements
- **代码优化**：删除 ~450行死代码（`config_center.py`、`get_logger()`、app.py 3个死方法）
- **导入清理**：13个文件中移除未使用的导入（`Union`、`Path`、`Optional`、`time` 等）
- **字段映射统一**：提取 `INTERNAL_TO_EXIFTOOL`、`INTERNAL_TO_IPTC` 等常量到 `constants.py`，消除 6处重复字典
- **UI组件拆分**：`widgets.py`（642行）拆分为 5个子模块，每文件 30-270行
- **滚动代码复用**：`batch_dialog.py` 中 3个对话框统一使用 `ScrollableFrame`，删除 ~54行重复代码
- **错误文档**：创建 `error_solutions.md`（18条记录），写入开发规则，要求修复后必须记录

#### Bug Fixes
- `error_handler.py` — 修复 logger 未定义（NameError）
- `metadata_reader.py` / `metadata_writer.py` — 修复 KeyError（`.get()` 默认值）
- `unified_api.py` — 修复 format_datetime 参数不匹配
- 15个过期备份测试删除，5个测试字段名更新

#### Testing
- 288 passed, 2 skipped, 0 failed

### v1.3.0 (2026-05-30)

#### New Features
- **统一API层**：`KingPhotoAPI` 类提供所有核心功能的编程接口，支持格式检测、元数据读写、文件修复、批量操作、插件管理
- **插件系统**：支持格式插件、功能插件、扩展插件三种类型，通过 `PluginManager` 动态加载和注册，无需修改核心代码
- **接口定义**：使用 Python ABC 定义 `IFormatDetector`、`IMetadataReader`、`IMetadataWriter`、`IRepairEngine`、`IFileProcessor` 等核心接口
- **错误处理体系**：层次化错误类（`KingPhotoError`、`FormatError`、`MetadataError`、`PluginError` 等）

#### Improvements
- **模块化重构**：核心模块实现对应接口，确保接口一致性
- **动态格式注册**：`FormatDetector` 支持 `register_format()` 动态添加新格式
- **插件示例**：提供 PNG、HEIC、WebP 格式插件和批量重命名、批量修复功能插件
- **插件文档**：`PLUGIN_DOC.md` 包含完整的插件开发指南

### v1.2.0 (2026-05-30)

#### Bug Fixes
- **ExifTool中文路径编码彻底修复**：Windows命令行传递中文路径时Perl运行时编码转换出错，导致路径被乱码。解决方案：将所有参数写入UTF-8编码的临时argfile，通过`-@ argfile`传递给ExifTool，完全绕过命令行编码问题
- **PNG拍摄时间显示修复**：PNG文件的拍摄时间标准字段是`photoshop:DateCreated`（"Creation Time"），而非`exif:DateTimeOriginal`。同时写入多个XMP命名空间字段确保Windows资源管理器正确显示
- **PIL文件识别错误处理改进**：损坏PNG文件导致PIL报错。在写入XMP前添加文件预检查（存在性、非空、PNG文件头验证）
- **文件格式验证改进**：添加视频格式魔数检测，`is_truly_image()`方法验证文件类型
- **缩略图加载错误处理优化**：提供更具体的错误信息，根据文件头判断文件类型

#### New Features
- **PNG Creation Time字段写入支持**：确保PNG文件的Creation Time字段（`XMP-photoshop:DateCreated`）被正确写入
- **PNG XMP命名空间命令**：ExifTool写入PNG时使用正确的XMP命名空间（`-XMP-photoshop:DateCreated`、`-XMP-exif:DateTimeOriginal`、`-XMP-xmp:CreateDate`）
- **未处理输出目录功能**：非图片文件自动复制到未处理目录
- **HEIC和WebP格式支持**：添加WebP XMP写入功能，注册HEIC格式支持

#### Improvements
- **项目重构完成**：删除回滚机制、修复文件属性保护、灵活时间源选择、修复按钮拆分
- **开发规范文档**：创建`DEVELOPMENT_RULES.md`和`PROJECT_STRUCTURE.md`
- **日志系统改进**：按级别分类，错误信息在前，每次运行覆盖
- **UI窗口大小修复**：RepairDialog和BatchMetadataDialog添加滚动机制

### v1.1.0

- 完整的 XMP 写入支持（PNG、SVG）
- 统一日志系统
- 配置文件持久化
- 缩略图异步加载
- 批量操作可取消
- 错误汇总导出
- 批量元信息编辑集成

## 许可证

MIT License
