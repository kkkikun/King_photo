"""
King_photo - 主应用窗口
"""

import logging
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List

# ttkbootstrap 主题框架（tkinter/ttk 超集）
import ttkbootstrap as ttk

from .folder_view import FolderView
from .single_view import SingleView
from ..api import get_api
from ..utils.helpers import get_image_files_in_folder, set_file_times, ensure_output_folder, get_unique_filename
from ..utils.config_manager import get_config_manager

# 获取日志记录器
logger = logging.getLogger(__name__)

# ============================================================
# ToolTip 工具提示组件
# ============================================================
class ToolTip:
    """鼠标悬停显示帮助文本的工具提示"""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self._after_id = None
        widget.bind('<Enter>', self._schedule_show)
        widget.bind('<Leave>', self._hide)
        widget.bind('<Button-1>', self._hide)

    def _schedule_show(self, event=None):
        self._after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Microsoft YaHei", 9), padx=6, pady=3)
        label.pack()

    def _hide(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class MainWindow:
    """主窗口"""

    def __init__(self, root=None):
        # 加载配置
        self.config = get_config_manager()

        # 初始化统一API
        self.api = get_api()

        # 使用传入的 root 或创建新的 ttkbootstrap Window
        if root is not None:
            self.root = root
        else:
            theme = self.config.get('ui.theme', 'darkly')
            self.root = ttk.Window(
                title="King_photo - 图片元信息编辑与修复工具",
                themename=theme
            )

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

        # 绑定全局快捷键
        self._bind_shortcuts()

        # 初始化视图
        self.folder_view = FolderView(self.main_frame, self)
        self.single_view = SingleView(self.main_frame, self)

        # 默认显示文件夹模式
        self._show_folder_mode()

        # 自动打开上次的文件夹
        last_folder = self.config.get('paths.last_folder', '')
        if last_folder and os.path.isdir(last_folder):
            self.root.after(100, lambda: self._open_folder_path(last_folder))

    # ============================================================
    # 快捷键绑定
    # ============================================================
    def _bind_shortcuts(self):
        """绑定全局快捷键"""
        self.root.bind('<Control-o>', lambda e: self._open_folder())
        self.root.bind('<Control-Shift-O>', lambda e: self._open_single_image())
        self.root.bind('<Control-d>', lambda e: self._set_output_dir())
        self.root.bind('<Control-a>', lambda e: self._select_all())
        self.root.bind('<Control-Shift-A>', lambda e: self._deselect_all())
        self.root.bind('<Control-i>', lambda e: self._invert_selection())
        self.root.bind('<Control-r>', lambda e: self._repair_with_dialog())
        self.root.bind('<Control-b>', lambda e: self._batch_rename())
        self.root.bind('<Control-e>', lambda e: self._batch_edit_metadata())
        self.root.bind('<Control-1>', lambda e: self._show_folder_mode())
        self.root.bind('<Control-2>', lambda e: self._show_single_mode())
        self.root.bind('<F5>', lambda e: self._refresh())
        self.root.bind('<F1>', lambda e: self._show_help())
        self.root.bind('<Escape>', lambda e: self._on_escape())

    def _refresh(self):
        """刷新（F5）"""
        if self.current_mode == 'folder':
            self.folder_view.refresh()
            self._update_status("已刷新")

    def _on_escape(self):
        """ESC 键处理"""
        if self.current_mode == 'folder':
            self.folder_view.deselect_all()

    # ============================================================
    # 菜单栏
    # ============================================================
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开文件夹\tCtrl+O", command=self._open_folder)
        file_menu.add_command(label="打开图片\tCtrl+Shift+O", command=self._open_single_image)
        file_menu.add_separator()
        file_menu.add_command(label="设置输出目录\tCtrl+D", command=self._set_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="全选\tCtrl+A", command=self._select_all)
        edit_menu.add_command(label="反选\tCtrl+I", command=self._invert_selection)
        edit_menu.add_command(label="取消选择\tCtrl+Shift+A", command=self._deselect_all)

        # 查看菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="查看", menu=view_menu)
        view_menu.add_command(label="文件夹模式\tCtrl+1", command=self._show_folder_mode)
        view_menu.add_command(label="单图片模式\tCtrl+2", command=self._show_single_mode)
        view_menu.add_separator()
        view_menu.add_command(label="刷新\tF5", command=self._refresh)

        # 主题子菜单
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="主题", menu=theme_menu)
        themes = ['darkly', 'flatly', 'cosmo', 'litera', 'minty', 'lumen',
                  'sandstone', 'yeti', 'pulse', 'united', 'morph', 'journal',
                  'solar', 'superhero', 'cyborg', 'vapor']
        current_theme = self.config.get('ui.theme', 'darkly')
        self._theme_var = tk.StringVar(value=current_theme)
        for theme in themes:
            theme_menu.add_radiobutton(
                label=theme, value=theme,
                variable=self._theme_var,
                command=lambda t=theme: self._switch_theme(t)
            )

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="批量重命名\tCtrl+B", command=self._batch_rename)
        tools_menu.add_command(label="批量编辑元信息\tCtrl+E", command=self._batch_edit_metadata)

        # 修复子菜单
        repair_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="修复操作", menu=repair_menu)
        repair_menu.add_command(label="完整修复\tCtrl+R", command=self._repair_with_dialog)
        repair_menu.add_separator()
        repair_menu.add_command(label="仅修复后缀", command=lambda: self._repair_with_dialog(fix_extension=True, fix_time=False))
        repair_menu.add_command(label="仅修复时间", command=lambda: self._repair_with_dialog(fix_extension=False, fix_time=True))

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明\tF1", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)

    def _switch_theme(self, theme: str):
        """切换主题"""
        try:
            self.root.style.theme_use(theme)
            self.config.set('ui.theme', theme)
            self.config.save()
            self._update_status(f"主题已切换: {theme}")
        except Exception as e:
            logger.error(f"切换主题失败: {e}")
            messagebox.showerror("错误", f"切换主题失败: {e}")

    # ============================================================
    # 工具栏
    # ============================================================
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        # 打开文件夹按钮
        btn_open = ttk.Button(toolbar, text="📂 打开文件夹", command=self._open_folder)
        btn_open.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_open, "打开文件夹 (Ctrl+O)\n加载文件夹中所有支持的图片")

        # 打开图片按钮
        btn_image = ttk.Button(toolbar, text="🖼️ 打开图片", command=self._open_single_image)
        btn_image.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_image, "打开单张图片 (Ctrl+Shift+O)\n进入单图片预览编辑模式")

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 设置输出目录
        btn_out = ttk.Button(toolbar, text="📁 输出目录", command=self._set_output_dir)
        btn_out.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_out, "设置输出目录 (Ctrl+D)\n修改后的文件将保存到此目录")

        # 输出目录显示
        self.output_dir_label = ttk.Label(toolbar, text="输出: 未设置")
        self.output_dir_label.pack(side=tk.LEFT, padx=5)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 批量重命名按钮
        btn_rename = ttk.Button(toolbar, text="✏️ 批量重命名", command=self._batch_rename)
        btn_rename.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_rename, "批量重命名 (Ctrl+B)\n按模板批量重命名选中图片")

        # 编辑元信息按钮
        btn_meta = ttk.Button(toolbar, text="📝 编辑元信息", command=self._batch_edit_metadata)
        btn_meta.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_meta, "批量编辑元信息 (Ctrl+E)\n批量修改选中图片的元数据")

        # 修复操作按钮组
        repair_menu_btn = ttk.Menubutton(toolbar, text="🔧 修复操作")
        repair_menu_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(repair_menu_btn, "修复图片 (Ctrl+R)\n修复文件后缀和时间信息")

        repair_menu = tk.Menu(repair_menu_btn, tearoff=0)
        repair_menu.add_command(label="完整修复\tCtrl+R", command=self._repair_with_dialog)
        repair_menu.add_separator()
        repair_menu.add_command(label="仅修复后缀", command=lambda: self._repair_with_dialog(fix_extension=True, fix_time=False))
        repair_menu.add_command(label="仅修复时间", command=lambda: self._repair_with_dialog(fix_extension=False, fix_time=True))
        repair_menu.add_command(label="仅重命名\tCtrl+B", command=self._batch_rename)
        repair_menu_btn.config(menu=repair_menu)

    # ============================================================
    # 主内容和状态栏
    # ============================================================
    def _create_main_content(self):
        """创建主内容区域"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_statusbar(self):
        """创建增强状态栏"""
        self.status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(5, 2))
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 模式
        self.status_mode = ttk.Label(self.status_frame, text="📁 文件夹模式", width=18)
        self.status_mode.pack(side=tk.LEFT, padx=(0, 10))

        # 分隔符
        ttk.Separator(self.status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 主状态文本
        self.statusbar = ttk.Label(self.status_frame, text="就绪", anchor=tk.W)
        self.statusbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 进度条（默认隐藏）
        self.status_progress = ttk.Progressbar(self.status_frame, mode='indeterminate', length=100)
        # 初始不显示

    def _show_folder_mode(self):
        """显示文件夹模式"""
        self.single_view.hide()
        self.folder_view.show()
        self.current_mode = 'folder'
        self.status_mode.config(text="📁 文件夹模式")

    def _show_single_mode(self):
        """显示单图片模式"""
        self.folder_view.hide()
        self.single_view.show()
        self.current_mode = 'single'
        self.status_mode.config(text="🖼️ 单图片模式")

    # ============================================================
    # 文件操作
    # ============================================================
    def _on_close(self):
        """关闭窗口"""
        geometry = self.root.geometry()
        try:
            size_part = geometry.split('+')[0]
            width, height = size_part.split('x')
            self.config.set('window.width', int(width))
            self.config.set('window.height', int(height))
        except Exception:
            pass

        self.config.save()
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

        filepath = filedialog.askopenfilename(title="选择图片", filetypes=filetypes)

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
            self.config.set('paths.output_dir', output_dir)
            self.config.save()

    # ============================================================
    # 选择操作
    # ============================================================
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

    # ============================================================
    # 批量操作入口
    # ============================================================
    def _batch_rename(self):
        """批量重命名"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要重命名的图片")
            return

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

        from .batch_dialog import BatchMetadataDialog
        dialog = BatchMetadataDialog(self.root, selected_files)
        self.root.wait_window(dialog)

        if dialog.result:
            metadata = dialog.result

            field_names = {
                'title': '标题', 'description': '描述', 'artist': '作者',
                'copyright': '版权', 'make': '相机品牌', 'model': '相机型号',
            }

            fields_text = "\n".join([f"- {field_names.get(k, k)}: {v}" for k, v in metadata.items()])
            if not messagebox.askyesno("确认", f"确定要修改 {len(selected_files)} 张图片的元信息吗？\n\n{fields_text}"):
                return

            def do_write():
                return self.api.batch_write_metadata(
                    selected_files, metadata,
                    copy_mode=True, output_dir=self.output_dir,
                    progress_callback=self._update_progress
                )

            self._execute_batch_operation(do_write, "批量编辑元信息")

    def _repair_with_dialog(self, fix_extension: bool = True, fix_time: bool = True):
        """Use dialog to repair images - format check happens AFTER user confirms repair settings"""
        if self.current_mode != 'folder':
            messagebox.showinfo("提示", "请先打开文件夹")
            return

        selected_files = self.folder_view.get_selected_files()
        if not selected_files:
            messagebox.showinfo("提示", "请先选择要修复的图片")
            return

        # ---- Phase 1: Show original RepairDialog for all settings ----
        from .batch_dialog import RepairDialog
        repair_dialog = RepairDialog(self.root, selected_files, self.output_dir,
                                     fix_extension=fix_extension, fix_time=fix_time)
        self.root.wait_window(repair_dialog)

        if not repair_dialog.result:
            return

        result = repair_dialog.result

        # ---- Phase 2: If fixing extensions, check for format mismatches ----
        from .format_mismatch_dialog import FormatMismatchDialog, collect_mismatched_files
        from ..utils.helpers import ensure_output_folder, get_unique_filename, set_file_times
        from datetime import datetime
        import shutil

        fix_files = list(selected_files)
        skip_files = []
        unprocessed_dir = None

        if result['fix_extension']:
            mismatched = collect_mismatched_files(selected_files)
            if mismatched:
                dialog = FormatMismatchDialog(self.root, mismatched, result['output_dir'])
                self.root.wait_window(dialog)

                if dialog.result:
                    decisions = dialog.result.get('decisions', {})
                    fix_files = []
                    skip_files = []

                    for fp in selected_files:
                        decision = decisions.get(fp, 'fix')
                        if decision == 'fix':
                            fix_files.append(fp)
                        else:
                            skip_files.append(fp)

                    if skip_files:
                        unprocessed_dir = result['output_dir'] or os.path.dirname(skip_files[0])
                        unprocessed_dir = os.path.join(unprocessed_dir, '未处理文件')
                        ensure_output_folder(unprocessed_dir)

        # ---- Phase 3: Execute repair + skip processing ----
        def do_process():
            all_results = []

            if fix_files and result:
                repair_result = self.api.batch_repair(
                    fix_files,
                    output_dir=result['output_dir'],
                    fix_extension=result['fix_extension'],
                    fix_time=result['fix_time'],
                    time_source=result.get('time_source', 'auto'),
                    rename_format=result['rename_format'],
                    progress_callback=self._update_progress
                )
                all_results.append(('repair', repair_result))

            if skip_files:
                skip_result = {'success': 0, 'failed': 0, 'total': len(skip_files), 'unprocessed': len(skip_files)}
                for fp in skip_files:
                    try:
                        dest = get_unique_filename(os.path.join(unprocessed_dir, os.path.basename(fp)))
                        shutil.copy2(fp, dest)
                        stat = os.stat(fp)
                        dt = datetime.fromtimestamp(stat.st_mtime)
                        set_file_times(dest, dt, set_created=True)
                        skip_result['success'] += 1
                    except Exception as e:
                        logger.warning(f"Skip file copy failed: {fp}, {e}")
                        skip_result['failed'] += 1
                all_results.append(('skip', skip_result))

            return all_results

        self._execute_batch_operation_with_split(do_process, "修复图片")

    def _execute_batch_operation_with_split(self, operation, operation_name: str):
        """Execute batch operation with split repair/skip results"""
        from .widgets import ProgressDialog

        progress_dialog = ProgressDialog(self.root, title=f"{operation_name}中...")
        self.progress_dialog = progress_dialog
        self.status_progress.pack(side=tk.RIGHT, padx=5)
        self.status_progress.start()

        cancel_flag = threading.Event()
        progress_dialog.set_cancel_callback(lambda: cancel_flag.set())

        def run():
            try:
                results = operation()
                if cancel_flag.is_set():
                    self.root.after(0, lambda: messagebox.showinfo("提示", f"{operation_name}已取消"))
                else:
                    self.root.after(0, lambda: self._on_split_operation_complete(results, operation_name))
            except Exception as e:
                if not cancel_flag.is_set():
                    self.root.after(0, lambda: messagebox.showerror("错误", f"操作失败: {str(e)}"))
            finally:
                self.root.after(0, self._on_operation_finish)

        threading.Thread(target=run, daemon=True).start()

    def _on_split_operation_complete(self, results: list, operation_name: str):
        """Handle split operation completion"""
        from ..utils.error_report import generate_error_report_from_batch_result, show_error_report_dialog

        messages = []
        for op_type, result in results:
            if op_type == 'repair':
                success = result.get('success', 0)
                failed = result.get('failed', 0)
                total = result.get('total', 0)
                unprocessed = result.get('unprocessed', 0)
                msg = f"修复完成: 成功 {success}, 失败 {failed}"
                if unprocessed > 0:
                    msg += f", 未处理(视频等) {unprocessed}"
                msg += f", 共 {total}"
                messages.append(msg)

                report = generate_error_report_from_batch_result(result, operation_name)
                if report.has_errors() or report.has_warnings():
                    show_error_report_dialog(self.root, report)

            elif op_type == 'skip':
                success = result.get('success', 0)
                failed = result.get('failed', 0)
                total = result.get('total', 0)
                messages.append(f"跳过修复: {success} 个文件已复制到未处理目录")

        messagebox.showinfo("完成", "\n".join(messages))

        if self.current_mode == 'folder':
            self.folder_view.refresh()

    def _show_rename_dialog(self, files: List[str]):
        """显示重命名对话框"""
        from .batch_dialog import RenameDialog
        dialog = RenameDialog(self.root, files, self.output_dir)
        self.root.wait_window(dialog)

        if dialog.result:
            self._execute_batch_operation(
                lambda: self.api.rename_files(
                    files, dialog.result['format'], dialog.result['output_dir']
                ),
                "批量重命名"
            )

    # ============================================================
    # 批量操作执行
    # ============================================================
    def _execute_batch_operation(self, operation, operation_name: str):
        """执行批量操作"""
        from .widgets import ProgressDialog

        progress_dialog = ProgressDialog(self.root, title=f"{operation_name}中...")
        self.progress_dialog = progress_dialog
        # 显示进度条
        self.status_progress.pack(side=tk.RIGHT, padx=5)
        self.status_progress.start()

        cancel_flag = threading.Event()

        def cancel_callback():
            cancel_flag.set()

        progress_dialog.set_cancel_callback(cancel_callback)

        def run():
            try:
                result = operation()
                if cancel_flag.is_set():
                    self.root.after(0, lambda: messagebox.showinfo("提示", f"{operation_name}已取消"))
                else:
                    self.root.after(0, lambda: self._on_operation_complete(result, operation_name))
            except Exception as e:
                if not cancel_flag.is_set():
                    self.root.after(0, lambda: messagebox.showerror("错误", f"操作失败: {str(e)}"))
            finally:
                self.root.after(0, self._on_operation_finish)

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def _on_operation_finish(self):
        """操作结束后清理"""
        self.status_progress.stop()
        self.status_progress.pack_forget()
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            try:
                self.progress_dialog.destroy()
            except Exception:
                pass

    def _update_progress(self, current: int, total: int, filename: str = ''):
        """更新进度"""
        if hasattr(self, 'progress_dialog'):
            self.root.after(0, lambda: self.progress_dialog.update_progress(current, total, filename))

    def _on_operation_complete(self, result: dict, operation_name: str):
        """操作完成"""
        from ..utils.error_report import generate_error_report_from_batch_result, show_error_report_dialog

        if 'success' in result and isinstance(result['success'], int):
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

            report = generate_error_report_from_batch_result(result, operation_name)
            if report.has_errors() or report.has_warnings():
                messagebox.showinfo("完成", message)
                show_error_report_dialog(self.root, report)
            else:
                messagebox.showinfo("完成", message)
        else:
            messagebox.showinfo("完成", f"{operation_name}完成")

        if self.current_mode == 'folder':
            self.folder_view.refresh()

    # ============================================================
    # 状态与帮助
    # ============================================================
    def _update_status(self, text: str):
        """更新状态栏"""
        self.statusbar.configure(text=text)

    def _show_about(self):
        """显示关于"""
        messagebox.showinfo(
            "关于",
            "King_photo v1.3.1\n\n"
            "图片元信息编辑与修复工具\n\n"
            "功能特性:\n"
            "- 查看/编辑图片元信息（EXIF/XMP）\n"
            "- 批量重命名（20+变量）\n"
            "- 修复文件时间\n"
            "- 修复文件后缀\n"
            "- 支持多种图片格式\n"
            "- 插件系统 + 统一API"
        )

    def _show_help(self):
        """显示帮助"""
        help_text = """使用说明:

快捷键:
  Ctrl+O       打开文件夹
  Ctrl+Shift+O 打开单张图片
  Ctrl+D       设置输出目录
  Ctrl+A       全选
  Ctrl+Shift+A 取消选择
  Ctrl+I       反选
  Ctrl+R       完整修复
  Ctrl+B       批量重命名
  Ctrl+E       批量编辑元信息
  Ctrl+1       文件夹模式
  Ctrl+2       单图片模式
  F5           刷新
  F1           帮助
  ESC          取消选择

1. 打开文件夹模式:
   - 点击"打开文件夹"或 Ctrl+O
   - 程序会显示所有支持的图片缩略图
   - 点击缩略图可预览，再次点击可切换选中状态
   - 使用工具栏按钮进行批量操作

2. 打开单个图片:
   - 点击"打开图片"或 Ctrl+Shift+O
   - 查看和编辑图片的详细元信息

3. 批量重命名 (Ctrl+B):
   - 选择要重命名的图片
   - 设置重命名格式（支持 {datetime} {original} 等变量）

4. 修复图片 (Ctrl+R):
   - 选择要修复的图片
   - 可选择修复后缀、修复时间
   - 可自定义重命名格式和时间来源

5. 主题切换:
   - 菜单「查看 → 主题」可切换暗色/亮色主题
"""
        messagebox.showinfo("使用说明", help_text)

    def run(self):
        """运行应用"""
        self.root.mainloop()
