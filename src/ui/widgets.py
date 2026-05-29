"""
King_photo - 自定义UI组件
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, List, Any
from PIL import Image, ImageTk
import os

from ..core.metadata_reader import MetadataReader

# 获取日志记录器
logger = logging.getLogger(__name__)


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
        self._loaded = False

        # 勾选框
        self.var_selected = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(
            self,
            variable=self.var_selected,
            command=self._on_checkbox_change
        )
        self.checkbox.pack(side=tk.TOP, anchor=tk.W)

        # 图片预览
        self.image_label = tk.Label(self, cursor="hand2", text="加载中...")
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

    def _load_thumbnail(self):
        """同步加载缩略图（用于小文件夹）"""
        try:
            # 检查文件是否存在
            if not os.path.exists(self.filepath):
                logger.warning(f"文件不存在: {self.filepath}")
                self.image_label.configure(
                    text='文件不存在',
                    width=self.size[0] // 8,
                    height=self.size[1] // 16
                )
                self._loaded = True
                return
            
            # 检查文件是否可读
            if not os.access(self.filepath, os.R_OK):
                logger.warning(f"文件不可读: {self.filepath}")
                self.image_label.configure(
                    text='文件不可读',
                    width=self.size[0] // 8,
                    height=self.size[1] // 16
                )
                self._loaded = True
                return
            
            with Image.open(self.filepath) as img:
                img.thumbnail(self.size)
                self.photo = ImageTk.PhotoImage(img)
                self.image_label.configure(image=self.photo, text='')
                self._loaded = True
        except Exception as e:
            logger.warning(f"加载缩略图失败: {self.filepath}, 错误: {str(e)}")
            # 根据错误类型显示不同的提示
            error_msg = str(e).lower()
            if "cannot identify image file" in error_msg:
                display_text = "无法识别"
            elif "corrupt exif data" in error_msg:
                display_text = "EXIF损坏"
            elif "doesnot have exif" in error_msg:
                display_text = "无EXIF"
            elif "broken or corrupt image" in error_msg or "not a valid image" in error_msg:
                display_text = "图片损坏"
            elif "unsupported image format" in error_msg:
                display_text = "不支持的格式"
            elif "unpack requires a buffer" in error_msg:
                display_text = "文件损坏"
            else:
                # 尝试获取文件扩展名以提供更多信息
                ext = os.path.splitext(self.filepath)[1].lower()
                if ext in ['.gif', '.png', '.webp', '.bmp', '.tiff', '.tif']:
                    display_text = f"无法预览{ext.upper()[1:]}"
                else:
                    display_text = "无法预览"
            
            self.image_label.configure(
                text=display_text,
                width=self.size[0] // 8,
                height=self.size[1] // 16
            )
            self._loaded = True

    def load_thumbnail_async(self, callback: Callable = None):
        """异步加载缩略图"""
        if self._loaded:
            if callback:
                callback()
            return

        def _load():
            try:
                # 检查文件是否存在
                if not os.path.exists(self.filepath):
                    logger.warning(f"文件不存在: {self.filepath}")
                    def show_error():
                        self.image_label.configure(
                            text='文件不存在',
                            width=self.size[0] // 8,
                            height=self.size[1] // 16
                        )
                        self._loaded = True
                        if callback:
                            callback()
                    self.after(0, show_error)
                    return
                
                # 检查文件是否可读
                if not os.access(self.filepath, os.R_OK):
                    logger.warning(f"文件不可读: {self.filepath}")
                    def show_error():
                        self.image_label.configure(
                            text='文件不可读',
                            width=self.size[0] // 8,
                            height=self.size[1] // 16
                        )
                        self._loaded = True
                        if callback:
                            callback()
                    self.after(0, show_error)
                    return
                
                with Image.open(self.filepath) as img:
                    img.thumbnail(self.size)
                    photo = ImageTk.PhotoImage(img)

                    # 在主线程中更新UI
                    def update_ui():
                        try:
                            self.photo = photo
                            self.image_label.configure(image=self.photo, text='')
                            self._loaded = True
                            if callback:
                                callback()
                        except Exception:
                            pass

                    self.after(0, update_ui)
            except Exception as e:
                logger.warning(f"异步加载缩略图失败: {self.filepath}, 错误: {str(e)}")
                
                # 根据错误类型显示不同的提示
                error_msg = str(e).lower()
                if "cannot identify image file" in error_msg:
                    # 尝试检查文件头，提供更具体的错误信息
                    display_text = self._get_file_type_error_display()
                elif "corrupt exif data" in error_msg:
                    display_text = "EXIF损坏"
                elif "doesnot have exif" in error_msg:
                    display_text = "无EXIF"
                elif "broken or corrupt image" in error_msg or "not a valid image" in error_msg:
                    display_text = "图片损坏"
                elif "unsupported image format" in error_msg:
                    display_text = "不支持的格式"
                elif "unpack requires a buffer" in error_msg:
                    display_text = "文件损坏"
                else:
                    # 尝试获取文件扩展名以提供更多信息
                    ext = os.path.splitext(self.filepath)[1].lower()
                    if ext in ['.gif', '.png', '.webp', '.bmp', '.tiff', '.tif']:
                        display_text = f"无法预览{ext.upper()[1:]}"
                    else:
                        display_text = "无法预览"
                
                def show_error():
                    self.image_label.configure(
                        text=display_text,
                        width=self.size[0] // 8,
                        height=self.size[1] // 16
                    )
                    self._loaded = True
                    if callback:
                        callback()

                self.after(0, show_error)

        thread = threading.Thread(target=_load, daemon=True)
        thread.start()

    def _on_image_click(self, event):
        """点击图片"""
        if self.on_click:
            self.on_click(self.filepath)

    def _on_checkbox_change(self):
        """勾选状态改变"""
        self.selected = self.var_selected.get()
        if self.on_select:
            self.on_select(self.filepath, self.selected)

    def _get_file_type_error_display(self) -> str:
        """获取文件类型错误显示文本"""
        try:
            # 尝试检查文件头
            with open(self.filepath, 'rb') as f:
                header = f.read(32)
            
            if not header:
                return "空文件"
            
            # 检查常见的视频文件头
            if header.startswith(b'\x00\x00\x00') and (b'ftyp' in header[:12] or b'qt  ' in header[:12]):
                # 检查是否为HEIC/HEIF格式
                if b'heic' in header[:16] or b'heif' in header[:16]:
                    return "HEIC图片"
                # 检查是否为AVIF格式
                elif b'avif' in header[:16] or b'avis' in header[:16]:
                    return "AVIF图片"
                else:
                    return "视频文件"
            elif header.startswith(b'RIFF'):
                # 可能是AVI或WebP
                if len(header) >= 12 and header[8:12] == b'WEBP':
                    return "WebP图片"
                else:
                    return "视频文件"
            elif header.startswith(b'\x1aE\xdf\xa3'):
                return "MKV视频"
            elif header.startswith(b'\x00\x00\x01\x00'):
                return "图标文件"
            elif header.startswith(b'BM'):
                return "BMP图片"
            elif header.startswith(b'\x89PNG'):
                return "PNG图片"
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                return "GIF图片"
            elif header.startswith(b'\xff\xd8\xff'):
                return "JPEG图片"
            else:
                # 根据扩展名提供提示
                ext = os.path.splitext(self.filepath)[1].lower()
                if ext in ['.mov', '.mp4', '.avi', '.wmv', '.mkv']:
                    return "视频文件"
                elif ext in ['.heic', '.heif']:
                    return "HEIC图片"
                elif ext in ['.avif']:
                    return "AVIF图片"
                elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
                    return f"无法识别{ext.upper()[1:]}"
                else:
                    return "无法识别"
        except Exception as e:
            logger.debug(f"检查文件类型失败: {self.filepath}, 错误: {str(e)}")
            return "无法识别"

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
        
        # 获取格式适配的可编辑字段
        editable_fields = MetadataReader.get_editable_fields(self.current_file)
        
        # 显示格式信息
        format_info = editable_fields.get('_format_info', {})
        self._show_format_info(format_info)
        
        # 按类别分组显示字段
        row = 0
        
        # 基本信息
        basic_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'basic'}
        if basic_fields:
            row = self._add_field_group("基本信息", basic_fields, row)
        
        # 时间字段
        time_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'time'}
        if time_fields:
            row = self._add_field_group("时间信息", time_fields, row)
        
        # XMP字段
        xmp_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'xmp'}
        if xmp_fields:
            row = self._add_field_group("XMP信息", xmp_fields, row)
        
        # EXIF字段
        exif_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'exif'}
        if exif_fields:
            row = self._add_field_group("EXIF信息", exif_fields, row)
        
        # 保存按钮
        if self.on_save:
            tk.Button(
                self.scrollable_frame,
                text='保存修改',
                command=self._on_save
            ).grid(row=row, column=0, columnspan=2, pady=10)
    
    def _show_format_info(self, format_info: dict):
        """显示格式信息"""
        format_name = format_info.get('format', 'Unknown')
        supports_exif = format_info.get('supports_exif', False)
        supports_xmp = format_info.get('supports_xmp', False)
        needs_exiftool = format_info.get('needs_exiftool', False)
        
        # 创建格式信息框架
        info_frame = ttk.LabelFrame(self.scrollable_frame, text="格式信息")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E, padx=5, pady=5)
        
        # 格式名称
        tk.Label(
            info_frame,
            text=f"格式: {format_name}",
            font=('Arial', 9, 'bold'),
            anchor=tk.W
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        # 支持情况
        supports = []
        if supports_exif:
            supports.append("EXIF")
        if supports_xmp:
            supports.append("XMP")
        if needs_exiftool:
            supports.append("需要ExifTool")
        
        support_text = "支持: " + ", ".join(supports) if supports else "不支持元数据编辑"
        tk.Label(
            info_frame,
            text=support_text,
            anchor=tk.W
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
    
    def _add_field_group(self, group_name: str, fields: dict, start_row: int) -> int:
        """添加字段组"""
        # 组标题
        ttk.Separator(self.scrollable_frame, orient=tk.HORIZONTAL).grid(
            row=start_row, column=0, columnspan=2, sticky=tk.W + tk.E, padx=5, pady=5
        )
        start_row += 1
        
        tk.Label(
            self.scrollable_frame,
            text=f"{group_name}:",
            font=('Arial', 9, 'bold'),
            anchor=tk.W
        ).grid(row=start_row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        start_row += 1
        
        row = start_row
        for field_name, field_info in fields.items():
            value = field_info.get('value', '')
            if value is None:
                value = ''
            
            label = field_info.get('label', field_name)
            editable = field_info.get('editable', False)
            
            # 根据可编辑状态设置颜色
            if editable:
                label_fg = '#000000'  # 黑色
                entry_state = 'normal'
                entry_bg = '#FFFFFF'  # 白色背景
            else:
                label_fg = '#888888'  # 灰色
                entry_state = 'disabled'
                entry_bg = '#F0F0F0'  # 灰色背景
            
            # 标签
            tk.Label(
                self.scrollable_frame,
                text=f"{label}:",
                font=('Arial', 9),
                anchor=tk.W,
                fg=label_fg
            ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
            
            # 值
            if editable:
                entry = tk.Entry(self.scrollable_frame, width=40)
                entry.insert(0, str(value))
                entry.grid(row=row, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
                self.entries[field_name] = entry
            else:
                entry = tk.Entry(self.scrollable_frame, width=40, state=entry_state, bg=entry_bg)
                entry.insert(0, str(value))
                entry.grid(row=row, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
                # 禁用状态下的Entry不会响应用户输入，但保留值
            
            row += 1
        
        return row

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

    def __init__(self, master, title: str = '处理中', cancellable: bool = True, **kwargs):
        super().__init__(master, **kwargs)

        self.title(title)
        self.transient(master)
        self.grab_set()

        self.cancellable = cancellable
        self.cancelled = False
        self.cancel_callback = None

        # 居中显示
        window_width = 400
        window_height = 180
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

        # 取消按钮
        if cancellable:
            self.cancel_button = ttk.Button(
                self,
                text='取消',
                command=self._on_cancel,
                width=10
            )
            self.cancel_button.pack(pady=5)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def update_progress(self, current: int, total: int, filename: str = ''):
        """更新进度"""
        if self.cancelled:
            return

        self.progress['maximum'] = total
        self.progress['value'] = current

        if filename:
            self.file_label.configure(text=filename)

        self.status_label.configure(text=f'{current}/{total}')
        self.update()

    def set_cancel_callback(self, callback):
        """设置取消回调"""
        self.cancel_callback = callback

    def _on_cancel(self):
        """取消操作"""
        if messagebox.askyesno("确认", "确定要取消当前操作吗？"):
            self.cancelled = True
            self.cancel_button.configure(state='disabled', text='取消中...')
            self.status_label.configure(text='正在取消...')

            if self.cancel_callback:
                self.cancel_callback()

    def _on_close(self):
        """关闭对话框"""
        if self.cancellable:
            self._on_cancel()
        # 如果不可取消，则忽略关闭事件


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
