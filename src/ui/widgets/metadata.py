"""
King_photo - 元数据编辑组件
"""

import logging
import tkinter as tk

import ttkbootstrap as ttk
from typing import Callable

from ...api import get_api

logger = logging.getLogger(__name__)

# ── 字段格式提示（灰色占位文字） ──
FIELD_PLACEHOLDERS = {
    # 时间
    'datetime':           'YYYY:MM:DD HH:MM:SS',
    'datetime_original':  'YYYY:MM:DD HH:MM:SS',
    'datetime_digitized': 'YYYY:MM:DD HH:MM:SS',
    'creation_time':      'YYYY:MM:DD HH:MM:SS',
    'file_modified':      'YYYY-MM-DD HH:MM:SS',
    'file_created':       'YYYY-MM-DD HH:MM:SS',
    # 技术参数
    'exposure_time':      '例如: 1/60 或 0.0167',
    'fnumber':            '例如: 2.8',
    'iso':                '例如: 400',
    'focal_length':       '例如: 50',
    'orientation':        '1=正常 3=180° 6=右转90° 8=左转90°',
    # 描述
    'title':              '请输入图片标题',
    'description':        '请输入图片描述',
    'artist':             '请输入作者名称',
    'copyright':          '请输入版权信息 (© 2024)',
    # 相机
    'make':               '例如: Canon',
    'model':              '例如: EOS 5D Mark IV',
    'software':           '例如: Adobe Photoshop 2024',
    'lens':               '例如: EF 24-70mm f/2.8L',
}

PLACEHOLDER_COLOR = '#888888'   # 灰色（darkly/lightly 主题均可见）
NORMAL_COLOR = '#000000'         # 正常（ttkbootstrap 会在 dark 主题自动转为浅色）


class PlaceholderEntry(tk.Entry):
    """带格式提示的输入框
    
    - 无内容时：浅灰色显示格式提示
    - 点击获得焦点：自动清除提示，黑色文字
    - 有实际数据时：黑色文字正常显示
    - 失焦且为空：恢复灰色提示
    """
    
    def __init__(self, master, placeholder: str = '', **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self._is_placeholder_shown = False
        
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
    
    def _show_placeholder(self):
        self.delete(0, tk.END)
        self.insert(0, self.placeholder)
        self.config(fg=PLACEHOLDER_COLOR)
        self._is_placeholder_shown = True
    
    def _on_focus_in(self, event):
        if self._is_placeholder_shown:
            self.delete(0, tk.END)
            self.config(fg=NORMAL_COLOR)
            self._is_placeholder_shown = False
    
    def _on_focus_out(self, event):
        if self.get().strip() == '' and self.placeholder:
            self._show_placeholder()
    
    def set_value(self, value):
        """设置实际值"""
        if value:
            self.delete(0, tk.END)
            self.config(fg=NORMAL_COLOR)
            self.insert(0, str(value))
            self._is_placeholder_shown = False
        elif self.placeholder:
            self._show_placeholder()
    
    def get_real_value(self) -> str:
        """获取用户实际输入（占位时返回空字符串）"""
        if self._is_placeholder_shown:
            return ''
        return self.get().strip()


class MetadataEditorWidget(tk.Frame):
    """元信息编辑组件"""

    def __init__(self, master, on_save: Callable = None, **kwargs):
        super().__init__(master, **kwargs)

        self.on_save = on_save
        self.entries = {}
        self.current_file = None
        
        self.api = get_api()

        # 复用 ScrollableFrame（规则 5.3）
        from .scrollable import ScrollableFrame
        self._scroll = ScrollableFrame(self)
        self._scroll.pack(fill=tk.BOTH, expand=True)
        self.scrollable_frame = self._scroll.scrollable_frame

    def load_metadata(self, metadata: dict):
        """加载元信息到编辑器"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.entries.clear()

        self.current_file = metadata.get('filepath')
        
        editable_fields = self.api.get_editable_fields(self.current_file)
        
        format_info = editable_fields.get('_format_info', {})
        self._show_format_info(format_info)
        
        row = 0
        
        basic_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'basic'}
        if basic_fields:
            row = self._add_field_group("基本信息", basic_fields, row)
        
        time_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'time'}
        if time_fields:
            row = self._add_field_group("时间信息", time_fields, row)
        
        xmp_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'xmp'}
        if xmp_fields:
            row = self._add_field_group("XMP信息", xmp_fields, row)
        
        exif_fields = {k: v for k, v in editable_fields.items() if v.get('category') == 'exif'}
        if exif_fields:
            row = self._add_field_group("EXIF信息", exif_fields, row)
        
        if self.on_save:
            tk.Button(
                self.scrollable_frame,
                text='保存修改',
                command=self._on_save
            ).grid(row=row, column=0, columnspan=2, pady=10)
    
    def _show_format_info(self, format_info: dict):
        format_name = format_info.get('format', 'Unknown')
        supports_exif = format_info.get('supports_exif', False)
        supports_xmp = format_info.get('supports_xmp', False)
        needs_exiftool = format_info.get('needs_exiftool', False)
        
        info_frame = ttk.LabelFrame(self.scrollable_frame, text="格式信息")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E, padx=5, pady=5)
        
        tk.Label(
            info_frame,
            text=f"格式: {format_name}",
            font=('Arial', 9, 'bold'),
            anchor=tk.W
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        supports = []
        if supports_exif:
            supports.append("EXIF")
        if supports_xmp:
            supports.append("XMP")
        if needs_exiftool:
            supports.append("需要ExifTool")
        
        support_text = "支持: " + ", ".join(supports) if supports else "不支持元数据编辑"
        tk.Label(info_frame, text=support_text, anchor=tk.W
                ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
    
    def _add_field_group(self, group_name: str, fields: dict, start_row: int) -> int:
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
            placeholder = FIELD_PLACEHOLDERS.get(field_name, '')
            
            if editable:
                label_fg = '#000000'
            else:
                label_fg = '#888888'
            
            tk.Label(
                self.scrollable_frame,
                text=f"{label}:",
                font=('Arial', 9),
                anchor=tk.W,
                fg=label_fg
            ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
            
            if editable and placeholder:
                # 可编辑 + 有格式提示 → PlaceholderEntry
                entry = PlaceholderEntry(
                    self.scrollable_frame, width=40,
                    placeholder=placeholder
                )
                entry.set_value(value)
            elif editable:
                # 可编辑但无格式提示 → 普通 Entry
                entry = tk.Entry(self.scrollable_frame, width=40)
                entry.insert(0, str(value))
            else:
                # 只读字段
                entry = tk.Entry(self.scrollable_frame, width=40,
                               state='disabled', bg='#F0F0F0')
                entry.insert(0, str(value))
            
            entry.grid(row=row, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
            self.entries[field_name] = entry
            
            row += 1
        
        return row

    def _on_save(self):
        if not self.on_save or not self.current_file:
            return

        metadata = {}
        for field, entry in self.entries.items():
            if isinstance(entry, PlaceholderEntry):
                value = entry.get_real_value()
            else:
                value = entry.get().strip()
            if value:
                metadata[field] = value

        self.on_save(self.current_file, metadata)

    def get_editable_metadata(self) -> dict:
        metadata = {}
        for field, entry in self.entries.items():
            if isinstance(entry, PlaceholderEntry):
                value = entry.get_real_value()
            else:
                value = entry.get().strip()
            if value:
                metadata[field] = value
        return metadata
