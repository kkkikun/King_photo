"""
King_photo - 文件夹模式视图（优化版）
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

# 缩略图配置
THUMBNAIL_WIDTH = 140
THUMBNAIL_HEIGHT = 160
MIN_COLS = 1
MAX_COLS = 10
SAFETY_MARGIN = 30

# 虚拟滚动配置
VIRTUAL_SCROLL_ENABLED = True  # 启用虚拟滚动
VISIBLE_BUFFER_ROWS = 2  # 额外渲染的行数（上下各2行）
MAX_VISIBLE_WIDGETS = 100  # 最大可见控件数
ROW_HEIGHT = THUMBNAIL_HEIGHT + 10  # 行高（包括padding）


class FolderView(ttk.Frame):
    """文件夹模式视图"""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)

        self.app = app
        self.folder_path = None
        self.files = []  # 所有文件路径
        self.thumbnails = []  # 兼容旧代码，不再使用
        self.selected_files = set()
        
        # 虚拟滚动相关属性
        self.visible_widgets = {}  # 索引 -> 控件
        self.selected_states = {}  # 索引 -> bool
        self.virtual_height = 0
        self.first_visible_row = 0
        self.last_visible_row = 0
        self.scroll_update_id = None
        
        # 动态布局相关
        self.debounce_id = None
        self.current_cols = 0
        self.last_canvas_width = 0
        
        self.api = get_api()

        self._create_ui()

    def _create_ui(self):
        """创建UI"""
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
        self.thumbnail_canvas.configure(yscrollcommand=self.thumbnail_scrollbar.set)

        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.thumbnail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        self.thumbnail_canvas.bind("<Enter>", self._on_canvas_enter)
        self.thumbnail_canvas.bind("<Leave>", self._on_canvas_leave)
        
        # 绑定画布大小变化事件
        self.thumbnail_canvas.bind("<Configure>", self._on_canvas_resize)

        # 右侧：预览和信息
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=3)

        self.preview = ImagePreviewWidget(right_frame, max_size=(600, 500))
        self.preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

        info_frame = ttk.LabelFrame(right_frame, text="图片信息")
        info_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        self.info_text = tk.Text(info_frame, height=12, wrap=tk.WORD)
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
        self.selected_states.clear()

        # 清空现有控件
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()
        self.visible_widgets.clear()

        if not VIRTUAL_SCROLL_ENABLED:
            # 原有逻辑：创建所有控件
            self._create_all_widgets(files)
        else:
            # 虚拟滚动：只创建可见控件
            self._setup_virtual_scroll()
            self._update_visible_widgets()

        self._update_select_count()

    def _create_all_widgets(self, files: List[str]):
        """创建所有控件（原有逻辑）"""
        # 计算列数
        cols = self._calculate_cols()
        self.current_cols = cols

        # 批量创建缩略图（使用grid布局）
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

        # 异步加载所有缩略图（避免阻塞UI）
        self._async_load_thumbnails(0, min(len(files), 5))

    def _async_load_thumbnails(self, start_idx, batch_size):
        """异步分批加载缩略图"""
        if start_idx >= len(self.thumbnails):
            return
        
        end_idx = min(start_idx + batch_size, len(self.thumbnails))
        
        # 加载当前批次
        for i in range(start_idx, end_idx):
            self.thumbnails[i].load_thumbnail_async()
        
        # 调度下一批次
        self.after(10, lambda: self._async_load_thumbnails(end_idx, batch_size))

    def _setup_virtual_scroll(self):
        """设置虚拟滚动区域"""
        cols = self._calculate_cols()
        if cols == 0:
            cols = 1
        
        # 更新current_cols
        self.current_cols = cols
        
        total_rows = (len(self.files) + cols - 1) // cols
        self.virtual_height = total_rows * ROW_HEIGHT

        # 设置虚拟滚动区域
        self.thumbnail_frame.configure(height=self.virtual_height)
        self.thumbnail_canvas.configure(scrollregion=(0, 0, 0, self.virtual_height))

    def _update_visible_widgets(self):
        """更新可见区域的控件"""
        if not self.files:
            return

        # 获取当前滚动位置
        scroll_top = self.thumbnail_canvas.canvasy(0)
        scroll_bottom = scroll_top + self.thumbnail_canvas.winfo_height()

        # 计算可见行范围
        cols = self._calculate_cols()
        if cols == 0:
            cols = 1
        
        # 更新current_cols
        self.current_cols = cols

        first_visible_row = max(0, int(scroll_top / ROW_HEIGHT) - VISIBLE_BUFFER_ROWS)
        last_visible_row = min(
            (len(self.files) + cols - 1) // cols,
            int(scroll_bottom / ROW_HEIGHT) + VISIBLE_BUFFER_ROWS
        )

        # 计算可见控件索引范围
        first_visible_idx = first_visible_row * cols
        last_visible_idx = min(len(self.files), (last_visible_row + 1) * cols)

        # 销毁不在可见范围内的控件
        for idx in list(self.visible_widgets.keys()):
            if idx < first_visible_idx or idx >= last_visible_idx:
                self.visible_widgets[idx].destroy()
                del self.visible_widgets[idx]

        # 创建新进入可见范围的控件
        for idx in range(first_visible_idx, last_visible_idx):
            if idx not in self.visible_widgets:
                self._create_thumbnail_widget(idx)

        # 更新控件位置
        self._update_widget_positions()

    def _create_thumbnail_widget(self, idx: int):
        """创建指定索引的缩略图控件"""
        filepath = self.files[idx]
        
        # 确保current_cols不为0
        cols = self.current_cols if self.current_cols > 0 else self._calculate_cols()
        if cols == 0:
            cols = 1
        
        row = idx // cols
        col = idx % cols

        # 检查是否已选中
        is_selected = self.selected_states.get(idx, False)

        thumb = ThumbnailWidget(
            self.thumbnail_frame,
            filepath,
            size=(120, 120),
            on_click=self._on_thumbnail_click,
            on_select=lambda fp, sel, i=idx: self._on_thumbnail_select_virtual(fp, sel, i)
        )

        # 恢复选中状态
        if is_selected:
            thumb.set_selected(True)

        thumb.grid(row=row, column=col, padx=5, pady=5)
        self.visible_widgets[idx] = thumb

        # 异步加载缩略图
        thumb.load_thumbnail_async()

    def _update_widget_positions(self):
        """更新控件位置"""
        cols = self._calculate_cols()
        if cols == 0:
            cols = 1
        
        # 更新current_cols
        self.current_cols = cols

        for idx, thumb in self.visible_widgets.items():
            row = idx // cols
            col = idx % cols
            thumb.grid(row=row, column=col, padx=5, pady=5)

    def _calculate_cols(self) -> int:
        """根据画布宽度计算列数"""
        canvas_width = self.thumbnail_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self.thumbnail_canvas.winfo_reqwidth()
        
        available_width = canvas_width - 20 - SAFETY_MARGIN
        cols = max(MIN_COLS, min(MAX_COLS, available_width // THUMBNAIL_WIDTH))
        return cols

    def _on_canvas_resize(self, event):
        """画布大小变化时重新排列缩略图（带防抖）"""
        current_width = self.thumbnail_canvas.winfo_width()
        if current_width == self.last_canvas_width:
            return
        
        self.last_canvas_width = current_width
        
        if self.debounce_id:
            self.after_cancel(self.debounce_id)
        
        self.debounce_id = self.after(200, self._on_resize_debounced)

    def _on_resize_debounced(self):
        """防抖后的重排处理"""
        new_cols = self._calculate_cols()
        if new_cols != self.current_cols:
            self.current_cols = new_cols
            if VIRTUAL_SCROLL_ENABLED and self.files:
                # 重新计算虚拟滚动区域
                self._setup_virtual_scroll()
                # 更新可见控件
                self._update_visible_widgets()
            else:
                # 原有逻辑：重新排列所有控件
                self._rearrange_thumbnails()

    def _rearrange_thumbnails(self):
        """重新排列缩略图到正确的网格位置"""
        if not self.thumbnails:
            return
        
        cols = self._calculate_cols()
        
        if cols == self.current_cols:
            return
        
        self.current_cols = cols
        
        # 重新排列所有缩略图
        for i, thumb in enumerate(self.thumbnails):
            new_row = i // cols
            new_col = i % cols
            thumb.grid(row=new_row, column=new_col, padx=5, pady=5)

    def _on_canvas_enter(self, event):
        """鼠标进入画布区域时绑定全局滚轮事件"""
        self.thumbnail_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_leave(self, event):
        """鼠标离开画布区域时解绑全局滚轮事件"""
        self.thumbnail_canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        """鼠标滚轮事件"""
        self.thumbnail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # 触发虚拟滚动更新
        self._on_scroll()

    def _on_scroll(self, event=None):
        """滚动事件处理"""
        if self.scroll_update_id:
            self.after_cancel(self.scroll_update_id)

        # 使用防抖机制，避免频繁更新
        self.scroll_update_id = self.after(50, self._update_visible_widgets)

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

    def _on_thumbnail_select_virtual(self, filepath: str, selected: bool, idx: int):
        """虚拟滚动模式下的选中状态改变"""
        if selected:
            self.selected_states[idx] = True
            self.selected_files.add(filepath)
        else:
            self.selected_states[idx] = False
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
        if VIRTUAL_SCROLL_ENABLED and self.files:
            # 虚拟滚动模式
            for idx in range(len(self.files)):
                self.selected_states[idx] = True
                filepath = self.files[idx]
                self.selected_files.add(filepath)
                # 更新可见控件
                if idx in self.visible_widgets:
                    self.visible_widgets[idx].set_selected(True)
        else:
            # 原有模式
            for thumb in self.thumbnails:
                thumb.set_selected(True)
                self.selected_files.add(thumb.filepath)
        self._update_select_count()

    def invert_selection(self):
        """反选"""
        if VIRTUAL_SCROLL_ENABLED and self.files:
            # 虚拟滚动模式
            self.selected_files.clear()
            for idx in range(len(self.files)):
                new_state = not self.selected_states.get(idx, False)
                self.selected_states[idx] = new_state
                filepath = self.files[idx]
                if new_state:
                    self.selected_files.add(filepath)
                # 更新可见控件
                if idx in self.visible_widgets:
                    self.visible_widgets[idx].set_selected(new_state)
        else:
            # 原有模式
            self.selected_files.clear()
            for thumb in self.thumbnails:
                new_state = not thumb.is_selected()
                thumb.set_selected(new_state)
                if new_state:
                    self.selected_files.add(thumb.filepath)
        self._update_select_count()

    def deselect_all(self):
        """取消选择"""
        if VIRTUAL_SCROLL_ENABLED and self.files:
            # 虚拟滚动模式
            for idx in range(len(self.files)):
                self.selected_states[idx] = False
                # 更新可见控件
                if idx in self.visible_widgets:
                    self.visible_widgets[idx].set_selected(False)
        else:
            # 原有模式
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