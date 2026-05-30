"""
King_photo - 主应用窗口
"""

import logging
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List

from .folder_view import FolderView
from .single_view import SingleView
from ..api import get_api
from ..utils.helpers import get_image_files_in_folder
from ..utils.config_manager import get_config_manager

# 获取日志记录器
logger = logging.getLogger(__name__)


class MainWindow:
    """主窗口"""

    def __init__(self):
        # 加载配置
        self.config = get_config_manager()
        
        # 初始化统一API
        self.api = get_api()

        self.root = tk.Tk()
        self.root.title("King_photo - 图片元信息编辑与修复工具")

        # 从配置加载窗口大小
        width = self.config.get('window.width', 1200)
        height = self.config.get('window.height', 800)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(800, 600)

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 当前模式
        self.current_mode = None  # 'folder' or 'single'
        self.current_files = []
        self.output_dir = self.config.get('paths.output_dir', '') or None

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

        # 自动打开上次的文件夹
        last_folder = self.config.get('paths.last_folder', '')
        if last_folder and os.path.isdir(last_folder):
            self.root.after(100, lambda: self._open_folder_path(last_folder))

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
        tools_menu.add_command(label="批量编辑元信息", command=self._batch_edit_metadata)
        
        # 修复子菜单
        repair_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="修复操作", menu=repair_menu)
        repair_menu.add_command(label="完整修复", command=self._repair_with_dialog)
        repair_menu.add_separator()
        repair_menu.add_command(label="仅修复后缀", command=lambda: self._repair_with_dialog(fix_extension=True, fix_time=False))
        repair_menu.add_command(label="仅修复时间", command=lambda: self._repair_with_dialog(fix_extension=False, fix_time=True))

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
            text="编辑元信息",
            command=self._batch_edit_metadata
        ).pack(side=tk.LEFT, padx=2)

        # 修复操作按钮组
        repair_menu_btn = ttk.Menubutton(toolbar, text="修复操作")
        repair_menu_btn.pack(side=tk.LEFT, padx=2)
        
        repair_menu = tk.Menu(repair_menu_btn, tearoff=0)
        repair_menu.add_command(label="完整修复", command=self._repair_with_dialog)
        repair_menu.add_separator()
        repair_menu.add_command(label="仅修复后缀", command=lambda: self._repair_with_dialog(fix_extension=True, fix_time=False))
        repair_menu.add_command(label="仅修复时间", command=lambda: self._repair_with_dialog(fix_extension=False, fix_time=True))
        repair_menu.add_command(label="仅重命名", command=self._batch_rename)
        repair_menu_btn.config(menu=repair_menu)

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

    def _on_close(self):
        """关闭窗口"""
        # 保存窗口大小
        geometry = self.root.geometry()
        try:
            # 解析窗口大小（格式：WIDTHxHEIGHT+X+Y）
            size_part = geometry.split('+')[0]
            width, height = size_part.split('x')
            self.config.set('window.width', int(width))
            self.config.set('window.height', int(height))
        except Exception:
            pass

        # 保存配置
        self.config.save()

        # 关闭窗口
        self.root.destroy()

    def _open_folder(self):
        """打开文件夹"""
        folder_path = filedialog.askdirectory(title="选择图片文件夹")
        if folder_path:
            self._open_folder_path(folder_path)

    def _open_folder_path(self, folder_path: str):
        """打开指定文件夹"""
        self.current_files = get_image_files_in_folder(folder_path)

        if not self.current_files:
            messagebox.showinfo("提示", "该文件夹中没有找到支持的图片文件")
            return

        # 保存最后打开的文件夹
        self.config.set('paths.last_folder', folder_path)
        self.config.save()

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

            # 保存输出目录配置
            self.config.set('paths.output_dir', output_dir)
            self.config.save()

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

    def _batch_edit_metadata(self):
        """批量编辑元信息"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要编辑的图片")
            return

        # 打开批量编辑对话框
        from .batch_dialog import BatchMetadataDialog
        dialog = BatchMetadataDialog(self.root, selected_files)
        self.root.wait_window(dialog)

        if dialog.result:
            metadata = dialog.result

            # 确认对话框
            field_names = {
                'title': '标题',
                'description': '描述',
                'artist': '作者',
                'copyright': '版权',
                'make': '相机品牌',
                'model': '相机型号',
            }

            fields_text = "\n".join([f"- {field_names.get(k, k)}: {v}" for k, v in metadata.items()])
            if not messagebox.askyesno("确认", f"确定要修改 {len(selected_files)} 张图片的元信息吗？\n\n{fields_text}"):
                return

            # 执行批量写入
            def do_write():
                return self.api.batch_write_metadata(
                    selected_files,
                    metadata,
                    copy_mode=True,
                    output_dir=self.output_dir,
                    progress_callback=self._update_progress
                )

            self._execute_batch_operation(do_write, "批量编辑元信息")

    def _repair_with_dialog(self, fix_extension: bool = True, fix_time: bool = True):
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
        dialog = RepairDialog(self.root, selected_files, self.output_dir, fix_extension=fix_extension, fix_time=fix_time)
        self.root.wait_window(dialog)

        if dialog.result:
            result = dialog.result

            # 执行修复
            def do_repair():
                return self.api.batch_repair(
                    selected_files,
                    output_dir=result['output_dir'],
                    fix_extension=result['fix_extension'],
                    fix_time=result['fix_time'],
                    time_source=result.get('time_source', 'auto'),
                    rename_format=result['rename_format'],
                    progress_callback=self._update_progress
                )

            self._execute_batch_operation(do_repair, "修复图片")



    def _show_rename_dialog(self, files: List[str]):
        """显示重命名对话框"""
        from .batch_dialog import RenameDialog
        dialog = RenameDialog(self.root, files, self.output_dir)
        self.root.wait_window(dialog)

        if dialog.result:
            self._execute_batch_operation(
                lambda: self.api.rename_files(
                    files,
                    dialog.result['format'],
                    dialog.result['output_dir']
                ),
                "批量重命名"
            )

    def _execute_batch_operation(self, operation, operation_name: str):
        """执行批量操作"""
        from .widgets import ProgressDialog

        progress_dialog = ProgressDialog(self.root, title=f"{operation_name}中...")
        self.progress_dialog = progress_dialog

        # 用于存储取消标志
        cancel_flag = threading.Event()

        def cancel_callback():
            """取消回调"""
            cancel_flag.set()

        progress_dialog.set_cancel_callback(cancel_callback)

        def run():
            try:
                result = operation()

                # 检查是否被取消
                if cancel_flag.is_set():
                    self.root.after(0, lambda: messagebox.showinfo("提示", f"{operation_name}已取消"))
                else:
                    self.root.after(0, lambda: self._on_operation_complete(result, operation_name))
            except Exception as e:
                if not cancel_flag.is_set():
                    self.root.after(0, lambda: messagebox.showerror("错误", f"操作失败: {str(e)}"))
            finally:
                self.root.after(0, progress_dialog.destroy)

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def _update_progress(self, current: int, total: int, filename: str = ''):
        """更新进度"""
        if hasattr(self, 'progress_dialog'):
            self.root.after(0, lambda: self.progress_dialog.update_progress(current, total, filename))

    def _on_operation_complete(self, result: dict, operation_name: str):
        """操作完成"""
        from ..utils.error_report import generate_error_report_from_batch_result, show_error_report_dialog

        # 处理不同格式的结果
        if 'success' in result and isinstance(result['success'], int):
            # 批量操作结果
            success = result.get('success', 0)
            failed = result.get('failed', 0)
            total = result.get('total', 0)
            partial = result.get('partial', 0)
            unprocessed = result.get('unprocessed', 0)

            message = f"{operation_name}完成\n\n成功: {success}\n失败: {failed}"
            if partial > 0:
                message += f"\n部分成功: {partial}"
            if unprocessed > 0:
                message += f"\n未处理: {unprocessed} (非图片文件，已复制到未处理目录)"
            message += f"\n总计: {total}"

            # 生成错误报告
            report = generate_error_report_from_batch_result(result, operation_name)

            if report.has_errors() or report.has_warnings():
                # 显示简要信息
                messagebox.showinfo("完成", message)

                # 显示详细错误报告
                show_error_report_dialog(self.root, report)
            else:
                messagebox.showinfo("完成", message)
        else:
            # 单个操作结果
            messagebox.showinfo("完成", f"{operation_name}完成")

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

4. 修复图片:
   - 选择要修复的图片
   - 点击"修复图片"
   - 可选择修复后缀、修复时间
   - 可自定义重命名格式
   - 可选择时间来源（自动、元数据、修改时间、创建时间）
   - GIF等无拍摄时间的格式会使用文件修改时间

5. 输出目录:
   - 默认保存在原目录
   - 可以设置单独的输出目录

6. 操作提醒:
   - 修复操作会修改文件，请在操作前备份重要数据
   - 修复后的文件会保留原始文件的时间属性
"""
        messagebox.showinfo("使用说明", help_text)

    def run(self):
        """运行应用"""
        self.root.mainloop()
