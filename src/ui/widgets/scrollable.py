"""
King_photo - 可滚动框架组件
"""

import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class ScrollableFrame(tk.Frame):
    """可滚动框架 —— 用于对话框内容区域，自动处理鼠标滚轮"""

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

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
