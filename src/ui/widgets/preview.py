"""
King_photo - 图片预览组件（默认适配窗口 + 自由缩放 + 拖拽平移）
"""
import logging
import tkinter as tk

import ttkbootstrap as ttk
from PIL import Image, ImageTk

from ...utils.image_loader import load_image

logger = logging.getLogger(__name__)


class ImagePreviewWidget(tk.Frame):
    """图片预览 — 默认适配窗口，自由缩放拖拽"""

    def __init__(self, master, max_size: tuple = (600, 500), **kwargs):
        super().__init__(master, **kwargs)

        self.max_size = max_size
        self._original_image = None
        self._fit_ratio = 1.0     # 适配窗口时的缩放比
        self._zoom_level = 1.0    # 当前缩放（1.0 = 适配窗口）
        self._free_zoom = False
        self._offset_x = 0
        self._offset_y = 0
        self._drag_start = None

        # --- Toolbar ---
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        self.btn_zoom = ttk.Button(toolbar, text="自由缩放", command=self._toggle_zoom,
                                    bootstyle="secondary-outline", width=10)
        self.btn_zoom.pack(side=tk.LEFT, padx=2)
        self.btn_reset = ttk.Button(toolbar, text="重置", command=self._reset,
                                     bootstyle="secondary-outline", width=6)
        self.btn_reset.pack(side=tk.LEFT, padx=2)
        self.zoom_label = ttk.Label(toolbar, text="适配", width=8, anchor=tk.CENTER)
        self.zoom_label.pack(side=tk.RIGHT, padx=5)

        # --- Preview label ---
        self.preview_label = tk.Label(self, text='Select image to preview',
                                       bg='#2b2b2b', fg='#888888', cursor="cross")
        self.preview_label.pack(expand=True, fill=tk.BOTH)

        # Bind events
        self.preview_label.bind("<MouseWheel>", self._on_zoom)
        self.preview_label.bind("<Button-4>", self._on_zoom)
        self.preview_label.bind("<Button-5>", self._on_zoom)
        self.preview_label.bind("<ButtonPress-1>", self._on_drag_start)
        self.preview_label.bind("<B1-Motion>", self._on_drag_move)
        self.preview_label.bind("<ButtonRelease-1>", lambda e: setattr(self, '_drag_start', None))

    def load_image(self, filepath: str):
        """Load image, auto-fit to window"""
        self._original_image = None
        self._fit_ratio = 1.0
        self._zoom_level = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._free_zoom = False
        self._update_zoom_button()

        img, err = load_image(filepath)
        if img:
            try:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                self._original_image = img.copy()
                img.close()
                self._update_display()
            except Exception as e:
                self.preview_label.configure(image='', text='Error: {}'.format(e))
        else:
            self.preview_label.configure(image='', text='Cannot load: {}'.format(err))

    def _update_zoom_button(self):
        if self._free_zoom:
            self.btn_zoom.configure(bootstyle="primary", text="自由缩放")
        else:
            self.btn_zoom.configure(bootstyle="secondary-outline", text="自由缩放")

    def _toggle_zoom(self):
        self._free_zoom = not self._free_zoom
        self._update_zoom_button()
        if not self._free_zoom:
            self._zoom_level = 1.0
            self._offset_x = 0
            self._offset_y = 0
        self._update_display()

    def _reset(self):
        self._zoom_level = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._update_display()

    def _update_display(self):
        if not self._original_image:
            return

        label_w = self.preview_label.winfo_width() or self.max_size[0]
        label_h = self.preview_label.winfo_height() or self.max_size[1]

        if label_w < 20 or label_h < 20:
            return

        img_w, img_h = self._original_image.size

        # Compute fit ratio: how much to scale so image fits inside label
        self._fit_ratio = min(label_w / img_w, label_h / img_h)

        # Effective zoom for display
        effective_zoom = self._fit_ratio * self._zoom_level
        display_w = max(1, int(img_w * effective_zoom))
        display_h = max(1, int(img_h * effective_zoom))

        # Update label text
        abs_zoom = int(effective_zoom * 100)
        self.zoom_label.configure(text="{}%".format(abs_zoom) if self._free_zoom else "适配")

        resized = self._original_image.resize(
            (display_w, display_h), Image.Resampling.LANCZOS
        )

        # Clamp offset
        ox = max(0, min(self._offset_x, max(0, display_w - label_w)))
        oy = max(0, min(self._offset_y, max(0, display_h - label_h)))
        self._offset_x = ox
        self._offset_y = oy

        bg = Image.new('RGB', (label_w, label_h), (43, 43, 43))

        if display_w <= label_w and display_h <= label_h:
            px = (label_w - display_w) // 2
            py = (label_h - display_h) // 2
            bg.paste(resized, (px, py))
        else:
            bg.paste(resized, (-ox, -oy))

        photo = ImageTk.PhotoImage(bg)
        self.preview_label.configure(image=photo, bg='#2b2b2b')
        setattr(self.preview_label, '_photo_ref', photo)

    def _on_zoom(self, event):
        if not self._original_image or not self._free_zoom:
            return

        mx, my = event.x, event.y
        old_zoom = self._zoom_level

        if event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self._zoom_level = max(0.05, self._zoom_level * 0.92)
        else:
            self._zoom_level = min(20.0, self._zoom_level * 1.08)

        ratio = self._zoom_level / old_zoom
        self._offset_x = int(mx * ratio - mx + self._offset_x * ratio)
        self._offset_y = int(my * ratio - my + self._offset_y * ratio)
        self._update_display()

    def _on_drag_start(self, event):
        if not self._free_zoom:
            return
        self._drag_start = (event.x, event.y, self._offset_x, self._offset_y)

    def _on_drag_move(self, event):
        if not self._drag_start:
            return
        sx, sy, ox, oy = self._drag_start
        self._offset_x = ox + (sx - event.x)
        self._offset_y = oy + (sy - event.y)
        self._update_display()

    def clear(self):
        self._original_image = None
        self._fit_ratio = 1.0
        self._zoom_level = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self.preview_label.configure(image='', text='Select image to preview',
                                      bg='#2b2b2b', fg='#888888')
        setattr(self.preview_label, '_photo_ref', None)
