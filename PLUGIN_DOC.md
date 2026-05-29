# King_photo 插件开发文档

## 目录

- [1. 插件系统概述](#1-插件系统概述)
- [2. 插件类型](#2-插件类型)
- [3. 插件接口详解](#3-插件接口详解)
- [4. 插件开发指南](#4-插件开发指南)
- [5. 插件配置管理](#5-插件配置管理)
- [6. 插件加载机制](#6-插件加载机制)
- [7. 示例插件](#7-示例插件)
- [8. 常见问题](#8-常见问题)

---

## 1. 插件系统概述

King_photo 插件系统支持动态扩展应用功能，无需修改核心代码即可添加新的图片格式支持、功能扩展或行为修改。

### 1.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **插件接口** | `plugin_interfaces.py` | 定义所有插件类型的抽象接口 |
| **插件管理器** | `plugin_manager.py` | 负责插件的加载、注册、管理和执行 |
| **统一API** | `unified_api.py` | 提供插件集成的统一访问接口 |

### 1.2 插件目录结构

```
plugins/
├── formats/           # 格式插件目录
│   ├── jpeg_plugin.py
│   ├── png_plugin.py
│   ├── heic_plugin.py
│   └── webp_plugin.py
├── functions/         # 功能插件目录
│   ├── batch_export_plugin.py
│   ├── batch_rename_plugin.py
│   └── batch_repair_plugin.py
├── extensions/        # 扩展插件目录
│   └── watermark_plugin.py
└── plugin_config.json # 插件配置文件
```

---

## 2. 插件类型

King_photo 支持三种插件类型：

### 2.1 格式插件 (Format Plugin)

**用途**: 添加新的图片格式支持

**接口**: `IFormatPlugin`

**特点**:
- 定义格式名称、扩展名、文件头魔数
- 实现元数据读取、写入、时间获取
- 支持能力声明（EXIF/XMP/IPTC支持等）

**适用场景**:
- 添加新的图片格式支持（如TIFF、BMP、PSD）
- 自定义现有格式的处理逻辑
- 替换内置格式处理

### 2.2 功能插件 (Function Plugin)

**用途**: 添加新的功能模块

**接口**: `IFunctionPlugin`

**特点**:
- 定义插件名称、类型、版本
- 实现批量处理功能
- 支持参数定义和进度回调

**适用场景**:
- 批量导出/转换功能
- 批量重命名功能
- 批量修复功能
- 自定义批量处理逻辑

### 2.3 扩展插件 (Extension Plugin)

**用途**: 扩展现有模块的行为

**接口**: `IExtensionPlugin`

**特点**:
- 定义目标模块和优先级
- 实现执行前/后钩子和错误处理
- 支持依赖管理

**适用场景**:
- 在元数据写入前添加水印
- 在文件修复后添加日志记录
- 修改现有模块的行为

---

## 3. 插件接口详解

### 3.1 IFormatPlugin 接口

```python
class IFormatPlugin(ABC):
    """格式插件接口"""
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """格式名称，如 'JPEG', 'PNG', 'HEIC'"""
        pass
    
    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """支持的扩展名列表，如 ['.jpg', '.jpeg']"""
        pass
    
    @property
    @abstractmethod
    def magic_numbers(self) -> List[bytes]:
        """文件头魔数列表"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """格式描述"""
        pass
    
    @abstractmethod
    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        """读取元数据"""
        pass
    
    @abstractmethod
    def write_metadata(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        """写入元数据"""
        pass
    
    @abstractmethod
    def get_datetime(self, filepath: str) -> Optional[datetime]:
        """获取拍摄时间"""
        pass
    
    def is_available(self) -> bool:
        """检查插件是否可用"""
        return True
    
    def get_capabilities(self) -> Dict[str, bool]:
        """获取插件能力"""
        return {
            "exif_support": False,
            "xmp_support": False,
            "iptc_support": False,
            "write_support": False,
            "batch_support": False
        }
```

### 3.2 IFunctionPlugin 接口

```python
class IFunctionPlugin(ABC):
    """功能插件接口"""
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """插件类型 ('batch', 'export', 'convert' 等)"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
    
    @abstractmethod
    def execute(self, file_list: List[str], **kwargs) -> Dict[str, Any]:
        """执行插件功能"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """获取插件参数定义"""
        pass
    
    def is_available(self) -> bool:
        """检查插件是否可用"""
        return True
    
    def get_progress_callback(self):
        """获取进度回调函数"""
        return None
```

### 3.3 IExtensionPlugin 接口

```python
class IExtensionPlugin(ABC):
    """扩展插件接口"""
    
    @property
    @abstractmethod
    def extension_name(self) -> str:
        """扩展名称"""
        pass
    
    @property
    @abstractmethod
    def target_module(self) -> str:
        """目标模块 ('format_detector', 'metadata_reader', 'metadata_writer', 'repair_engine')"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """扩展描述"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """扩展优先级（数字越小优先级越高）"""
        pass
    
    @abstractmethod
    def before_execute(self, *args, **kwargs) -> Any:
        """执行前钩子"""
        pass
    
    @abstractmethod
    def after_execute(self, result: Any, *args, **kwargs) -> Any:
        """执行后钩子"""
        pass
    
    @abstractmethod
    def on_error(self, error: Exception, *args, **kwargs) -> Any:
        """错误处理钩子"""
        pass
    
    def is_enabled(self) -> bool:
        """检查扩展是否启用"""
        return True
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的插件列表"""
        return []
```

---

## 4. 插件开发指南

### 4.1 创建格式插件

**步骤**:

1. 在 `plugins/formats/` 目录下创建 Python 文件
2. 实现 `IFormatPlugin` 接口
3. 定义插件元数据
4. 重启应用或重新加载插件

**示例**:

```python
from src.api.plugin_interfaces import IFormatPlugin

class TIFFFormatPlugin(IFormatPlugin):
    """TIFF格式插件"""
    
    @property
    def format_name(self) -> str:
        return "TIFF"
    
    @property
    def extensions(self) -> List[str]:
        return [".tif", ".tiff"]
    
    @property
    def magic_numbers(self) -> List[bytes]:
        return [b'II\x2a\x00', b'MM\x00\x2a']
    
    @property
    def description(self) -> str:
        return "TIFF图片格式插件"
    
    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        # 实现元数据读取
        pass
    
    def write_metadata(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        # 实现元数据写入
        pass
    
    def get_datetime(self, filepath: str) -> Optional[datetime]:
        # 实现时间获取
        pass

# 插件元数据
PLUGIN_METADATA = {
    "name": "TIFF Format Plugin",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "TIFF图片格式插件",
    "format_name": "TIFF"
}
```

### 4.2 创建功能插件

**步骤**:

1. 在 `plugins/functions/` 目录下创建 Python 文件
2. 实现 `IFunctionPlugin` 接口
3. 定义插件元数据
4. 重启应用或重新加载插件

**示例**:

```python
from src.api.plugin_interfaces import IFunctionPlugin

class BatchConvertPlugin(IFunctionPlugin):
    """批量转换插件"""
    
    @property
    def plugin_name(self) -> str:
        return "batch_convert"
    
    @property
    def plugin_type(self) -> str:
        return "convert"
    
    @property
    def description(self) -> str:
        return "批量转换图片格式"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def execute(self, file_list: List[str], **kwargs) -> Dict[str, Any]:
        # 实现批量转换逻辑
        pass
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "output_format": {
                "type": "str",
                "default": "jpeg",
                "required": False,
                "description": "输出格式"
            },
            "quality": {
                "type": "int",
                "default": 85,
                "required": False,
                "description": "输出质量"
            }
        }

# 插件元数据
PLUGIN_METADATA = {
    "name": "Batch Convert Plugin",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "批量转换图片格式插件",
    "plugin_name": "batch_convert"
}
```

### 4.3 创建扩展插件

**步骤**:

1. 在 `plugins/extensions/` 目录下创建 Python 文件
2. 实现 `IExtensionPlugin` 接口
3. 定义插件元数据
4. 重启应用或重新加载插件

**示例**:

```python
from src.api.plugin_interfaces import IExtensionPlugin

class LogExtensionPlugin(IExtensionPlugin):
    """日志扩展插件"""
    
    @property
    def extension_name(self) -> str:
        return "logging"
    
    @property
    def target_module(self) -> str:
        return "metadata_writer"
    
    @property
    def description(self) -> str:
        return "记录元数据写入日志"
    
    @property
    def priority(self) -> int:
        return 5  # 高优先级
    
    def before_execute(self, *args, **kwargs) -> Any:
        # 执行前记录日志
        print(f"准备写入元数据: {args}")
        return args, kwargs
    
    def after_execute(self, result: Any, *args, **kwargs) -> Any:
        # 执行后记录日志
        print(f"元数据写入完成: {result}")
        return result
    
    def on_error(self, error: Exception, *args, **kwargs) -> Any:
        # 错误处理
        print(f"元数据写入失败: {error}")
        return None

# 插件元数据
PLUGIN_METADATA = {
    "name": "Log Extension Plugin",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "日志扩展插件",
    "extension_name": "logging"
}
```

---

## 5. 插件配置管理

### 5.1 插件配置文件

插件配置存储在 `plugins/plugin_config.json` 文件中：

```json
{
  "JPEG Format Plugin": {
    "enabled": true
  },
  "PNG Format Plugin": {
    "enabled": true
  },
  "Batch Export Plugin": {
    "enabled": true,
    "output_dir": "exports"
  },
  "Watermark Extension Plugin": {
    "enabled": false,
    "config": {
      "text": "King_photo",
      "opacity": 0.5
    }
  }
}
```

### 5.2 配置字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `enabled` | bool | 插件是否启用 |
| `config` | dict | 插件自定义配置 |
| `priority` | int | 插件优先级（仅扩展插件） |

### 5.3 启用/禁用插件

通过API启用或禁用插件：

```python
from src.api.unified_api import get_api

api = get_api()

# 启用插件
api.enable_plugin("Watermark Extension Plugin")

# 禁用插件
api.disable_plugin("Watermark Extension Plugin")
```

---

## 6. 插件加载机制

### 6.1 自动加载

应用启动时，插件管理器会自动扫描插件目录：

1. 扫描 `plugins/formats/` 目录加载格式插件
2. 扫描 `plugins/functions/` 目录加载功能插件
3. 扫描 `plugins/extensions/` 目录加载扩展插件

### 6.2 加载流程

```
1. 检查插件配置文件
2. 遍历插件目录
3. 动态导入插件模块
4. 查找插件类（继承自对应接口）
5. 创建插件实例
6. 检查插件是否启用
7. 注册插件到管理器
```

### 6.3 手动加载

可以通过API手动注册插件：

```python
from src.api.unified_api import get_api

api = get_api()

# 创建插件实例
from plugins.formats.jpeg_plugin import JPEGFormatPlugin
plugin = JPEGFormatPlugin()

# 注册插件
api.register_plugin(plugin)
```

---

## 7. 示例插件

### 7.1 格式插件示例

| 插件 | 文件 | 说明 |
|------|------|------|
| JPEG | `plugins/formats/jpeg_plugin.py` | JPEG格式支持 |
| PNG | `plugins/formats/png_plugin.py` | PNG格式支持 |
| HEIC | `plugins/formats/heic_plugin.py` | HEIC/HEIF格式支持 |
| WebP | `plugins/formats/webp_plugin.py` | WebP格式支持 |

### 7.2 功能插件示例

| 插件 | 文件 | 说明 |
|------|------|------|
| 批量导出 | `plugins/functions/batch_export_plugin.py` | 批量导出图片 |
| 批量重命名 | `plugins/functions/batch_rename_plugin.py` | 批量重命名文件 |
| 批量修复 | `plugins/functions/batch_repair_plugin.py` | 批量修复文件 |

### 7.3 扩展插件示例

| 插件 | 文件 | 说明 |
|------|------|------|
| 水印 | `plugins/extensions/watermark_plugin.py` | 添加水印扩展 |

---

## 8. 常见问题

### 8.1 插件无法加载

**可能原因**:
1. 插件文件语法错误
2. 未继承正确的接口类
3. 依赖缺失

**解决方法**:
1. 检查日志文件获取错误信息
2. 确保插件类继承自 `IFormatPlugin`、`IFunctionPlugin` 或 `IExtensionPlugin`
3. 安装缺失的依赖包

### 8.2 插件执行失败

**可能原因**:
1. 插件依赖的模块不可用
2. 参数配置错误
3. 文件权限问题

**解决方法**:
1. 检查插件 `is_available()` 方法返回值
2. 验证参数配置
3. 检查文件权限

### 8.3 插件冲突

**可能原因**:
1. 多个插件处理同一格式
2. 插件优先级设置不当

**解决方法**:
1. 确保同一格式只有一个插件
2. 调整扩展插件优先级

### 8.4 开发调试

**调试建议**:
1. 使用 `logging` 模块记录调试信息
2. 在插件中添加异常捕获和日志记录
3. 检查插件配置文件确认启用状态

---

## 附录

### A. 插件元数据字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | str | 是 | 插件显示名称 |
| `version` | str | 是 | 版本号 |
| `author` | str | 否 | 作者 |
| `description` | str | 是 | 插件描述 |
| `format_name` | str | 格式插件 | 格式名称 |
| `plugin_name` | str | 功能插件 | 插件标识名 |
| `extension_name` | str | 扩展插件 | 扩展标识名 |

### B. 插件能力字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `exif_support` | bool | 是否支持EXIF元数据 |
| `xmp_support` | bool | 是否支持XMP元数据 |
| `iptc_support` | bool | 是否支持IPTC元数据 |
| `write_support` | bool | 是否支持写入操作 |
| `batch_support` | bool | 是否支持批量操作 |
| `needs_exiftool` | bool | 是否需要ExifTool |

### C. 目标模块列表

| 模块名 | 说明 |
|--------|------|
| `format_detector` | 格式检测模块 |
| `metadata_reader` | 元数据读取模块 |
| `metadata_writer` | 元数据写入模块 |
| `repair_engine` | 修复引擎模块 |

---

**文档版本**: 1.0  
**最后更新**: 2026-05-30  
**维护者**: King_photo 开发团队