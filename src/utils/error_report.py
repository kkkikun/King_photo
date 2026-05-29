"""
King_photo - 错误报告模块
提供错误汇总和导出功能
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# 获取日志记录器
logger = logging.getLogger(__name__)


class ErrorReport:
    """错误报告"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.operation_name = ""
        self.start_time = None
        self.end_time = None

    def start(self, operation_name: str):
        """开始记录"""
        self.operation_name = operation_name
        self.start_time = datetime.now()
        self.errors = []
        self.warnings = []

    def add_error(self, file_path: str, error_message: str, details: str = ""):
        """添加错误"""
        self.errors.append({
            'file': file_path,
            'message': error_message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def add_warning(self, file_path: str, warning_message: str, details: str = ""):
        """添加警告"""
        self.warnings.append({
            'file': file_path,
            'message': warning_message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def finish(self):
        """完成记录"""
        self.end_time = datetime.now()

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            'operation': self.operation_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
        }

    def generate_text_report(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"King_photo 错误报告")
        lines.append("=" * 60)
        lines.append("")

        # 摘要信息
        summary = self.get_summary()
        lines.append(f"操作: {summary['operation']}")
        lines.append(f"开始时间: {summary['start_time']}")
        lines.append(f"结束时间: {summary['end_time']}")
        if summary['duration_seconds'] is not None:
            lines.append(f"耗时: {summary['duration_seconds']:.2f} 秒")
        lines.append(f"错误数量: {summary['error_count']}")
        lines.append(f"警告数量: {summary['warning_count']}")
        lines.append("")

        # 错误详情
        if self.errors:
            lines.append("-" * 60)
            lines.append("错误详情:")
            lines.append("-" * 60)
            for i, error in enumerate(self.errors, 1):
                lines.append(f"\n{i}. 文件: {os.path.basename(error['file'])}")
                lines.append(f"   路径: {error['file']}")
                lines.append(f"   错误: {error['message']}")
                if error['details']:
                    lines.append(f"   详情: {error['details']}")
            lines.append("")

        # 警告详情
        if self.warnings:
            lines.append("-" * 60)
            lines.append("警告详情:")
            lines.append("-" * 60)
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"\n{i}. 文件: {os.path.basename(warning['file'])}")
                lines.append(f"   路径: {warning['file']}")
                lines.append(f"   警告: {warning['message']}")
                if warning['details']:
                    lines.append(f"   详情: {warning['details']}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("报告生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        lines.append("=" * 60)

        return "\n".join(lines)

    def export_to_file(self, file_path: str) -> bool:
        """
        导出报告到文件

        Args:
            file_path: 文件路径

        Returns:
            是否导出成功
        """
        try:
            report = self.generate_text_report()

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"错误报告已导出: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出错误报告失败: {str(e)}")
            return False


def generate_error_report_from_batch_result(
    result: Dict[str, Any],
    operation_name: str
) -> ErrorReport:
    """
    从批量操作结果生成错误报告

    Args:
        result: 批量操作结果
        operation_name: 操作名称

    Returns:
        错误报告对象
    """
    report = ErrorReport()
    report.start(operation_name)

    # 处理不同格式的结果
    if 'details' in result:
        for detail in result['details']:
            file_path = detail.get('file', '未知')
            file_result = detail.get('result', {})

            if not file_result.get('success', False):
                report.add_error(
                    file_path,
                    file_result.get('message', '未知错误')
                )
            elif file_result.get('skipped', False):
                report.add_warning(
                    file_path,
                    file_result.get('message', '已跳过')
                )

    if 'errors' in result:
        for error in result['errors']:
            report.add_error(
                error.get('file', '未知'),
                error.get('message', '未知错误')
            )

    report.finish()
    return report


def show_error_report_dialog(parent, report: ErrorReport):
    """
    显示错误报告对话框

    Args:
        parent: 父窗口
        report: 错误报告对象
    """
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    if not report.has_errors() and not report.has_warnings():
        messagebox.showinfo("完成", "操作完成，没有错误或警告。")
        return

    # 创建对话框
    dialog = tk.Toplevel(parent)
    dialog.title("错误报告")
    dialog.transient(parent)
    dialog.grab_set()

    # 居中显示
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    window_width = min(600, int(screen_width * 0.5))
    window_height = min(400, int(screen_height * 0.5))
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # 摘要标签
    summary = report.get_summary()
    summary_text = f"操作: {summary['operation']}\n"
    summary_text += f"错误: {summary['error_count']}  警告: {summary['warning_count']}"

    ttk.Label(
        dialog,
        text=summary_text,
        font=('Arial', 10, 'bold')
    ).pack(pady=10)

    # 报告文本框
    text_frame = ttk.Frame(dialog)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    text_widget = tk.Text(text_frame, wrap=tk.WORD)
    scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)

    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 插入报告内容
    report_text = report.generate_text_report()
    text_widget.insert(1.0, report_text)
    text_widget.configure(state='disabled')

    # 按钮框架
    button_frame = ttk.Frame(dialog)
    button_frame.pack(fill=tk.X, padx=10, pady=10)

    def export_report():
        """导出报告"""
        file_path = filedialog.asksaveasfilename(
            title="导出错误报告",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if file_path:
            if report.export_to_file(file_path):
                messagebox.showinfo("成功", f"报告已导出到:\n{file_path}")

    ttk.Button(
        button_frame,
        text="导出报告",
        command=export_report,
        width=12
    ).pack(side=tk.LEFT, padx=5)

    ttk.Button(
        button_frame,
        text="关闭",
        command=dialog.destroy,
        width=10
    ).pack(side=tk.RIGHT, padx=5)