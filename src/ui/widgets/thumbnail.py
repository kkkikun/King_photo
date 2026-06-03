"""
King_photo - 缩略图组件
"""
import logging
import threading
import tkinter as tk

import ttkbootstrap as ttk
from typing import Callable
from PIL import Image, ImageTk
import os

from ...utils.image_loader import load_image

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
        self._destroyed = False  # 标记控件是否已被销毁

        # Checkbox
        self.var_selected = tk.BooleanVar(value=False)
        self.checkbox = tk.Checkbutton(self, variable=self.var_selected,
                                       command=self._on_checkbox_change)
        self.checkbox.pack(side=tk.TOP, anchor=tk.W)

        # Image preview
        self.image_label = tk.Label(self, cursor="hand2", text="Loading...")
        self.image_label.pack(side=tk.TOP, padx=2, pady=2)
        self.image_label.bind("<Button-1>", self._on_image_click)

        # Filename
        filename = os.path.basename(filepath)
        display_name = filename if len(filename) <= 15 else filename[:12] + '...'
        self.name_label = tk.Label(self, text=display_name,
                                    wraplength=size[0], font=('Arial', 8))
        self.name_label.pack(side=tk.TOP)

    def destroy(self):
        """重写destroy方法，标记控件已销毁"""
        self._destroyed = True
        super().destroy()

    def _load_thumbnail(self):
        """同步加载缩略图"""
        try:
            if not os.path.exists(self.filepath):
                self.image_label.configure(text='File not found', width=self.size[0] // 8,
                                           height=self.size[1] // 16)
                self._loaded = True
                return
            
            if not os.access(self.filepath, os.R_OK):
                self.image_label.configure(text='No permission', width=self.size[0] // 8,
                                           height=self.size[1] // 16)
                self._loaded = True
                return
            
            img, err = load_image(self.filepath)
            if img:
                img.thumbnail(self.size)
                self.photo = ImageTk.PhotoImage(img)
                self.image_label.configure(image=self.photo, text='')
                img.close()
            else:
                display_text = self._get_error_display(err)
                self.image_label.configure(text=display_text,
                                           width=self.size[0] // 8,
                                           height=self.size[1] // 16)
            self._loaded = True
        except Exception as e:
            logger.warning(f"Failed to load thumbnail: {self.filepath}, {e}")
            self.image_label.configure(text='Error', width=self.size[0] // 8,
                                       height=self.size[1] // 16)
            self._loaded = True

    def load_thumbnail_async(self, callback: Callable = None):
        """异步加载缩略图"""
        if self._loaded:
            if callback: callback()
            return

        def _load():
            try:
                if not os.path.exists(self.filepath):
                    self.after(0, lambda: self._show_error('File not found', callback))
                    return
                if not os.access(self.filepath, os.R_OK):
                    self.after(0, lambda: self._show_error('No permission', callback))
                    return
                
                img, err = load_image(self.filepath)
                if img:
                    img.thumbnail(self.size)
                    photo = ImageTk.PhotoImage(img)
                    img.close()
                    self.after(0, lambda: self._show_image(photo, callback))
                else:
                    display = self._get_error_display(err)
                    self.after(0, lambda: self._show_error(display, callback))
            except Exception as e:
                logger.warning(f"Async thumbnail failed: {self.filepath}, {e}")
                self.after(0, lambda: self._show_error('Error', callback))

        threading.Thread(target=_load, daemon=True).start()

    def _show_image(self, photo, callback=None):
        """显示加载的图片"""
        if self._destroyed:
            return  # 控件已销毁，不再更新
        self.photo = photo
        self.image_label.configure(image=self.photo, text='')
        self._loaded = True
        if callback: callback()

    def _show_error(self, text, callback=None):
        """显示错误信息"""
        if self._destroyed:
            return  # 控件已销毁，不再更新
        self.image_label.configure(text=text, width=self.size[0] // 8,
                                   height=self.size[1] // 16)
        self._loaded = True
        if callback: callback()

    def _get_error_display(self, err: str = None) -> str:
        """Generate user-friendly error display text"""
        if err and 'not found' in err.lower():
            return 'File missing'
        if err and 'permission' in err.lower():
            return 'No access'
        ext = os.path.splitext(self.filepath)[1].lower()
        if ext in ('.heic', '.heif'):
            return 'HEIC (no lib)'
        if ext == '.avif':
            return 'AVIF (no lib)'
        if ext in ('.jxl',):
            return 'JXL (no lib)'
        if ext in ('.svg',):
            return 'SVG (no lib)'
        if ext in ('.cr2', '.nef', '.arw', '.dng'):
            return 'RAW (no lib)'
        return 'Unsupported'

    def _on_image_click(self, event):
        if self.on_click: self.on_click(self.filepath)

    def _on_checkbox_change(self):
        self.selected = self.var_selected.get()
        if self.on_select: self.on_select(self.filepath, self.selected)

    def set_selected(self, selected: bool):
        self.selected = selected
        self.var_selected.set(selected)

    def is_selected(self) -> bool:
        return self.selected
