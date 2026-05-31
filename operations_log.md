# King_photo 项目操作日志

## 2026-05-13

### 操作 1：更新 single_view.py 使用新 API
- **时间**: 2026-05-13
- **内容**: 重写 `single_view.py` 中的修复相关方法
- **变更**:
  - 删除旧方法 `_fix_time` 和 `_fix_extension`（调用不存在的 API）
  - 重写 `_full_repair` 使用 `RepairEngine.repair_with_backup()`
  - 实现缺失的 `_restore` 方法
  - 添加 `_original_file` 属性记录修复前的原始文件路径

### 操作 2：修复恢复功能逻辑
- **时间**: 2026-05-13
- **内容**: 解决修复后无法恢复的问题
- **变更**:
  - 添加 `_original_file` 属性跟踪原始文件
  - 修复后 UI 加载新文件，但恢复时通过 `_original_file` 找到 `.res` 备份
  - `load_image` 方法中重置 `_original_file`

### 操作 3：修复语法错误
- **时间**: 2026-05-13
- **内容**: 修复中文引号导致的字符串解析错误
- **变更**: 将 `"修复"` 改为 `[修复]` 避免引号冲突

### 操作 4：验证回滚机制
- **时间**: 2026-05-13
- **内容**: 运行完整测试验证修复 + 备份 + 恢复流程
- **测试结果**:
  - 修复时自动创建 `.res` 备份文件 ✓
  - 同一文件多次修复不会重复创建备份 ✓
  - 恢复功能正确还原原始文件内容 ✓
  - GIF 格式正确使用文件修改时间 ✓
  - 文件名中的时间戳正确提取 ✓
  - 文件修改时间被正确设置 ✓

---

## 2026-05-12（之前会话）

### 操作 5：创建 King_photo 项目
- **内容**: 从零搭建完整的图片元信息编辑与修复工具
- **模块**:
  - `src/core/format_detector.py` - 格式检测（魔数识别）
  - `src/core/exif_handler.py` - EXIF 元数据读写
  - `src/core/xmp_handler.py` - XMP 元数据解析
  - `src/core/metadata_reader.py` - 统一元数据读取接口
  - `src/core/metadata_writer.py` - 元数据写入引擎
  - `src/core/file_processor.py` - 文件处理（重命名、时间修复）
  - `src/core/repair_engine.py` - 修复引擎（后缀、时间修复）
  - `src/ui/app.py` - 主应用窗口
  - `src/ui/folder_view.py` - 文件夹模式视图
  - `src/ui/single_view.py` - 单图片模式视图
  - `src/ui/batch_dialog.py` - 批量操作对话框
  - `src/ui/widgets.py` - 自定义 UI 组件

### 操作 6：增强时间提取功能
- **内容**: 优化 `extract_time_from_filename` 支持更多格式
- **支持格式**:
  - mmexport 前缀（微信导出）
  - 13 位毫秒时间戳
  - img_ 前缀带负数 ID
  - Image_ 前缀
  - Cache_ 前缀
- **结果**: 时间提取率从 3.6% 提升到 69.3%

### 操作 7：添加回滚机制
- **内容**: 实现 `.res` 备份文件机制
- **功能**:
  - 修复前自动备份原文件为 `.res` 后缀
  - 支持从备份恢复
  - 同一文件只保留一个备份
  - 一键删除所有备份文件

### 操作 8：优化 UI 布局
- **内容**: 修复窗口显示问题
- **变更**:
  - RenameDialog 添加自适应屏幕大小和滚动条
  - 添加鼠标滚轮支持
  - RepairDialog 修复按钮被隐藏问题
