"""
King_photo - 文件夹模式视图
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from .widgets import ThumbnailWidget, ImagePreviewWidget, MetadataEditorWidget
from ..api import get_api
from ..utils.helpers import format_file_size, format_datetime

# 异步加载阈值：文件数量超过此值时使用异步加载
ASYNC_THRESHOLD = 20


class FolderView(ttk.Frame):
    """文件夹模式视图"""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)

        self.app = app
        self.folder_path = None
        self.files = []
        self.thumbnails = []
        self.selected_files = set()
        
        # 初始化统一API
        self.api = get_api()

        self._create_ui()

    def _create_ui(self):
        """创建UI"""
        # 主分割面板
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 左侧：缩略图列表
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=2)

        # 选择控制栏
        select_frame = ttk.Frame(left_frame)
        select_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(select_frame, text="全选", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(select_frame, text="反选", command=self.invert_selection).pack(side=tk.LEFT, padx=2)
        ttk.Button(select_frame, text="取消选择", command=self.deselect_all).pack(side=tk.LEFT, padx=2)

        self.select_count_label = ttk.Label(select_frame, text="已选: 0")
        self.select_count_label.pack(side=tk.RIGHT, padx=5)

        # 缩略图滚动区域
        self.thumbnail_canvas = tk.Canvas(left_frame)
        self.thumbnail_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.thumbnail_canvas.yview)

        self.thumbnail_frame = ttk.Frame(self.thumbnail_canvas)
        self.thumbnail_frame.bind(
            "<Configure>",
            lambda e: self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))
        )

        self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_frame, anchor=tk.NW)
        self.thumbnail_canvas.configure(yscrollcommand=self.thumbnail_scrollbar.set)

        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.thumbnail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        self.thumbnail_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 右侧：预览和信息
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=1)

        # 图片预览
        self.preview = ImagePreviewWidget(right_frame, max_size=(300, 300))
        self.preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 信息显示
        info_frame = ttk.LabelFrame(right_frame, text="图片信息")
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.info_text = tk.Text(info_frame, height=10, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def show(self):
        """显示视图"""
        self.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """隐藏视图"""
        self.pack_forget()

    def load_folder(self, folder_path: str, files: List[str]):
        """加载文件夹"""
        self.folder_path = folder_path
        self.files = files
        self.selected_files.clear()

        # 清空现有缩略图
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()
        self.thumbnails.clear()

        # 创建缩略图
        cols = 4  # 每行4个
        use_async = len(files) > ASYNC_THRESHOLD

        for i, filepath in enumerate(files):
            row = i // cols
            col = i % cols

            thumb = ThumbnailWidget(
                self.thumbnail_frame,
                filepath,
                size=(120, 120),
                on_click=self._on_thumbnail_click,
                on_select=self._on_thumbnail_select
            )
            thumb.grid(row=row, column=col, padx=5, pady=5)
            self.thumbnails.append(thumb)

            if use_async:
                thumb.load_thumbnail_async()

        self._update_select_count()

    def _on_thumbnail_click(self, filepath: str):
        """点击缩略图"""
        # 显示预览
        self.preview.load_image(filepath)

        # 显示信息
        self._show_image_info(filepath)

    def _on_thumbnail_select(self, filepath: str, selected: bool):
        """缩略图选中状态改变"""
        if selected:
            self.selected_files.add(filepath)
        else:
            self.selected_files.discard(filepath)

        self._update_select_count()

    def _show_image_info(self, filepath: str):
        """显示图片信息"""
        metadata = self.api.get_metadata_summary(filepath)

        self.info_text.delete(1.0, tk.END)

        info = f"文件名: {metadata['filename']}\n"
        info += f"格式: {metadata['format']}\n"
        info += f"大小: {format_file_size(metadata['filesize'])}\n"
        info += f"尺寸: {metadata['width']} x {metadata['height']}\n"
        info += f"拍摄时间: {format_datetime(metadata['datetime'])}\n"

        if metadata.get('make'):
            info += f"品牌: {metadata['make']}\n"
        if metadata.get('model'):
            info += f"型号: {metadata['model']}\n"

        if not metadata.get('is_consistent', True):
            info += "\n⚠️ 警告: 文件后缀与实际格式不一致\n"

        self.info_text.insert(1.0, info)

    def _update_select_count(self):
        """更新选择计数"""
        self.select_count_label.configure(text=f"已选: {len(self.selected_files)}")

    def _on_mousewheel(self, event):
        """鼠标滚轮"""
        self.thumbnail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def select_all(self):
        """全选"""
        for thumb in self.thumbnails:
            thumb.set_selected(True)
            self.selected_files.add(thumb.filepath)
        self._update_select_count()

    def invert_selection(self):
        """反选"""
        self.selected_files.clear()
        for thumb in self.thumbnails:
            new_state = not thumb.is_selected()
            thumb.set_selected(new_state)
            if new_state:
                self.selected_files.add(thumb.filepath)
        self._update_select_count()

    def deselect_all(self):
        """取消选择"""
        for thumb in self.thumbnails:
            thumb.set_selected(False)
        self.selected_files.clear()
        self._update_select_count()

    def get_selected_files(self) -> List[str]:
        """获取选中的文件列表"""
        return list(self.selected_files)

    def refresh(self):
        """刷新视图"""
        if self.folder_path:
            self.files = get_image_files_in_folder(self.folder_path)
            self.load_folder(self.folder_path, self.files)
