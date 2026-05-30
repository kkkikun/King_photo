# King_photo 错误解决记录

## 错误 1：single_view.py 调用不存在的 API

### 问题描述
`single_view.py` 中的 `_fix_time`、`_fix_extension`、`_full_repair` 方法调用了 `RepairEngine` 中不存在的方法：
- `RepairEngine.repair_time_info()` - 不存在
- `RepairEngine.fix_extension()` 参数错误（使用 `copy_mode` 而非 `output_dir`）
- `RepairEngine.full_repair()` - 不存在

### 错误原因
`repair_engine.py` 被重写后，旧的 API 方法被移除，但 `single_view.py` 未同步更新。

### 解决方案
1. 删除旧方法 `_fix_time` 和 `_fix_extension`
2. 重写 `_full_repair` 使用新 API `RepairEngine.repair_with_backup()`
3. 参数从 `copy_mode` 改为 `output_dir`

### 涉及文件
- `src/ui/single_view.py`

---

## 错误 2：_restore 方法缺失导致 AttributeError

### 问题描述
工具栏中有"恢复"按钮绑定到 `self._restore`，但该方法未实现，点击会抛出 `AttributeError`。

### 错误原因
添加恢复按钮时忘记实现对应的方法。

### 解决方案
实现 `_restore()` 方法：
```python
def _restore(self):
    if not self.current_file:
        return
    target_file = self._original_file or self.current_file
    if not RepairEngine.has_backup(target_file):
        return
    result = RepairEngine.restore_from_backup(
        RepairEngine.get_backup_path(target_file)
    )
    if result['success']:
        self.load_image(result['restore_path'])
```

### 涉及文件
- `src/ui/single_view.py`

---

## 错误 3：修复后无法恢复（备份文件找不到）

### 问题描述
用户修复图片后，点击恢复按钮提示"没有找到备份文件"。

### 错误原因
修复后 UI 加载新文件（`self.current_file` 变为修复后的文件），但 `.res` 备份是原始文件的。`has_backup(repaired_file)` 返回 `False`。

### 解决方案
1. 添加 `self._original_file` 属性记录修复前的原始文件路径
2. `_restore` 方法优先使用 `_original_file` 查找备份
3. `load_image` 中重置 `_original_file`

### 关键代码
```python
# 修复时记录原始路径
original_path = self.current_file
result = RepairEngine.repair_with_backup(original_path, ...)
self._original_file = original_path

# 恢复时使用原始路径
target_file = self._original_file or self.current_file
```

### 涉及文件
- `src/ui/single_view.py`

---

## 错误 4：中文引号导致 SyntaxError

### 问题描述
```python
messagebox.showinfo("提示", "...通过"修复"功能...")
```
中文引号 `"修复"` 被 Python 解释器识别为字符串结束符，导致语法错误。

### 错误原因
中文全角引号 `""` 与 Python 字符串定界符 `""` 冲突。

### 解决方案
将中文引号改为方括号：
```python
messagebox.showinfo("提示", "...通过[修复]功能...")
```

### 涉及文件
- `src/ui/single_view.py`

---

## 错误 5：回滚机制不生效（.res 文件未生成）

### 问题描述
用户点击修复后，没有生成 `.res` 备份文件。

### 错误原因
`repair_with_backup` 方法中存在逻辑问题：
- 使用 `if not copy_mode:` 守卫，导致某些情况下跳过备份
- `batch_repair` 调用时传入了已废弃的 `copy_mode` 参数

### 解决方案
重写 `repair_engine.py`：
- 移除 `copy_mode` 参数
- 始终在 `output_dir` 创建备份
- 当 `output_dir=None` 时，使用源文件所在目录

### 关键代码
```python
if output_dir is None:
    output_dir = os.path.dirname(filepath)
backup_result = RepairEngine.create_backup(filepath, output_dir)
```

### 涉及文件
- `src/core/repair_engine.py`

---

## 错误 6：时间提取率过低（3.6%）

### 问题描述
初始测试 166 个文件，只有 6 个能提取到时间信息。

### 错误原因
`extract_time_from_filename` 只支持标准日期格式，不支持：
- 微信导出的 `mmexport` 前缀
- 13 位毫秒时间戳
- `img_` 前缀带负数 ID

### 解决方案
扩展正则表达式支持更多格式：
```python
# 13位毫秒时间戳
r'(?:mmexport|img_|Image_|Cache_)?(\d{13})'
# 带负数ID的格式
r'img_-?\d+_(\d{13})'
```

