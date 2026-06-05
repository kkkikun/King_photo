"""
King_photo - 通用功能插件执行对话框
根据插件 get_parameters() 动态生成参数表单，执行插件
"""

import logging
import threading
import tkinter as tk
import tkinter.messagebox as messagebox
from typing import Dict, Any, List

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .widgets.progress import ProgressDialog

logger = logging.getLogger(__name__)


class GenericPluginDialog(tk.Toplevel):
    """通用功能插件执行对话框
    
    完全由 IFunctionPlugin.get_parameters() 驱动，无需预知任何插件名。
    支持参数类型：str, int, bool
    """

    # 参数类型 → 控件构建器映射
    _WIDGET_BUILDERS = {}

    def __init__(self, parent, api, plugin_name: str, selected_files: List[str]):
        super().__init__(parent)

        self.api = api
        self.plugin_name = plugin_name
        self.selected_files = selected_files

        # 获取插件实例
        self._plugin = self.api._plugin_manager.get_function_plugin(plugin_name)
        if self._plugin is None:
            messagebox.showerror("错误", f"插件不存在: {plugin_name}")
            self.destroy()
            return

        # 读取参数定义
        self._params_def = self._plugin.get_parameters()
        self._param_widgets: Dict[str, Dict[str, Any]] = {}  # name → {var, widget, ...}

        # 窗口设置
        self.title(f"{self._plugin.plugin_name} — King_photo")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        # 计算窗口高度（参数越多越高）
        rows = len(self._params_def) if self._params_def else 1
        win_h = min(max(200, 160 + rows * 70), 600)
        self.geometry(f"550x{win_h}")

        # 居中
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 550) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - win_h) // 2
        self.geometry(f"+{x}+{y}")

        self._create_widgets()

        # 绑定回车键提交
        self.bind("<Return>", lambda e: self._on_execute())

    # ============================================================
    # UI 构建
    # ============================================================
    def _create_widgets(self):
        """动态生成参数表单"""
        # 标题区
        header = ttk.Frame(self, padding=(15, 10))
        header.pack(fill=tk.X)

        ttk.Label(
            header,
            text=f"⚙️ {self._plugin.plugin_name}",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor=tk.W)

        desc = self._plugin.description
        if desc:
            ttk.Label(
                header, text=desc,
                font=("Microsoft YaHei", 9),
                foreground="gray", wraplength=500, justify=tk.LEFT
            ).pack(anchor=tk.W, pady=(3, 0))

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(5, 10))

        # 参数表单区
        self._form_frame = ttk.Frame(self, padding=(15, 5))
        self._form_frame.pack(fill=tk.BOTH, expand=True)

        if not self._params_def:
            # 无参数插件
            ttk.Label(
                self._form_frame,
                text="此插件无需额外参数，直接点击执行。",
                font=("Microsoft YaHei", 10),
                foreground="gray"
            ).pack(pady=20)
        else:
            for param_name, param_def in self._params_def.items():
                self._build_param_row(param_name, param_def)

        # 底部按钮
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)
        btn_frame = ttk.Frame(self, padding=(15, 10))
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame, text="取消",
            command=self.destroy,
            bootstyle=SECONDARY
        ).pack(side=tk.RIGHT, padx=5)

        self._exec_btn = ttk.Button(
            btn_frame, text="▶ 执行",
            command=self._on_execute,
            bootstyle=SUCCESS
        )
        self._exec_btn.pack(side=tk.RIGHT, padx=5)

        # 文件提示
        ttk.Label(
            btn_frame,
            text=f"已选中 {len(self.selected_files)} 个文件",
            font=("Microsoft YaHei", 9),
            foreground="gray"
        ).pack(side=tk.LEFT)

    def _build_param_row(self, name: str, param_def: Dict[str, Any]):
        """为单个参数构建一行表单控件"""
        ptype = param_def.get("type", "str")
        default = param_def.get("default")
        required = param_def.get("required", False)
        desc = param_def.get("description", "")

        # 行容器
        row = ttk.Frame(self._form_frame)
        row.pack(fill=tk.X, pady=3)

        # 标签：参数名 + 必填标 *
        label_text = name
        if required:
            label_text += " *"
        lbl = ttk.Label(row, text=label_text, font=("Microsoft YaHei", 10), width=16, anchor=tk.E)
        lbl.pack(side=tk.LEFT, padx=(0, 8))

        # 控件
        widget_frame = ttk.Frame(row)
        widget_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if ptype == "bool":
            var = tk.BooleanVar(value=bool(default) if default is not None else False)
            cb = ttk.Checkbutton(widget_frame, variable=var, text="启用")
            cb.pack(side=tk.LEFT)
            self._param_widgets[name] = {"var": var, "widget": cb, "type": "bool"}

        elif ptype == "int":
            var = tk.StringVar(value=str(default) if default is not None else "0")
            sp = ttk.Spinbox(widget_frame, from_=0, to=10000, textvariable=var, width=10)
            sp.pack(side=tk.LEFT)
            self._param_widgets[name] = {"var": var, "widget": sp, "type": "int"}

        else:  # str 和其他类型
            var = tk.StringVar(value=str(default) if default is not None else "")
            entry = ttk.Entry(widget_frame, textvariable=var, width=40)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._param_widgets[name] = {"var": var, "widget": entry, "type": "str"}

        # 参数描述
        if desc:
            desc_label = ttk.Label(
                self._form_frame, text=f"        {desc}",
                font=("Microsoft YaHei", 8),
                foreground="gray", wraplength=480, justify=tk.LEFT
            )
            desc_label.pack(anchor=tk.W)

    # ============================================================
    # 参数收集与校验
    # ============================================================
    def _collect_params(self) -> Dict[str, Any]:
        """从表单收集所有参数值"""
        params = {}
        for name, pw in self._param_widgets.items():
            val = pw["var"].get()
            if pw["type"] == "int":
                try:
                    params[name] = int(val)
                except (ValueError, TypeError):
                    params[name] = 0
            elif pw["type"] == "bool":
                params[name] = bool(val)
            else:
                # 空字符串 → None
                params[name] = val if val else None
        return params

    def _validate(self) -> tuple:
        """校验参数，返回 (ok, message)"""
        for name, param_def in self._params_def.items():
            if param_def.get("required", False):
                pw = self._param_widgets.get(name)
                if pw:
                    val = pw["var"].get()
                    if not val:
                        return False, f"参数 '{name}' 为必填项"
            if param_def.get("type") == "int":
                pw = self._param_widgets.get(name)
                if pw:
                    try:
                        int(pw["var"].get())
                    except (ValueError, TypeError):
                        return False, f"参数 '{name}' 必须是整数"
        return True, ""

    # ============================================================
    # 执行
    # ============================================================
    def _on_execute(self):
        """收集参数并执行插件"""
        # 校验
        ok, msg = self._validate()
        if not ok:
            messagebox.showwarning("参数校验", msg, parent=self)
            return

        params = self._collect_params()

        # 确认（无参数时也确认）
        if not self._params_def:
            if not messagebox.askyesno(
                "确认执行",
                f"确定要对 {len(self.selected_files)} 个文件执行"
                f"「{self._plugin.plugin_name}」吗？",
                parent=self
            ):
                return

        # 禁用按钮防止重复点击
        self._exec_btn.config(state=tk.DISABLED, text="执行中...")

        # 后台执行
        progress_dialog = ProgressDialog(self, title=f"{self._plugin.plugin_name}中...")
        cancel_flag = threading.Event()
        progress_dialog.set_cancel_callback(lambda: cancel_flag.set())

        def run():
            try:
                result = self._plugin.execute(
                    self.selected_files,
                    **params
                )
                if cancel_flag.is_set():
                    self.after(0, lambda: messagebox.showinfo(
                        "已取消", f"「{self._plugin.plugin_name}」已取消"))
                else:
                    self.after(0, lambda: self._on_done(result))
            except Exception as e:
                logger.error(f"插件执行失败 [{self.plugin_name}]: {e}")
                self.after(0, lambda: messagebox.showerror(
                    "执行失败", f"插件执行出错:\n{str(e)}"))
            finally:
                self.after(0, self._on_finish)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _on_done(self, result: Dict[str, Any]):
        """执行完成"""
        success = result.get("success", 0) if isinstance(result, dict) else 0
        failed = result.get("failed", 0) if isinstance(result, dict) else 0
        total = result.get("total", len(self.selected_files))

        msg = f"「{self._plugin.plugin_name}」执行完成\n\n"
        msg += f"成功: {success}\n失败: {failed}\n总计: {total}"
        messagebox.showinfo("完成", msg)

        # 刷新文件夹视图
        if hasattr(self, 'api'):
            try:
                self.api._ensure_initialized()
            except Exception:
                pass

    def _on_finish(self):
        """无论成功失败，清理"""
        try:
            if hasattr(self, '_exec_btn') and self._exec_btn.winfo_exists():
                self._exec_btn.config(state=tk.NORMAL, text="▶ 执行")
        except Exception:
            pass
        self.destroy()
