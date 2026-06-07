"""
King_photo - 插件管理对话框
管理已安装插件的启用/禁用状态
"""

import logging
import tkinter as tk
from typing import Dict, List, Any

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from .widgets.scrollable import ScrollableFrame

logger = logging.getLogger(__name__)


class PluginManagerDialog(tk.Toplevel):
    """插件管理对话框"""

    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api
        self.plugins_data: List[Dict[str, Any]] = []
        self._plugin_frames: Dict[str, tk.Frame] = {}

        # 窗口设置
        self.title("插件管理 — King_photo")
        self.geometry("800x600")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()

        # 居中
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 800) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 600) // 2
        self.geometry(f"+{x}+{y}")

        self._create_widgets()
        self._load_plugins()

    # ============================================================
    # UI 构建
    # ============================================================
    def _create_widgets(self):
        """创建界面组件"""
        # 顶部标题栏
        header = ttk.Frame(self, padding=(15, 10))
        header.pack(fill=tk.X)

        ttk.Label(
            header, text="🔌 插件管理",
            font=("Microsoft YaHei", 16, "bold")
        ).pack(side=tk.LEFT)

        # 统计信息
        self._stats_label = ttk.Label(
            header, text="",
            font=("Microsoft YaHei", 10),
            foreground="gray"
        )
        self._stats_label.pack(side=tk.RIGHT, padx=10)

        # 刷新按钮
        btn_refresh = ttk.Button(
            header, text="🔄 刷新",
            command=self._load_plugins,
            bootstyle=(OUTLINE, SECONDARY)
        )
        btn_refresh.pack(side=tk.RIGHT, padx=5)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        # 可滚动内容区域
        self._scroll = ScrollableFrame(self)
        self._scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 底部按钮
        footer = ttk.Frame(self, padding=(15, 10))
        footer.pack(fill=tk.X)

        ttk.Button(
            footer, text="关闭",
            command=self.destroy,
            bootstyle=SECONDARY
        ).pack(side=tk.RIGHT)

        ttk.Button(
            footer, text="🧹 清理残留",
            command=self._cleanup_config,
            bootstyle=(OUTLINE, WARNING)
        ).pack(side=tk.RIGHT, padx=5)

    # ============================================================
    # 数据加载
    # ============================================================
    def _load_plugins(self):
        """加载插件数据"""
        # 清除旧内容
        for widget in self._scroll.scrollable_frame.winfo_children():
            widget.destroy()
        self._plugin_frames.clear()

        # 从 API 获取
        try:
            self.plugins_data = self.api.get_all_plugin_info()
        except Exception as e:
            logger.error(f"加载插件信息失败: {e}")
            ttk.Label(
                self._scroll.scrollable_frame,
                text=f"❌ 加载失败: {e}",
                font=("Microsoft YaHei", 11),
                foreground="red"
            ).pack(pady=20)
            return

        if not self.plugins_data:
            ttk.Label(
                self._scroll.scrollable_frame,
                text="📦 暂无已注册的插件",
                font=("Microsoft YaHei", 11),
                foreground="gray"
            ).pack(pady=40)
            self._update_stats()
            return

        # 分组显示
        type_groups = self._group_by_type()
        for type_key, (type_label, plugins) in type_groups.items():
            self._create_type_section(type_label, plugins)

        self._update_stats()

    def _group_by_type(self):
        """按类型分组插件"""
        type_config = {
            "format":   ("📷 格式插件",   []),
            "function": ("⚙️ 功能插件",   []),
            "extension":("🔗 扩展插件",   []),
            "unknown":  ("❓ 未知类型",   []),
        }
        for p in self.plugins_data:
            t = p.get("type", "unknown")
            if t in type_config:
                type_config[t][1].append(p)
            else:
                type_config["unknown"][1].append(p)
        # 去掉空分组
        return {k: v for k, v in type_config.items() if v[1]}

    def _create_type_section(self, label: str, plugins: list):
        """创建一种类型的分组标题和插件列表"""
        parent = self._scroll.scrollable_frame

        # 分组标题
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=10, pady=(15, 5))

        ttk.Label(
            header_frame, text=label,
            font=("Microsoft YaHei", 12, "bold")
        ).pack(side=tk.LEFT)

        ttk.Label(
            header_frame,
            text=f"({len(plugins)} 个)",
            font=("Microsoft YaHei", 10),
            foreground="gray"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        # 插件卡片
        for plugin in plugins:
            self._create_plugin_card(parent, plugin)

    def _create_plugin_card(self, parent, plugin: dict):
        """创建单个插件卡片"""
        name = plugin.get("name", "?")
        enabled = plugin.get("enabled", True)
        description = plugin.get("description", "")
        version = plugin.get("version", "—")
        author = plugin.get("author", "—")
        ptype = plugin.get("type", "unknown")

        # 卡片容器
        card = ttk.Frame(parent, padding=10)
        card.pack(fill=tk.X, padx=10, pady=3)

        # 左侧状态指示
        status_color = "success" if enabled else "secondary"
        status_text = "启用" if enabled else "禁用"

        status_dot = tk.Canvas(card, width=12, height=12, highlightthickness=0)
        status_dot.pack(side=tk.LEFT, padx=(0, 10))
        self._draw_dot(status_dot, enabled)
        # 存储引用防止 GC
        card._status_dot = status_dot

        # 中间信息区
        info_frame = ttk.Frame(card)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 名称行
        name_row = ttk.Frame(info_frame)
        name_row.pack(fill=tk.X)

        ttk.Label(
            name_row, text=name,
            font=("Microsoft YaHei", 11, "bold")
        ).pack(side=tk.LEFT)

        # 类型标签
        type_labels = {
            "format": "格式", "function": "功能",
            "extension": "扩展", "unknown": "未知"
        }
        type_tag = ttk.Label(
            name_row,
            text=type_labels.get(ptype, ptype),
            font=("Microsoft YaHei", 8),
            padding=(6, 2),
            bootstyle=SECONDARY
        )
        type_tag.pack(side=tk.LEFT, padx=8)

        # 状态标签
        status_tag = ttk.Label(
            name_row, text=status_text,
            font=("Microsoft YaHei", 8),
            padding=(6, 2),
            bootstyle=SUCCESS if enabled else SECONDARY
        )
        status_tag.pack(side=tk.LEFT)
        card._status_tag = status_tag

        # 描述
        if description:
            ttk.Label(
                info_frame, text=description,
                font=("Microsoft YaHei", 9),
                foreground="gray",
                wraplength=500, justify=tk.LEFT
            ).pack(anchor=tk.W, pady=(2, 0))

        # 元信息行
        meta_frame = ttk.Frame(info_frame)
        meta_frame.pack(fill=tk.X, pady=(2, 0))

        meta_parts = []
        if version and version != "—":
            meta_parts.append(f"v{version}")
        if author and author != "—":
            meta_parts.append(author)

        # 额外信息
        extra = plugin.get("extra", {})
        if ptype == "format" and extra.get("extensions"):
            meta_parts.append(", ".join(extra["extensions"]))
        if ptype == "extension" and extra.get("target_module"):
            meta_parts.append(f"目标: {extra['target_module']}")

        if meta_parts:
            ttk.Label(
                meta_frame, text=" · ".join(meta_parts),
                font=("Microsoft YaHei", 8),
                foreground="gray"
            ).pack(side=tk.LEFT)

        # 右侧按钮区
        btn_frame = ttk.Frame(card)
        btn_frame.pack(side=tk.RIGHT, padx=(10, 0))

        # 功能插件：运行按钮
        if ptype == "function" and enabled:
            run_btn = ttk.Button(
                btn_frame, text="▶ 运行", width=6,
                bootstyle=SUCCESS,
                command=lambda n=name: self._run_plugin(n)
            )
            run_btn.pack(side=tk.RIGHT, padx=(5, 0))
            card._run_btn = run_btn

        # 启用/禁用按钮
        if enabled:
            btn_text = "禁用"
            btn_style = (OUTLINE, DANGER)
            new_state = False
        else:
            btn_text = "启用"
            btn_style = (OUTLINE, SUCCESS)
            new_state = True

        toggle_btn = ttk.Button(
            btn_frame, text=btn_text, width=6,
            bootstyle=btn_style,
            command=lambda n=name, ns=new_state, c=card, b=None: self._toggle_plugin(n, ns, c, b)
        )
        toggle_btn.pack(side=tk.RIGHT, padx=(5, 0))
        card._toggle_btn = toggle_btn

        # 扩展插件：自动触发开关
        if ptype == "extension":
            auto_var = tk.BooleanVar(value=plugin.get("enabled", True))
            auto_cb = ttk.Checkbutton(
                btn_frame, text="自动触发", variable=auto_var,
                command=lambda n=name, v=auto_var: self._toggle_auto_trigger(n, v)
            )
            auto_cb.pack(side=tk.RIGHT, padx=(10, 0))
            card._auto_var = auto_var

        # 存储引用
        card._plugin_name = name
        card._plugin_enabled = enabled
        self._plugin_frames[name] = card

    def _draw_dot(self, canvas: tk.Canvas, enabled: bool):
        """绘制状态圆点"""
        color = "#28a745" if enabled else "#6c757d"
        canvas.delete("all")
        canvas.create_oval(1, 1, 11, 11, fill=color, outline="")

    # ============================================================
    # 操作
    # ============================================================
    def _toggle_plugin(self, name: str, new_state: bool, card: tk.Frame, btn):
        """切换插件启用/禁用状态"""
        try:
            if new_state:
                success = self.api.enable_plugin(name)
            else:
                success = self.api.disable_plugin(name)
        except Exception as e:
            logger.error(f"切换插件状态失败: {name}, {e}")
            return

        if success:
            # 更新数据
            for p in self.plugins_data:
                if p["name"] == name:
                    p["enabled"] = new_state
                    break

            # 更新卡片 UI
            if hasattr(card, '_status_dot'):
                self._draw_dot(card._status_dot, new_state)

            if hasattr(card, '_status_tag'):
                tag = card._status_tag
                tag.config(
                    text="启用" if new_state else "禁用",
                    bootstyle=SUCCESS if new_state else SECONDARY
                )

            if hasattr(card, '_toggle_btn'):
                btn = card._toggle_btn
                if new_state:
                    btn.config(text="禁用", bootstyle=(OUTLINE, DANGER))
                else:
                    btn.config(text="启用", bootstyle=(OUTLINE, SUCCESS))

            card._plugin_enabled = new_state
            self._update_stats()

            action = "启用" if new_state else "禁用"
            logger.info(f"插件 {action}: {name}")

    def _update_stats(self):
        """更新统计信息"""
        total = len(self.plugins_data)
        enabled_count = sum(1 for p in self.plugins_data if p.get("enabled", False))
        self._stats_label.config(
            text=f"共 {total} 个插件，已启用 {enabled_count} 个"
        )

    def _run_plugin(self, plugin_name: str):
        """在插件管理对话框中直接运行功能插件"""
        from tkinter import messagebox

        # 获取主窗口引用
        main = self.master
        # 查找 MainWindow（如果是 ttk.Window 则在其下方）
        if hasattr(main, 'folder_view'):
            selected = main.folder_view.get_selected_files()
        else:
            messagebox.showinfo("提示", "请先在主窗口中打开文件夹并选中图片", parent=self)
            return

        if not selected:
            messagebox.showinfo("提示", "请先在文件夹中选中要处理的图片", parent=self)
            return

        from .generic_plugin_dialog import GenericPluginDialog
        GenericPluginDialog(self, self.api, plugin_name, selected)

    def _toggle_auto_trigger(self, name: str, var: tk.BooleanVar):
        """切换扩展插件的自动触发状态"""
        auto = var.get()
        logger.info(f"扩展插件自动触发: {name} → {auto}")
        # 存储到 plugin_config
        try:
            self.api._plugin_manager._plugin_configs.setdefault(name, {})["auto_trigger"] = auto
            self.api._plugin_manager._save_plugin_config()
        except Exception as e:
            logger.warning(f"保存自动触发配置失败: {e}")

    def _cleanup_config(self):
        """清理配置残留"""
        from tkinter import messagebox
        orphans = [p for p in self.plugins_data if p.get("type") == "unknown"]
        if not orphans:
            messagebox.showinfo("清理完成", "没有配置残留需要清理。", parent=self)
            return

        names = [p["name"] for p in orphans]
        if messagebox.askyesno(
            "清理残留",
            f"将移除以下 {len(names)} 个配置残留：\n\n" + "\n".join(f"  - {n}" for n in names),
            parent=self
        ):
            for name in names:
                self.api._plugin_manager._plugin_configs.pop(name, None)
            self.api._plugin_manager._save_plugin_config()
            self._load_plugins()

    def destroy(self):
        """关闭时通知主窗口刷新菜单"""
        try:
            main = self.master
            if hasattr(main, '_refresh_function_plugin_menu'):
                main._refresh_function_plugin_menu()
        except Exception:
            logger.debug("通知主窗口刷新菜单失败", exc_info=True)
        super().destroy()
