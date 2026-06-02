"""
King_photo - 文件夹模式视图（虚拟列表优化版）
"""

import os
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import PanedWindow
from typing import List, Dict, Optional

import ttkbootstrap as ttk

from .widgets import ThumbnailWidget, ImagePreviewWidget, MetadataEditorWidget
from ..api import get_api
from ..utils.helpers import format_file_size, format_datetime, get_image_files_in_folder

# 异步加载阈值：文件数量超过此值时使用异步加载
ASYNC_THRESHOLD = 20

# 缩略图配置
THUMBNAIL_WIDTH = 140  # 每个缩略图占用的总宽度（包括间距）
THUMBNAIL_HEIGHT = 160  # 每个缩略图占用的总高度（包括间距）
MIN_COLS = 1
MAX_COLS = 10
SAFETY_MARGIN = 30  # 安全边距

# 虚拟列表配置
BUFFER_ROWS = 2  # 可见区域上下各额外渲染的行数


class FolderView(ttk.Frame):
    """文件夹模式视图（虚拟列表优化版）"""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)

        self.app = app
        self.folder_path = None
        self.files = []
        self.thumbnails = []  # 所有缩略图控件（缓存）
        self.visible_thumbnails = {}  # 当前可见的缩略图 {index: widget}
        self.selected_files = set()
        
        # 防抖相关
        self.debounce_id = None
        self.current_cols = 0
        self.last_canvas_width = 0
        
        # 虚拟列表相关
        self.thumbnail_frame_height = 0  # 总高度（用于scrollregion）
        self.rendered_start = 0  # 当前渲染的起始索引
        self.rendered_end = 0  # 当前渲染的结束索引
        
        # 初始化统一API
        self.api = get_api()

        self._create_ui()

    def _create_ui(self):
        """创建UI"""
        # 主分割面板
        self.paned = PanedWindow(self, orient=tk.HORIZONTAL)
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
        self.thumbnail_canvas.configure(yscrollcommand=self.scrollbar_yview)

        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.thumbnail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        self.thumbnail_canvas.bind("<Enter>", self._on_canvas_enter)
        self.thumbnail_canvas.bind("<Leave>", self._on_canvas_leave)
        
        # 绑定画布大小变化事件
        self.thumbnail_canvas.bind("<Configure>", self._on_canvas_resize)
        
        # 绑定滚动事件
        self.thumbnail_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # 右侧：预览和信息
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=3)

        # 图片预览
        self.preview = ImagePreviewWidget(right_frame, max_size=(600, 500))
        self.preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

        # 信息显示
        info_frame = ttk.LabelFrame(right_frame, text="图片信息")
        info_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        self.info_text = tk.Text(info_frame, height=12, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def scrollbar_yview(self, *args):
        """滚动条回调，同步更新可见区域"""
        if args:
            if args[0] == 'moveto':
                self.thumbnail_canvas.yview_moveto(args[1])
            elif args[0] == 'scroll':
                self.thumbnail_canvas.yview_scroll(args[1], args[2])
        self._update_visible_thumbnails()

    def show(self):
        """显示视图"""
        self.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """隐藏视图"""
        self.pack_forget()

    def load_folder(self, folder_path: str, files: List[str]):
        """加载文件夹（虚拟列表模式）"""
        self.folder_path = folder_path
        self.files = files
        self.selected_files.clear()

        # 清空现有控件
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()
        self.thumbnails.clear()
        self.visible_thumbnails.clear()

        # 计算列数
        cols = self._calculate_cols()
        self.current_cols = cols
        
        # 计算总高度
        total_rows = (len(files) + cols - 1) // cols
        self.thumbnail_frame_height = total_rows * THUMBNAIL_HEIGHT
        
        # 更新canvas的scrollregion
        self.thumbnail_canvas.configure(scrollregion=(0, 0, 1, self.thumbnail_frame_height))
        
        # 刷新可见区域
        self._update_visible_thumbnails()
        
        self._update_select_count()

    def _calculate_cols(self) -> int:
        """根据画布宽度计算列数"""
        canvas_width = self.thumbnail_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self.thumbnail_canvas.winfo_reqwidth()
        
        available_width = canvas_width - 20 - SAFETY_MARGIN
        cols = max(MIN_COLS, min(MAX_COLS, available_width // THUMBNAIL_WIDTH))
        return cols

    def _get_visible_range(self) -> tuple:
        """获取当前可见区域的文件索引范围"""
        # 获取当前滚动位置
        y0 = self.thumbnail_canvas.canvasx(0)
        y1 = y0 + self.thumbnail_canvas.winfo_height()
        
        # 计算可见的行范围（包含缓冲行）
        start_row = max(0, int(y0 // THUMBNAIL_HEIGHT) - BUFFER_ROWS)
        end_row = min((len(self.files) + self.current_cols - 1) // self.current_cols, 
                      int(y1 // THUMBNAIL_HEIGHT) + BUFFER_ROWS)
        
        # 转换为文件索引范围
        start_idx = start_row * self.current_cols
        end_idx = min(len(self.files), (end_row + 1) * self.current_cols)
        
        return start_idx, end_idx

    def _update_visible_thumbnails(self):
        """更新可见区域的缩略图"""
        if not self.files:
            return
            
        start_idx, end_idx = self._get_visible_range()
        
        # 移除不再可见的缩略图
        to_remove = []
        for idx in self.visible_thumbnails:
            if idx < start_idx or idx >= end_idx:
                widget = self.visible_thumbnails[idx]
                widget.pack_forget()
                widget.grid_forget()
                to_remove.append(idx)
        
        for idx in to_remove:
            del self.visible_thumbnails[idx]
        
        # 加载新可见的缩略图
        for idx in range(start_idx, end_idx):
            if idx not in self.visible_thumbnails:
                self._create_and_render_thumbnail(idx)
        
        self.rendered_start = start_idx
        self.rendered_end = end_idx

    def _create_and_render_thumbnail(self, idx: int):
        """创建并渲染指定索引的缩略图"""
        if idx >= len(self.files):
            return
        
        filepath = self.files[idx]
        cols = self.current_cols
        
        # 计算位置
        row = idx // cols
        col = idx % cols
        
        # 创建缩略图控件
        thumb = ThumbnailWidget(
            self.thumbnail_frame,
            filepath,
            size=(120, 120),
            on_click=self._on_thumbnail_click,
            on_select=self._on_thumbnail_select
        )
        
        # 设置选中状态
        if filepath in self.selected_files:
            thumb.set_selected(True)
        
        # 放置到正确位置
        thumb.grid(row=row, column=col, padx=5, pady=5)
        self.visible_thumbnails[idx] = thumb
        
        # 异步加载缩略图
        thumb.load_thumbnail_async()

    def _on_canvas_resize(self, event):
        """画布大小变化时重新计算列数并刷新（带防抖）"""
        current_width = self.thumbnail_canvas.winfo_width()
        if current_width == self.last_canvas_width:
            return
        
        self.last_canvas_width = current_width
        
        if self.debounce_id:
            self.after_cancel(self.debounce_id)
        
        self.debounce_id = self.after(200, self._handle_resize)

    def _handle_resize(self):
        """处理窗口大小变化"""
        cols = self._calculate_cols()
        if cols != self.current_cols:
            self.current_cols = cols
            
            # 清空现有控件
            for widget in self.thumbnail_frame.winfo_children():
                widget.destroy()
            self.visible_thumbnails.clear()
            
            # 重新计算总高度
            total_rows = (len(self.files) + cols - 1) // cols
            self.thumbnail_frame_height = total_rows * THUMBNAIL_HEIGHT
            self.thumbnail_canvas.configure(scrollregion=(0, 0, 1, self.thumbnail_frame_height))
            
            # 刷新可见区域
            self._update_visible_thumbnails()

    def _on_canvas_enter(self, event):
        """鼠标进入画布区域时绑定全局滚轮事件"""
        self.thumbnail_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_leave(self, event):
        """鼠标离开画布区域时解绑全局滚轮事件"""
        self.thumbnail_canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        """鼠标滚轮事件"""
        self.thumbnail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._update_visible_thumbnails()

    def _on_thumbnail_click(self, filepath: str):
        """点击缩略图"""
        self.preview.load_image(filepath)
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

    def select_all(self):
        """全选"""
        for idx, filepath in enumerate(self.files):
            self.selected_files.add(filepath)
            # 更新可见控件的选中状态
            if idx in self.visible_thumbnails:
                self.visible_thumbnails[idx].set_selected(True)
        self._update_select_count()

    def invert_selection(self):
        """反选"""
        for idx, filepath in enumerate(self.files):
            if filepath in self.selected_files:
                self.selected_files.remove(filepath)
                if idx in self.visible_thumbnails:
                    self.visible_thumbnails[idx].set_selected(False)
            else:
                self.selected_files.add(filepath)
                if idx in self.visible_thumbnails:
                    self.visible_thumbnails[idx].set_selected(True)
        self._update_select_count()

    def deselect_all(self):
        """取消选择"""
        for idx in self.visible_thumbnails:
            self.visible_thumbnails[idx].set_selected(False)
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