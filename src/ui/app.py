"""
King_photo - 主应用窗口
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional

from .folder_view import FolderView
from .single_view import SingleView
from ..core.metadata_reader import MetadataReader
from ..core.file_processor import FileProcessor
from ..core.repair_engine import RepairEngine
from ..core.metadata_writer import MetadataWriter
from ..utils.helpers import get_image_files_in_folder, is_supported_image


class MainWindow:
    """主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("King_photo - 图片元信息编辑与修复工具")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # 当前模式
        self.current_mode = None  # 'folder' or 'single'
        self.current_files = []
        self.output_dir = None

        # 创建UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_content()
        self._create_statusbar()

        # 初始化视图
        self.folder_view = FolderView(self.main_frame, self)
        self.single_view = SingleView(self.main_frame, self)

        # 默认显示文件夹模式
        self._show_folder_mode()

    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开文件夹", command=self._open_folder)
        file_menu.add_command(label="打开图片", command=self._open_single_image)
        file_menu.add_separator()
        file_menu.add_command(label="设置输出目录", command=self._set_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="全选", command=self._select_all)
        edit_menu.add_command(label="反选", command=self._invert_selection)
        edit_menu.add_command(label="取消选择", command=self._deselect_all)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="批量重命名", command=self._batch_rename)
        tools_menu.add_command(label="修复图片（带备份）", command=self._repair_with_dialog)
        tools_menu.add_separator()
        tools_menu.add_command(label="恢复上一次操作", command=self._restore_from_backup)
        tools_menu.add_command(label="删除备份文件", command=self._delete_backups)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
        help_menu.add_command(label="使用说明", command=self._show_help)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        # 打开文件夹按钮
        ttk.Button(
            toolbar,
            text="打开文件夹",
            command=self._open_folder
        ).pack(side=tk.LEFT, padx=2)

        # 打开图片按钮
        ttk.Button(
            toolbar,
            text="打开图片",
            command=self._open_single_image
        ).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 设置输出目录
        ttk.Button(
            toolbar,
            text="设置输出目录",
            command=self._set_output_dir
        ).pack(side=tk.LEFT, padx=2)

        # 输出目录显示
        self.output_dir_label = ttk.Label(toolbar, text="输出: 未设置")
        self.output_dir_label.pack(side=tk.LEFT, padx=5)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 批量操作按钮
        ttk.Button(
            toolbar,
            text="批量重命名",
            command=self._batch_rename
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="修复图片",
            command=self._repair_with_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="恢复",
            command=self._restore_from_backup
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="删除备份",
            command=self._delete_backups
        ).pack(side=tk.LEFT, padx=2)

    def _create_main_content(self):
        """创建主内容区域"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = ttk.Label(
            self.root,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _show_folder_mode(self):
        """显示文件夹模式"""
        self.single_view.hide()
        self.folder_view.show()
        self.current_mode = 'folder'

    def _show_single_mode(self):
        """显示单图片模式"""
        self.folder_view.hide()
        self.single_view.show()
        self.current_mode = 'single'

    def _open_folder(self):
        """打开文件夹"""
        folder_path = filedialog.askdirectory(title="选择图片文件夹")
        if folder_path:
            self.current_files = get_image_files_in_folder(folder_path)

            if not self.current_files:
                messagebox.showinfo("提示", "该文件夹中没有找到支持的图片文件")
                return

            self._show_folder_mode()
            self.folder_view.load_folder(folder_path, self.current_files)
            self._update_status(f"已加载 {len(self.current_files)} 张图片")

    def _open_single_image(self):
        """打开单个图片"""
        filetypes = [
            ("图片文件", "*.jpg *.jpeg *.png *.gif *.webp *.tif *.tiff *.heic *.heif *.bmp *.ico *.svg *.psd *.arw *.cr2 *.nef *.dng *.avif *.jxl"),
            ("所有文件", "*.*")
        ]

        filepath = filedialog.askopenfilename(
            title="选择图片",
            filetypes=filetypes
        )

        if filepath:
            self._show_single_mode()
            self.single_view.load_image(filepath)
            self._update_status(f"已加载: {os.path.basename(filepath)}")

    def _set_output_dir(self):
        """设置输出目录"""
        output_dir = filedialog.askdirectory(title="选择输出目录")
        if output_dir:
            self.output_dir = output_dir
            self.output_dir_label.configure(text=f"输出: {output_dir}")
            self._update_status(f"输出目录已设置: {output_dir}")

    def _select_all(self):
        """全选"""
        if self.current_mode == 'folder':
            self.folder_view.select_all()

    def _invert_selection(self):
        """反选"""
        if self.current_mode == 'folder':
            self.folder_view.invert_selection()

    def _deselect_all(self):
        """取消选择"""
        if self.current_mode == 'folder':
            self.folder_view.deselect_all()

    def _batch_rename(self):
        """批量重命名"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要重命名的图片")
            return

        # 打开重命名对话框
        self._show_rename_dialog(selected_files)

    def _batch_fix_time(self):
        """批量修复时间"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要修复的图片")
            return

        # 确认对话框
        if not messagebox.askyesno("确认", f"确定要修复 {len(selected_files)} 张图片的时间信息吗？\n（会先修复后缀，再修复时间）"):
            return

        # 先修复后缀，再修复时间
        def fix_time_with_prefix():
            # 先修复后缀
            ext_result = RepairEngine.batch_repair_extension(
                selected_files,
                self.output_dir,
                True,
                self._update_progress
            )
            # 获取修复后缀后的文件列表
            fixed_files = []
            for detail in ext_result.get('details', []):
                if detail['result'].get('success') and not detail['result'].get('skipped'):
                    fixed_files.append(detail['result']['new_path'])
                else:
                    fixed_files.append(detail['file'])

            # 再修复时间
            time_result = FileProcessor.batch_fix_time(
                fixed_files,
                self.output_dir,
                True,
                self._update_progress
            )
            return time_result

        # 执行修复
        self._execute_batch_operation(
            fix_time_with_prefix,
            "修复时间"
        )

    def _batch_fix_extension(self):
        """批量修复后缀"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要修复的图片")
            return

        # 确认对话框
        if not messagebox.askyesno("确认", f"确定要修复 {len(selected_files)} 张图片的后缀吗？"):
            return

        # 执行修复
        self._execute_batch_operation(
            lambda: RepairEngine.batch_repair_extension(
                selected_files,
                self.output_dir,
                True,
                self._update_progress
            ),
            "修复后缀"
        )

    def _full_repair(self):
        """完整修复"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要修复的图片")
            return

        # 确认对话框
        if not messagebox.askyesno("确认", f"确定要完整修复 {len(selected_files)} 张图片吗？\n（包括后缀修复和时间修复）"):
            return

        # 执行修复
        self._execute_batch_operation(
            lambda: RepairEngine.batch_full_repair(
                selected_files,
                self.output_dir,
                True,
                self._update_progress
            ),
            "完整修复"
        )

    def _repair_with_dialog(self):
        """使用对话框修复图片"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要修复的图片")
            return

        # 打开修复对话框
        from .batch_dialog import RepairDialog
        dialog = RepairDialog(self.root, selected_files, self.output_dir)
        self.root.wait_window(dialog)

        if dialog.result:
            result = dialog.result

            # 执行修复
            def do_repair():
                return RepairEngine.batch_repair(
                    selected_files,
                    rename_format=result['rename_format'],
                    output_dir=result['output_dir'],
                    fix_extension=result['fix_extension'],
                    fix_time=result['fix_time'],
                    progress_callback=self._update_progress
                )

            self._execute_batch_operation(do_repair, "修复图片")

    def _delete_backups(self):
        """删除备份文件"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        # 确定要删除的文件夹
        folder_path = self.folder_view.folder_path
        if not folder_path:
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        # 确认对话框
        if not messagebox.askyesno("确认", f"确定要删除以下文件夹中的所有备份文件吗？\n\n{folder_path}\n\n备份文件后缀为 .res"):
            return

        # 执行删除
        result = RepairEngine.delete_backups(folder_path)

        # 显示结果
        message = f"删除完成\n\n找到备份: {result['total']}\n成功删除: {result['deleted']}\n删除失败: {result['failed']}"

        if result['deleted'] > 0:
            message += "\n\n已删除文件:\n"
            for f in result['files'][:10]:
                message += f"- {os.path.basename(f)}\n"
            if len(result['files']) > 10:
                message += f"... 还有 {len(result['files']) - 10} 个文件"

        messagebox.showinfo("完成", message)

        # 刷新视图
        if self.current_mode == 'folder':
            self.folder_view.refresh()

    def _restore_from_backup(self):
        """从备份恢复"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要恢复的图片")
            return

        # 检查是否有备份
        files_with_backup = []
        files_without_backup = []

        for filepath in selected_files:
            if RepairEngine.has_backup(filepath):
                files_with_backup.append(filepath)
            else:
                files_without_backup.append(filepath)

        if not files_with_backup:
            messagebox.showinfo("提示", "选中的文件没有找到备份文件（.res后缀）")
            return

        # 确认对话框
        message = f"找到 {len(files_with_backup)} 个备份文件\n"
        if files_without_backup:
            message += f"未找到备份: {len(files_without_backup)} 个\n"
        message += f"\n确定要恢复吗？\n（将从 .res 备份文件恢复到原文件名）"

        if not messagebox.askyesno("确认", message):
            return

        # 执行恢复
        def do_restore():
            return RepairEngine.batch_restore(
                files_with_backup,
                progress_callback=self._update_progress
            )

        self._execute_batch_operation(do_restore, "恢复备份")

    def _show_rename_dialog(self, files: List[str]):
        """显示重命名对话框"""
        from .batch_dialog import RenameDialog
        dialog = RenameDialog(self.root, files, self.output_dir)
        self.root.wait_window(dialog)

        if dialog.result:
            self._execute_batch_operation(
                lambda: FileProcessor.batch_rename(
                    files,
                    dialog.result['format'],
                    dialog.result['output_dir'],
                    True,
                    self._update_progress
                ),
                "批量重命名"
            )

    def _execute_batch_operation(self, operation, operation_name: str):
        """执行批量操作"""
        from .widgets import ProgressDialog

        progress_dialog = ProgressDialog(self.root, title=f"{operation_name}中...")
        self.progress_dialog = progress_dialog

        def run():
            try:
                result = operation()
                self.root.after(0, lambda: self._on_operation_complete(result, operation_name))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"操作失败: {str(e)}"))
            finally:
                self.root.after(0, progress_dialog.destroy)

        import threading
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def _update_progress(self, current: int, total: int, filename: str = ''):
        """更新进度"""
        if hasattr(self, 'progress_dialog'):
            self.root.after(0, lambda: self.progress_dialog.update_progress(current, total, filename))

    def _on_operation_complete(self, result: dict, operation_name: str):
        """操作完成"""
        # 处理不同格式的结果
        if 'success' in result and isinstance(result['success'], int):
            # 批量操作结果
            success = result.get('success', 0)
            failed = result.get('failed', 0)
            total = result.get('total', 0)
            partial = result.get('partial', 0)

            message = f"{operation_name}完成\n\n成功: {success}\n失败: {failed}"
            if partial > 0:
                message += f"\n部分成功: {partial}"
            message += f"\n总计: {total}"

            if failed > 0 and 'errors' in result:
                message += "\n\n失败详情:\n"
                for error in result['errors'][:5]:
                    message += f"- {os.path.basename(error['file'])}: {error['message']}\n"
                if len(result['errors']) > 5:
                    message += f"... 还有 {len(result['errors']) - 5} 个错误"
        else:
            # 单个操作结果
            message = f"{operation_name}完成"

        messagebox.showinfo("完成", message)

        # 刷新视图
        if self.current_mode == 'folder':
            self.folder_view.refresh()

    def _update_status(self, text: str):
        """更新状态栏"""
        self.statusbar.configure(text=text)

    def _show_about(self):
        """显示关于"""
        messagebox.showinfo(
            "关于",
            "King_photo v1.0.0\n\n"
            "图片元信息编辑与修复工具\n\n"
            "功能特性:\n"
            "- 查看/编辑图片元信息\n"
            "- 批量重命名\n"
            "- 修复文件时间\n"
            "- 修复文件后缀\n"
            "- 支持多种图片格式"
        )

    def _show_help(self):
        """显示帮助"""
        help_text = """使用说明:

1. 打开文件夹模式:
   - 点击"打开文件夹"选择包含图片的文件夹
   - 程序会显示所有支持的图片
   - 勾选要处理的图片
   - 使用工具栏按钮进行批量操作

2. 打开单个图片:
   - 点击"打开图片"选择单张图片
   - 查看和编辑图片的详细元信息

3. 批量重命名:
   - 选择要重命名的图片
   - 点击"批量重命名"
   - 设置重命名格式和输出目录

4. 修复图片（带备份）:
   - 选择要修复的图片
   - 点击"修复图片"
   - 可选择修复后缀、修复时间
   - 可自定义重命名格式
   - 修复前会自动备份原图（.res后缀）
   - GIF等无拍摄时间的格式会使用文件修改时间

5. 恢复上一次操作:
   - 选择已修复的图片
   - 点击"恢复"
   - 将从 .res 备份文件恢复原图

6. 删除备份文件:
   - 修复完成后，确认无问题
   - 点击"删除备份"清理 .res 文件

7. 输出目录:
   - 默认保存在原目录
   - 可以设置单独的输出目录

8. 回滚机制:
   - 每次修复前会自动创建 .res 备份
   - 同一文件只保留一个备份，不重复创建
   - 可随时通过"恢复"按钮恢复原图
"""
        messagebox.showinfo("使用说明", help_text)

    def run(self):
        """运行应用"""
        self.root.mainloop()
