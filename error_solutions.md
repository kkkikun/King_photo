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
