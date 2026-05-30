"""
King_photo - 缩略图组件
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable
from PIL import Image, ImageTk
import os

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
            if not os.path.exists(self.filepath):
                logger.warning(f"文件不存在: {self.filepath}")
                self.image_label.configure(
                    text='文件不存在',
                    width=self.size[0] // 8,
                    height=self.size[1] // 16
                )
                self._loaded = True
                return
            
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
                error_msg = str(e).lower()
                if "cannot identify image file" in error_msg:
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
        if self.on_click:
            self.on_click(self.filepath)

    def _on_checkbox_change(self):
        self.selected = self.var_selected.get()
        if self.on_select:
            self.on_select(self.filepath, self.selected)

    def _get_file_type_error_display(self) -> str:
        try:
            with open(self.filepath, 'rb') as f:
                header = f.read(32)
            if not header:
                return "空文件"
            if header.startswith(b'\x00\x00\x00') and (b'ftyp' in header[:12] or b'qt  ' in header[:12]):
                if b'heic' in header[:16] or b'heif' in header[:16]:
                    return "HEIC图片"
                elif b'avif' in header[:16] or b'avis' in header[:16]:
                    return "AVIF图片"
                else:
                    return "视频文件"
            elif header.startswith(b'RIFF'):
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
        self.selected = selected
        self.var_selected.set(selected)

    def is_selected(self) -> bool:
        return self.selected
