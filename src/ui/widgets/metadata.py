"""
King_photo - 元数据编辑组件
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable

from ...api import get_api

logger = logging.getLogger(__name__)


class MetadataEditorWidget(tk.Frame):
    """元信息编辑组件"""

    def __init__(self, master, on_save: Callable = None, **kwargs):
        super().__init__(master, **kwargs)

        self.on_save = on_save
        self.entries = {}
        self.current_file = None
        
        self.api = get_api()

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

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
            
            if editable:
                label_fg = '#000000'
                entry_state = 'normal'
                entry_bg = '#FFFFFF'
            else:
                label_fg = '#888888'
                entry_state = 'disabled'
                entry_bg = '#F0F0F0'
            
            tk.Label(
                self.scrollable_frame,
                text=f"{label}:",
                font=('Arial', 9),
                anchor=tk.W,
                fg=label_fg
            ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
            
            if editable:
                entry = tk.Entry(self.scrollable_frame, width=40)
                entry.insert(0, str(value))
                entry.grid(row=row, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
                self.entries[field_name] = entry
            else:
                entry = tk.Entry(self.scrollable_frame, width=40, state=entry_state, bg=entry_bg)
                entry.insert(0, str(value))
                entry.grid(row=row, column=1, sticky=tk.W + tk.E, padx=5, pady=2)
            
            row += 1
        
        return row

    def _on_save(self):
        if not self.on_save or not self.current_file:
            return

        metadata = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if value:
                metadata[field] = value

        self.on_save(self.current_file, metadata)

    def get_editable_metadata(self) -> dict:
        metadata = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if value:
                metadata[field] = value
        return metadata
