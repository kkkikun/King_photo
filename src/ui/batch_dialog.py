"""
King_photo - 批量操作对话框
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional

from ..utils.constants import RENAME_VARIABLES, DEFAULT_RENAME_FORMAT
from ..api import get_api


class RenameDialog(tk.Toplevel):
    """重命名对话框"""

    def __init__(self, master, files: List[str], output_dir: str = None, **kwargs):
        super().__init__(master, **kwargs)

        self.title("批量重命名")
        self.transient(master)
        self.grab_set()

        self.files = files
        self.output_dir = output_dir
        self.result = None

        # 获取屏幕尺寸，自适应窗口大小
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 窗口大小为屏幕的60%，最小600x500
        window_width = max(600, int(screen_width * 0.5))
        window_height = max(500, int(screen_height * 0.6))

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.resizable(True, True)

        self._create_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _create_ui(self):
        """创建UI"""
        # 主容器（带滚动）
        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=main_canvas.yview)
        main_frame = ttk.Frame(main_canvas)

        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=main_frame, anchor=tk.NW)
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        main_canvas.bind("<MouseWheel>", lambda e: main_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 文件数量提示
        ttk.Label(
            main_frame,
            text=f"已选择 {len(self.files)} 个文件",
            font=('Arial', 10, 'bold')
        ).pack(pady=10)

        # 重命名格式
        format_frame = ttk.LabelFrame(main_frame, text="重命名格式")
        format_frame.pack(fill=tk.X, padx=10, pady=5)

        # 格式输入
        input_frame = ttk.Frame(format_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="格式:").pack(side=tk.LEFT)

        self.format_var = tk.StringVar(value=DEFAULT_RENAME_FORMAT)
        self.format_entry = ttk.Entry(input_frame, textvariable=self.format_var)
        self.format_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 格式说明
        ttk.Label(
            format_frame,
            text="常用格式示例:\n"
                 "  {datetime}  -> 20240101_120000\n"
                 "  {date}_{seq}  -> 20240101_001\n"
                 "  {camera}_{datetime}  -> Canon_EOS_R5_20240101_120000\n"
                 "  {original}  -> 原文件名",
            justify=tk.LEFT
        ).pack(padx=5, pady=5, anchor=tk.W)

        # 变量列表
        variables_frame = ttk.LabelFrame(main_frame, text="可用变量（双击插入）")
        variables_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 变量表格
        columns = ('变量', '说明')
        self.variables_tree = ttk.Treeview(variables_frame, columns=columns, show='headings', height=12)

        self.variables_tree.heading('变量', text='变量')
        self.variables_tree.heading('说明', text='说明')

        self.variables_tree.column('变量', width=150)
        self.variables_tree.column('说明', width=400)

        for var, desc in RENAME_VARIABLES.items():
            self.variables_tree.insert('', tk.END, values=(var, desc))

        # 滚动条
        tree_scrollbar = ttk.Scrollbar(variables_frame, orient=tk.VERTICAL, command=self.variables_tree.yview)
        self.variables_tree.configure(yscrollcommand=tree_scrollbar.set)

        self.variables_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击插入变量
        self.variables_tree.bind('<Double-1>', self._insert_variable)

        # 输出目录
        output_frame = ttk.LabelFrame(main_frame, text="输出目录")
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        output_input_frame = ttk.Frame(output_frame)
        output_input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.output_var = tk.StringVar(value=self.output_dir or '')
        self.output_entry = ttk.Entry(output_input_frame, textvariable=self.output_var)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            output_input_frame,
            text="浏览",
            command=self._browse_output
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            output_frame,
            text="留空则保存到原目录",
            foreground="gray"
        ).pack(padx=5, pady=2, anchor=tk.W)

        # 预览
        preview_frame = ttk.LabelFrame(main_frame, text="预览")
        preview_frame.pack(fill=tk.X, padx=10, pady=5)

        self.preview_label = ttk.Label(
            preview_frame,
            text="",
            wraplength=500,
            font=('Arial', 10)
        )
        self.preview_label.pack(padx=10, pady=10)

        # 绑定格式变化事件
        self.format_var.trace_add('write', self._update_preview)
        self._update_preview()

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=15)

        ttk.Button(
            button_frame,
            text="确定",
            command=self._on_ok,
            width=10
        ).pack(side=tk.RIGHT, padx=10)

        ttk.Button(
            button_frame,
            text="取消",
            command=self._on_cancel,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

    def _insert_variable(self, event):
        """插入变量到格式"""
        selection = self.variables_tree.selection()
        if selection:
            var = self.variables_tree.item(selection[0])['values'][0]
            self.format_entry.insert(tk.END, var)

    def _browse_output(self):
        """浏览输出目录"""
        output_dir = filedialog.askdirectory(title="选择输出目录")
        if output_dir:
            self.output_var.set(output_dir)

    def _update_preview(self, *args):
        """更新预览"""
        format_str = self.format_var.get()
        if not format_str:
            self.preview_label.configure(text="请输入格式")
            return

        # 生成预览
        from ..utils.helpers import generate_renamed_filename
        preview_name = generate_renamed_filename(
            "IMG_1234",
            format_str,
            {'datetime': None, 'camera': 'Canon EOS R5', 'make': 'Canon'},
            1,
            '.jpg'
        )

        self.preview_label.configure(text=f"预览: {preview_name}")

    def _on_ok(self):
        """确定"""
        format_str = self.format_var.get().strip()
        if not format_str:
            messagebox.showwarning("警告", "请输入重命名格式")
            return

        self.result = {
            'format': format_str,
            'output_dir': self.output_var.get().strip() or None
        }

        self.destroy()

    def _on_cancel(self):
        """取消"""
        self.result = None
        self.destroy()


class RepairDialog(tk.Toplevel):
    """修复对话框（带重命名选项）"""

    def __init__(self, master, files: List[str], output_dir: str = None, fix_extension: bool = True, fix_time: bool = True, **kwargs):
        super().__init__(master, **kwargs)

        self.title("修复图片")
        self.transient(master)
        self.grab_set()

        self.files = files
        self.output_dir = output_dir
        self.result = None
        self.fix_extension = fix_extension
        self.fix_time = fix_time

        # 居中显示
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = max(500, int(screen_width * 0.4))
        window_height = max(400, int(screen_height * 0.5))

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.resizable(True, True)

        self._create_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _create_ui(self):
        """创建UI"""
        # 主容器（带滚动）
        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=main_canvas.yview)
        main_frame = ttk.Frame(main_canvas)

        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=main_frame, anchor=tk.NW)
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        main_canvas.bind("<MouseWheel>", lambda e: main_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 文件数量提示
        ttk.Label(
            main_frame,
            text=f"已选择 {len(self.files)} 个文件",
            font=('Arial', 10, 'bold')
        ).pack(pady=10)

        # 修复选项
        options_frame = ttk.LabelFrame(main_frame, text="修复选项")
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        # 修复后缀选项
        self.fix_extension_var = tk.BooleanVar(value=self.fix_extension)
        ttk.Checkbutton(
            options_frame,
            text="修复错误后缀",
            variable=self.fix_extension_var
        ).pack(padx=10, pady=5, anchor=tk.W)

        # 修复时间选项
        self.fix_time_var = tk.BooleanVar(value=self.fix_time)
        ttk.Checkbutton(
            options_frame,
            text="修复时间信息",
            variable=self.fix_time_var
        ).pack(padx=10, pady=5, anchor=tk.W)

        # 时间来源选择
        time_source_frame = ttk.Frame(options_frame)
        time_source_frame.pack(fill=tk.X, padx=20, pady=2)

        ttk.Label(time_source_frame, text="时间来源:").pack(side=tk.LEFT)

        self.time_source_var = tk.StringVar(value="auto")
        time_sources = [
            ("自动选择（推荐）", "auto"),
            ("使用元数据时间", "metadata"),
            ("使用文件修改时间", "modified"),
            ("使用文件创建时间", "created"),
        ]

        for text, value in time_sources:
            ttk.Radiobutton(
                time_source_frame,
                text=text,
                variable=self.time_source_var,
                value=value
            ).pack(side=tk.LEFT, padx=5)

        # 重命名格式
        rename_frame = ttk.LabelFrame(main_frame, text="重命名格式（修复后）")
        rename_frame.pack(fill=tk.X, padx=10, pady=5)

        input_frame = ttk.Frame(rename_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="格式:").pack(side=tk.LEFT)

        self.format_var = tk.StringVar(value="{datetime}")
        self.format_entry = ttk.Entry(input_frame, textvariable=self.format_var)
        self.format_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Label(
            rename_frame,
            text="默认只使用拍摄时间命名，如需原文件名可添加 {original}",
            foreground="gray"
        ).pack(padx=5, pady=2, anchor=tk.W)

        # 输出目录
        output_frame = ttk.LabelFrame(main_frame, text="输出目录")
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        output_input_frame = ttk.Frame(output_frame)
        output_input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.output_var = tk.StringVar(value=self.output_dir or '')
        self.output_entry = ttk.Entry(output_input_frame, textvariable=self.output_var)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            output_input_frame,
            text="浏览",
            command=self._browse_output
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            output_frame,
            text="留空则保存到原目录",
            foreground="gray"
        ).pack(padx=5, pady=2, anchor=tk.W)

        # 未处理文件输出目录
        unprocessed_frame = ttk.LabelFrame(main_frame, text="未处理文件输出目录")
        unprocessed_frame.pack(fill=tk.X, padx=10, pady=5)

        unprocessed_input_frame = ttk.Frame(unprocessed_frame)
        unprocessed_input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.unprocessed_var = tk.StringVar(value='')
        self.unprocessed_entry = ttk.Entry(unprocessed_input_frame, textvariable=self.unprocessed_var)
        self.unprocessed_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            unprocessed_input_frame,
            text="浏览",
            command=self._browse_unprocessed
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            unprocessed_frame,
            text="非图片文件（如视频）将被复制到此目录，方便管理",
            foreground="gray"
        ).pack(padx=5, pady=2, anchor=tk.W)

        # 操作提醒
        reminder_frame = ttk.LabelFrame(main_frame, text="操作提醒")
        reminder_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(
            reminder_frame,
            text="修复操作会修改文件，请在操作前备份重要数据\n"
                 "修复后的文件会保留原始文件的时间属性",
            justify=tk.LEFT
        ).pack(padx=10, pady=10, anchor=tk.W)

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=15)

        ttk.Button(
            button_frame,
            text="开始修复",
            command=self._on_ok,
            width=10
        ).pack(side=tk.RIGHT, padx=10)

        ttk.Button(
            button_frame,
            text="取消",
            command=self._on_cancel,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

    def _browse_output(self):
        """浏览输出目录"""
        output_dir = filedialog.askdirectory(title="选择输出目录")
        if output_dir:
            self.output_var.set(output_dir)

    def _browse_unprocessed(self):
        """浏览未处理文件输出目录"""
        unprocessed_dir = filedialog.askdirectory(title="选择未处理文件输出目录")
        if unprocessed_dir:
            self.unprocessed_var.set(unprocessed_dir)

    def _on_ok(self):
        """确定"""
        self.result = {
            'fix_extension': self.fix_extension_var.get(),
            'fix_time': self.fix_time_var.get(),
            'rename_format': self.format_var.get().strip() or '{datetime}',
            'output_dir': self.output_var.get().strip() or None,
            'time_source': self.time_source_var.get(),
            'unprocessed_dir': self.unprocessed_var.get().strip() or None
        }
        self.destroy()

    def _on_cancel(self):
        """取消"""
        self.result = None
        self.destroy()


class BatchMetadataDialog(tk.Toplevel):
    """批量元信息编辑对话框"""

    def __init__(self, master, files: List[str], **kwargs):
        super().__init__(master, **kwargs)

        self.title("批量编辑元信息")
        self.transient(master)
        self.grab_set()

        self.files = files
        self.result = None
        
        # 初始化统一API
        self.api = get_api()

        # 居中显示
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = max(500, int(screen_width * 0.4))
        window_height = max(400, int(screen_height * 0.5))

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.resizable(True, True)

        self._create_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _create_ui(self):
        """创建UI"""
        # 主容器（带滚动）
        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=main_canvas.yview)
        main_frame = ttk.Frame(main_canvas)

        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=main_frame, anchor=tk.NW)
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        main_canvas.bind("<MouseWheel>", lambda e: main_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 文件数量提示
        ttk.Label(
            main_frame,
            text=f"已选择 {len(self.files)} 个文件",
            font=('Arial', 10, 'bold')
        ).pack(pady=10)

        # 根据第一个文件获取可编辑字段（用于确定字段可编辑性）
        self.entries = {}
        self.entry_widgets = {}
        
        if self.files:
            # 获取第一个文件的格式信息
            first_file = self.files[0]
            editable_fields = self.api.get_editable_fields(first_file)
            format_info = editable_fields.get('_format_info', {})
            
            # 显示格式信息
            info_frame = ttk.LabelFrame(main_frame, text="格式信息")
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            format_name = format_info.get('format', 'Unknown')
            supports = []
            if format_info.get('supports_exif', False):
                supports.append("EXIF")
            if format_info.get('supports_xmp', False):
                supports.append("XMP")
            if format_info.get('needs_exiftool', False):
                supports.append("需要ExifTool")
            
            support_text = f"格式: {format_name} | 支持: {', '.join(supports) if supports else '不支持元数据编辑'}"
            ttk.Label(
                info_frame,
                text=support_text,
                foreground="gray"
            ).pack(padx=5, pady=5, anchor=tk.W)
            
            # 按类别分组显示字段
            # 时间字段
            time_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'time'}
            if time_fields:
                self._add_field_group(main_frame, "时间信息", time_fields)
            
            # XMP字段
            xmp_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'xmp'}
            if xmp_fields:
                self._add_field_group(main_frame, "XMP信息", xmp_fields)
            
            # EXIF字段
            exif_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'exif'}
            if exif_fields:
                self._add_field_group(main_frame, "EXIF信息", exif_fields)

        # 说明
        ttk.Label(
            main_frame,
            text="留空的字段将不会被修改\n灰色字段当前格式不支持编辑",
            foreground="gray"
        ).pack(padx=10, pady=5, anchor=tk.W)

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="确定",
            command=self._on_ok,
            width=10
        ).pack(side=tk.RIGHT, padx=10)

        ttk.Button(
            button_frame,
            text="取消",
            command=self._on_cancel,
            width=10
        ).pack(side=tk.RIGHT, padx=5)
    
    def _add_field_group(self, parent, group_name: str, fields: dict):
        """添加字段组"""
        group_frame = ttk.LabelFrame(parent, text=group_name)
        group_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for field_name, field_info in fields.items():
            label = field_info.get('label', field_name)
            editable = field_info.get('editable', False)
            
            frame = ttk.Frame(group_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # 根据可编辑状态设置颜色
            if editable:
                label_fg = '#000000'  # 黑色
                entry_state = 'normal'
            else:
                label_fg = '#888888'  # 灰色
                entry_state = 'disabled'
            
            ttk.Label(frame, text=f"{label}:", width=10, foreground=label_fg).pack(side=tk.LEFT)
            
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, state=entry_state)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            self.entries[field_name] = var
            self.entry_widgets[field_name] = entry

    def _on_ok(self):
        """确定"""
        metadata = {}
        for field, var in self.entries.items():
            # 跳过内部字段
            if field.startswith('_'):
                continue
            
            # 检查entry是否可用（可编辑）
            entry = self.entry_widgets.get(field)
            if entry and str(entry['state']) == 'disabled':
                continue
            
            value = var.get().strip()
            if value:
                metadata[field] = value

        if not metadata:
            messagebox.showwarning("警告", "请至少填写一个可编辑字段")
            return

        self.result = metadata
        self.destroy()

    def _on_cancel(self):
        """取消"""
        self.result = None
        self.destroy()
