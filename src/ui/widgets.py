"""
King_photo - 自定义UI组件
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Any
from PIL import Image, ImageTk
import os


class ThumbnailWidget(tk.Frame):
    """缩略图组件"""

    def __init__(self, master, filepath: str, size: tuple = (100, 100),
                 on_click: Callable = None, on_select: Callable = None, **kwargs):
        super().__init__(master, **kwargs)

        self.filepath = filepath
        self.size = size
        self.on_click = on_click
        self.on_select = on_select
        self.selected = False

        # 勾选框
        self.var_selected = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(
            self,
            variable=self.var_selected,
            command=self._on_checkbox_change
        )
        self.checkbox.pack(side=tk.TOP, anchor=tk.W)

        # 图片预览
        self.image_label = tk.Label(self, cursor="hand2")
        self.image_label.pack(side=tk.TOP, padx=2, pady=2)
        self.image_label.bind("<Button-1>", self._on_image_click)

        # 文件名
        filename = os.path.basename(filepath)
        display_name = filename if len(filename) <= 15 else filename[:12] + '...'
        self.name_label = tk.Label(
            self,
            text=display_name,
            wraplength=size[0],
            font=('Arial', 8)
        )
        self.name_label.pack(side=tk.TOP)

        # 加载缩略图
        self._load_thumbnail()

    def _load_thumbnail(self):
        """加载缩略图"""
        try:
            with Image.open(self.filepath) as img:
                img.thumbnail(self.size)
                self.photo = ImageTk.PhotoImage(img)
                self.image_label.configure(image=self.photo)
        except Exception:
            # 显示占位图
            self.image_label.configure(
                text='无法预览',
                width=self.size[0] // 8,
                height=self.size[1] // 16
            )

    def _on_image_click(self, event):
        """点击图片"""
        if self.on_click:
            self.on_click(self.filepath)

    def _on_checkbox_change(self):
        """勾选状态改变"""
        self.selected = self.var_selected.get()
        if self.on_select:
            self.on_select(self.filepath, self.selected)

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.selected = selected
        self.var_selected.set(selected)

    def is_selected(self) -> bool:
        """获取选中状态"""
        return self.selected


class ImagePreviewWidget(tk.Frame):
    """图片预览组件"""

    def __init__(self, master, max_size: tuple = (400, 400), **kwargs):
        super().__init__(master, **kwargs)

        self.max_size = max_size
        self.current_image = None

        # 预览标签
        self.preview_label = tk.Label(self, text='选择图片预览', bg='white')
        self.preview_label.pack(expand=True, fill=tk.BOTH)

    def load_image(self, filepath: str):
        """加载图片预览"""
        try:
            with Image.open(filepath) as img:
                # 计算缩放比例
                ratio = min(
                    self.max_size[0] / img.width,
                    self.max_size[1] / img.height
                )
                new_size = (int(img.width * ratio), int(img.height * ratio))

                img = img.resize(new_size, Image.Resampling.LANCZOS)
                self.current_image = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=self.current_image, text='')
        except Exception as e:
            self.preview_label.configure(image=None, text=f'无法加载: {str(e)}')

    def clear(self):
        """清空预览"""
        self.current_image = None
        self.preview_label.configure(image=None, text='选择图片预览')


class MetadataEditorWidget(tk.Frame):
    """元信息编辑组件"""

    def __init__(self, master, on_save: Callable = None, **kwargs):
        super().__init__(master, **kwargs)

        self.on_save = on_save
        self.entries = {}
        self.current_file = None

        # 创建滚动区域
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_metadata(self, metadata: dict):
        """加载元信息到编辑器"""
        # 清空现有内容
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.entries.clear()

        self.current_file = metadata.get('filepath')

        # 字段定义
        fields = [
            ('filename', '文件名', False),
            ('extension', '扩展名', False),
            ('filesize', '文件大小', False),
            ('width', '宽度', False),
            ('height', '高度', False),
            ('format', '格式', False),
            ('title', '标题', True),
            ('description', '描述', True),
            ('artist', '作者', True),
            ('copyright', '版权', True),
            ('make', '相机品牌', True),
            ('model', '相机型号', True),
            ('software', '软件', True),
            ('lens', '镜头型号', True),
            ('datetime', '拍摄时间', True),
            ('exposure_time', '曝光时间', False),
            ('fnumber', '光圈', False),
            ('iso', 'ISO', False),
            ('focal_length', '焦距', False),
            ('orientation', '方向', False),
        ]

        row = 0
        for field, label, editable in fields:
            value = metadata.get(field, '')
            if value is None:
                value = ''

            # 标签
            tk.Label(
                self.scrollable_frame,
                text=f"{label}:",
                font=('Arial', 9, 'bold'),
                anchor=tk.W
            ).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)

            # 值
            if editable:
                entry = tk.Entry(self.scrollable_frame, width=40)
                entry.insert(0, str(value))
                entry.grid(row=row, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
                self.entries[field] = entry
            else:
                tk.Label(
                    self.scrollable_frame,
                    text=str(value),
                    anchor=tk.W
                ).grid(row=row, column=1, sticky=tk.W + tk.E, padx=5, pady=2)

            row += 1

        # 保存按钮
        if self.on_save:
            tk.Button(
                self.scrollable_frame,
                text='保存修改',
                command=self._on_save
            ).grid(row=row, column=0, columnspan=2, pady=10)

    def _on_save(self):
        """保存修改"""
        if not self.on_save or not self.current_file:
            return

        metadata = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if value:
                metadata[field] = value

        self.on_save(self.current_file, metadata)

    def get_editable_metadata(self) -> dict:
        """获取可编辑的元信息"""
        metadata = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if value:
                metadata[field] = value
        return metadata


class ProgressDialog(tk.Toplevel):
    """进度对话框"""

    def __init__(self, master, title: str = '处理中', **kwargs):
        super().__init__(master, **kwargs)

        self.title(title)
        self.transient(master)
        self.grab_set()

        # 居中显示
        window_width = 400
        window_height = 150
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.resizable(False, False)

        # 文件名标签
        self.file_label = tk.Label(self, text='准备中...', wraplength=380)
        self.file_label.pack(pady=10)

        # 进度条
        self.progress = ttk.Progressbar(self, length=350, mode='determinate')
        self.progress.pack(pady=5)

        # 状态标签
        self.status_label = tk.Label(self, text='')
        self.status_label.pack(pady=5)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def update_progress(self, current: int, total: int, filename: str = ''):
        """更新进度"""
        self.progress['maximum'] = total
        self.progress['value'] = current

        if filename:
            self.file_label.configure(text=filename)

        self.status_label.configure(text=f'{current}/{total}')
        self.update()

    def _on_close(self):
        """关闭对话框"""
        pass  # 禁止关闭


class ScrollableFrame(tk.Frame):
    """可滚动框架"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.canvas = tk.Canvas(self)
        self.scrollbar_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 绑定鼠标滚轮
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