### 结果
时间提取率从 3.6% 提升到 69.3%（115/166）

### 涉及文件
- `src/utils/helpers.py`

---

## 错误 7：RenameDialog 窗口显示不全

### 问题描述
批量重命名对话框中，输出目录字段被窗口底部截断，需要手动拖动窗口才能看到。

### 错误原因
固定窗口大小，未考虑不同屏幕分辨率。

### 解决方案
1. 使用屏幕尺寸的百分比设置窗口大小（50% 宽度，60% 高度）
2. 添加 Canvas 滚动条
3. 绑定鼠标滚轮事件

### 涉及文件
- `src/ui/batch_dialog.py`

---

## 错误 8：exiftool_wrapper.py 语法错误

### 问题描述
```python
def _find_exiftool) ->:
```
缺少 `self` 参数。

### 错误原因
代码编写时遗漏了方法的 `self` 参数。

### 解决方案
```python
def _find_exiftool(self) -> str:
```

### 涉及文件
- `src/utils/exiftool_wrapper.py`

---

## 错误 9：ExifTool 中文路径编码错误

### 问题描述
ExifTool 处理含中文路径的文件时报错，路径被乱码为类似 `ͼƬ����` 的内容，导致所有含中文路径的文件操作失败。

### 错误原因
Python subprocess 通过 Windows 命令行传递 Unicode 字符串时，ExifTool 的 Perl 运行时在 `GetCommandLineA()` → `GetCommandLineW()` 转换过程中编码不一致。

### 解决方案
将所有参数和文件路径写入 UTF-8 编码的临时 argfile，通过 `-@ argfile` 传递给 ExifTool，完全绕过命令行编码问题。

### 关键代码
```python
# 新增方法
def _build_exiftool_args(self, **kwargs) -> List[str]:
    """构建参数列表"""
    
def _run_exiftool(self, filepath: str, args: List[str]) -> str:
    """通过argfile运行ExifTool"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                      delete=False, encoding='utf-8') as f:
        for arg in args:
            f.write(arg + '\n')
        f.write(filepath + '\n')
    # ... subprocess.run via -@ argfile
```

### 涉及文件
- `src/utils/exiftool_wrapper.py`

---

## 错误 10：PNG 拍摄时间写入后 Windows 资源管理器不显示

### 问题描述
PNG 文件拍摄时间通过 ExifTool 写入后，Windows 资源管理器中不显示。

### 错误原因
PNG 文件的拍摄时间标准字段是 `photoshop:DateCreated`（"Creation Time"），代码只写入了 `exif:DateTimeOriginal`，且没有写全 XMP 命名空间命令。

### 解决方案
1. `xmp_handler.py` 字段映射改为 `photoshop:DateCreated`
2. `exiftool_wrapper.py` 添加 PNG XMP 命名空间映射：
   - `-XMP-photoshop:DateCreated=...`（拍摄时间）
   - `-XMP-exif:DateTimeOriginal=...`（原始拍摄时间）
   - `-XMP-xmp:CreateDate=...`（创建时间）
3. `write_xmp_to_png()` 从 `img.info` 中移除旧 XMP 防止保留旧数据

### 涉及文件
- `src/core/xmp_handler.py`
- `src/utils/exiftool_wrapper.py`
- `src/utils/constants.py`

---

## 错误 11：PIL 无法识别损坏的 PNG 文件

### 问题描述
损坏的 PNG 文件导致 PIL `Image.open()` 抛出 "cannot identify image file" 错误。

### 错误原因
没有在打开文件前验证文件完整性。

### 解决方案
在 `xmp_handler.py` 的 `write_xmp_to_png()` 中添加文件预检查：
- 检查文件是否存在
- 检查文件是否非空
- 验证 PNG 文件头（`89 50 4E 47 0D 0A 1A 0A`）

### 涉及文件
- `src/core/xmp_handler.py`

---

## 错误 12：metadata_reader/metadata_writer KeyError

### 问题描述
```python
KeyError: 'needs_exiftool'
```
`metadata_reader.py:54` 和 `metadata_writer.py:90` 中使用 `format_info['needs_exiftool']` 直接访问字典键，但该键可能不存在。

### 错误原因
`FormatDetector.get_format_info()` 对某些格式不返回 `needs_exiftool` 字段。

