# King_photo

图片元信息编辑与修复工具

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
| PNG | ❌ | ✅ | tEXt/iTXt块 |
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
git clone https://github.com/yourusername/King_photo.git
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

## 项目结构

```
King_photo/
├── src/
│   ├── __init__.py
│   ├── main.py              # 程序入口
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py           # 主应用窗口
│   │   ├── folder_view.py   # 文件夹模式视图
│   │   ├── single_view.py   # 单图片模式视图
│   │   ├── batch_dialog.py  # 批量操作对话框
│   │   └── widgets.py       # 自定义组件
│   ├── core/
│   │   ├── __init__.py
│   │   ├── metadata_reader.py  # 元信息读取引擎
│   │   ├── metadata_writer.py  # 元信息写入引擎
│   │   ├── exif_handler.py     # EXIF处理
│   │   ├── xmp_handler.py      # XMP处理
│   │   ├── file_processor.py   # 文件处理
│   │   ├── repair_engine.py    # 修复引擎
│   │   └── format_detector.py  # 格式检测
│   └── utils/
│       ├── __init__.py
│       ├── constants.py        # 常量定义
│       ├── helpers.py          # 工具函数
│       └── exiftool_wrapper.py # exiftool封装
├── assets/                  # 图标等资源
├── tests/                   # 测试代码
├── requirements.txt         # 依赖
├── build.py                 # 打包脚本
├── run.py                   # 启动脚本
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

## 许可证

MIT License
