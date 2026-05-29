"""
King_photo - 单图片模式视图
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from .widgets import ImagePreviewWidget, MetadataEditorWidget
from ..core.metadata_reader import MetadataReader
from ..core.metadata_writer import MetadataWriter
from ..core.repair_engine import RepairEngine
from ..utils.helpers import format_file_size, format_datetime


class SingleView(ttk.Frame):
    """单图片模式视图"""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)

        self.app = app
        self.current_file = None

        self._create_ui()

    def _create_ui(self):
        """创建UI"""
        # 主分割面板
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 左侧：图片预览
        left_frame = ttk.LabelFrame(self.paned, text="图片预览")
        self.paned.add(left_frame, weight=1)

        self.preview = ImagePreviewWidget(left_frame, max_size=(500, 500))
        self.preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 右侧：元信息编辑
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=1)

        # 工具栏
        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(toolbar, text="保存修改", command=self._save_metadata).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="修复", command=self._full_repair).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="恢复", command=self._restore).pack(side=tk.LEFT, padx=2)

        # 元信息编辑器
        self.editor = MetadataEditorWidget(right_frame, on_save=self._on_save_metadata)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 状态信息
        status_frame = ttk.LabelFrame(right_frame, text="状态")
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_text = tk.Text(status_frame, height=4, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 绑定滚轮到整个右侧区域
        self._bind_mousewheel(right_frame)

    def _bind_mousewheel(self, widget):
        """绑定鼠标滚轮到组件及其子组件"""
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_mousewheel(child)

    def _on_mousewheel(self, event):
        """鼠标滚轮事件"""
        # 滚动元信息编辑器
        self.editor.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def show(self):
        """显示视图"""
        self.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """隐藏视图"""
        self.pack_forget()

    def load_image(self, filepath: str):
        """加载图片"""
        self.current_file = filepath

        # 加载预览
        self.preview.load_image(filepath)

        # 加载元信息
        metadata = MetadataReader.read_metadata(filepath)
        self.editor.load_metadata(metadata)

        # 显示状态
        self._update_status(metadata)

    def _update_status(self, metadata: dict):
        """更新状态显示"""
        self.status_text.delete(1.0, tk.END)

        status = f"文件: {metadata.get('filename', '')}\n"
        status += f"格式: {metadata.get('format', 'Unknown')}\n"

        if not metadata.get('is_consistent', True):
            status += "⚠️ 警告: 文件后缀与实际格式不一致\n"

        if metadata.get('datetime'):
            status += f"拍摄时间: {format_datetime(metadata['datetime'])}\n"
        else:
            status += "⚠️ 未找到拍摄时间信息\n"

        self.status_text.insert(1.0, status)

    def _save_metadata(self):
        """保存元信息"""
        if not self.current_file:
            messagebox.showinfo("提示", "请先加载图片")
            return

        metadata = self.editor.get_editable_metadata()
        if not metadata:
            messagebox.showinfo("提示", "没有可保存的修改")
            return

        # 确认对话框
        output_dir = self.app.output_dir
        copy_mode = output_dir is not None

        if copy_mode:
            message = f"将保存到: {output_dir}\n确定保存吗？"
        else:
            message = "将直接修改原文件\n确定保存吗？"

        if not messagebox.askyesno("确认", message):
            return

        # 执行保存
        result = MetadataWriter.write_metadata(
            self.current_file,
            metadata,
            copy_mode=copy_mode,
            output_dir=output_dir
        )

        if result['success']:
            messagebox.showinfo("成功", result['message'])
            # 重新加载
            self.load_image(result.get('output_path', self.current_file))
        else:
            messagebox.showerror("失败", result['message'])

    def _on_save_metadata(self, filepath: str, metadata: dict):
        """保存元信息回调"""
        self._save_metadata()

    def _full_repair(self):
        """完整修复"""
        if not self.current_file:
            messagebox.showinfo("提示", "请先加载图片")
            return

        output_dir = self.app.output_dir
        original_path = self.current_file

        # 确认对话框
        if not messagebox.askyesno("确认", "将执行完整修复（后缀修复 + 时间修复）\n\n请在操作前备份重要数据\n确定继续吗？"):
            return

        result = RepairEngine.repair(
            original_path,
            output_dir=output_dir,
            fix_extension=True,
            fix_time=True
        )

        if result['success']:
            messagebox.showinfo("成功", result['message'])
            # 加载修复后的文件
            self.current_file = result['output_path']
            self.load_image(result['output_path'])
        else:
            # 显示详细结果
            details = result['details']
            message = f"修复结果:\n\n"

            if details.get('extension'):
                ext = details['extension']
                message += f"后缀修复: {'成功' if ext['success'] else '跳过' if ext.get('skipped') else '失败'}\n"
                if not ext['success'] and not ext.get('skipped'):
                    message += f"  原因: {ext.get('message', '未知')}\n"

            if details.get('time'):
                t = details['time']
                message += f"时间修复: {'成功' if t['success'] else '失败'}\n"
                if not t['success']:
                    message += f"  原因: {t.get('message', '未知')}\n"

            messagebox.showinfo("完成", message)

    def _restore(self):
        """提示用户手动恢复"""
        if not self.current_file:
            messagebox.showinfo("提示", "请先加载图片")
            return

        # 提示用户手动恢复
        messagebox.showinfo(
            "恢复提示",
            "当前版本已移除自动备份功能\n\n"
            "如需恢复文件，请：\n"
            "1. 检查是否有其他备份副本\n"
            "2. 使用系统还原点恢复\n"
            "3. 从回收站恢复删除的文件\n\n"
            "建议在操作前手动备份重要文件"
        )
