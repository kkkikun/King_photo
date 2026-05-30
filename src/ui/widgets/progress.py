"""
King_photo - 进度对话框组件
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox

logger = logging.getLogger(__name__)


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

        window_width = 400
        window_height = 180
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.resizable(False, False)

        self.file_label = tk.Label(self, text='准备中...', wraplength=380)
        self.file_label.pack(pady=10)

        self.progress = ttk.Progressbar(self, length=350, mode='determinate')
        self.progress.pack(pady=5)

        self.status_label = tk.Label(self, text='')
        self.status_label.pack(pady=5)

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