### 解决方案
全部改用 `.get()` 方法设置默认值：
```python
# 修复前
if format_info['needs_exiftool']:
# 修复后
if format_info.get('needs_exiftool', False):
```

### 涉及文件
- `src/core/metadata_reader.py`
- `src/core/metadata_writer.py`

---

## 错误 13：unified_api.py format_datetime 参数不匹配

### 问题描述
```python
TypeError: format_datetime() takes 1 positional argument but 2 were given
```
`KingPhotoAPI.format_datetime()` 调用 `helpers.format_datetime(dt, format_str)` 但 `helpers.format_datetime` 只接受一个参数。

### 错误原因
API 层未适配 helpers 中的函数签名。

### 解决方案
```python
# 修复后
def format_datetime(self, dt, format_str=None):
    if format_str:
        return dt.strftime(format_str)
    return format_datetime(dt)  # helpers单参版本
```

### 涉及文件
- `src/api/unified_api.py`

---

## 错误 14：error_handler.py logger 未定义（NameError）

### 问题描述
`error_handler.py` 中多处调用 `logger.error()` / `logger.warning()`，但模块顶部未定义 `logger`，调用即抛出 `NameError`。

### 错误原因
遗漏了 `logger = logging.getLogger(__name__)` 声明。

### 解决方案
在模块顶部（import 语句后）添加：
```python
logger = logging.getLogger(__name__)
```

### 涉及文件
- `src/utils/error_handler.py`

---

## 错误 15：测试字段名与实际 API 不匹配

### 问题描述
测试中使用 `supports_exif`、`supports_xmp`、`needs_exiftool` 检查 `get_format_info()` 返回值，但实际 API 返回 `exif_support`、`xmp_support`、`need_exiftool`。

### 错误原因
API 重构后字段名变更，测试未同步更新。

### 解决方案
将测试中的字段名更新为实际 API 返回的名称：
```python
assert info.get('exif_support') is True   # 原 supports_exif
assert info.get('xmp_support') is True    # 原 supports_xmp
assert info.get('need_exiftool') is False # 原 needs_exiftool
```

`get_editable_fields()` 测试需跳过 `_format_info` 开头的特殊项。

### 涉及文件
- `tests/test_format_detector.py`
- `tests/test_metadata_reader.py`

---

## 错误 16：测试调用已删除的备份方法

### 问题描述
`test_repair_engine.py` 中 15 个测试调用已删除的方法（`get_backup_path`、`has_backup`、`create_backup` 等），全部失败。

### 错误原因
项目重构中删除了回滚机制，但对应测试未删除。

### 解决方案
删除 6 个备份相关测试类（142 行）：`TestBackupPath`、`TestHasBackup`、`TestCreateBackup`、`TestRestoreFromBackup`、`TestDeleteBackup`、`TestDeleteBackups`。

### 涉及文件
- `tests/test_repair_engine.py`

---

## 错误 17：exif_handler.py / metadata_writer.py 重复字段映射字典

### 问题描述
`exif_handler.py` 的 `field_mapping_et` 和 `metadata_writer.py` 的 `field_mapping` 在多个方法中重复定义，共 6 处重复。

### 错误原因
各方法独立定义映射字典，未提取公共常量。

### 解决方案
在 `constants.py` 新增统一映射常量：
```python
INTERNAL_TO_EXIFTOOL = {'artist': 'Artist', 'copyright': 'Copyright', ...}
INTERNAL_TO_IPTC = {'title': 'Title', 'description': 'Description', ...}
PIEIXF_VALID_FIELDS = {'artist', 'copyright', 'description', ...}
```
所有模块改为引用统一常量。

### 涉及文件
- `src/utils/constants.py`
- `src/core/exif_handler.py`
- `src/core/metadata_writer.py`

---

## 错误 18：batch_dialog.py 三个对话框重复实现滚动代码

### 问题描述
`RenameDialog`、`RepairDialog`、`BatchMetadataDialog` 各自重复 ~18 行 Canvas+Scrollbar 创建代码。

### 错误原因
未复用已有的 `ScrollableFrame` 组件。

### 解决方案
3 处全部替换为：
```python
sf = ScrollableFrame(self)
sf.pack(fill=tk.BOTH, expand=True)
main_frame = sf.scrollable_frame
```

### 涉及文件
- `src/ui/batch_dialog.py`

---

> **文档版本**: 2.0  
> **最后更新**: 2026-05-30  
> **维护规则**: 每次修复错误后，必须在本文档中添加新记录
