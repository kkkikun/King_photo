"""
King_photo - 图片预览组件
"""

import logging
import tkinter as tk
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)


class ImagePreviewWidget(tk.Frame):
    """图片预览组件"""

    def __init__(self, master, max_size: tuple = (400, 400), **kwargs):
        super().__init__(master, **kwargs)

        self.max_size = max_size
        self.current_image = None

        self.preview_label = tk.Label(self, text='选择图片预览', bg='white')
        self.preview_label.pack(expand=True, fill=tk.BOTH)

    def load_image(self, filepath: str):
        """加载图片预览"""
        try:
            with Image.open(filepath) as img:
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
