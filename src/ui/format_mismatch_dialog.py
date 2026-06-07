"""
格式不匹配交互式对话框
"""
import logging
import os
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict

import ttkbootstrap as ttk
from PIL import Image, ImageTk

from ..utils.image_loader import load_image

logger = logging.getLogger(__name__)


class FormatMismatchDialog(tk.Toplevel):
    """格式不匹配处理对话框 — 双缩略图 + 文件信息 + 操作选项"""

    def __init__(self, master, mismatched_files: List[dict], output_dir: str = None):
        super().__init__(master)
        
        self.mismatched_files = mismatched_files
        self.output_dir = output_dir
        self.current_index = 0
        self.decisions: Dict[str, str] = {}
        self.batch_rules: Dict[str, str] = {}
        self.result = None
        
        self.title("检测到格式不匹配")
        self.transient(master)
        self.grab_set()
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = min(int(screen_w * 0.75), 950)
        win_h = min(int(screen_h * 0.65), 550)
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.minsize(750, 420)
        
        self._create_ui()
        self._show_current_file()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_ui(self):
        """创建对话框UI"""
        # === Row 0: Header ===
        header = ttk.Frame(self, padding=(10, 8))
        header.pack(fill=tk.X)
        self.count_label = ttk.Label(header, font=('', 10, 'bold'))
        self.count_label.pack(side=tk.LEFT)
        ttk.Button(header, text="浏览文件", command=self._on_browse_file,
                   bootstyle="secondary-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(header, text="跳过当前", command=self._on_skip_current,
                   bootstyle="secondary-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # === Row 1: Preview + Info (main content) ===
        mid = ttk.Frame(self, padding=(10, 5))
        mid.pack(fill=tk.BOTH, expand=True)

        # Left: dual thumbnails
        thumb_area = ttk.Frame(mid)
        thumb_area.pack(side=tk.LEFT, fill=tk.BOTH)

        # Current disguise
        cur_frame = ttk.LabelFrame(thumb_area, text="当前伪装")
        cur_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        self.preview_cur = tk.Label(cur_frame, bg='#4a3030', fg='white',
                                     width=24, height=11, font=('', 9))
        self.preview_cur.pack(padx=2, pady=2)
        self.status_cur = tk.Label(cur_frame, text="", fg='#ff6b6b', bg=self.cget('bg'), font=('', 8))
        self.status_cur.pack()

        # Corrected
        fix_frame = ttk.LabelFrame(thumb_area, text="修正后")
        fix_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        self.preview_fix = tk.Label(fix_frame, bg='#304a30', fg='white',
                                     width=24, height=11, font=('', 9))
        self.preview_fix.pack(padx=2, pady=2)
        self.status_fix = tk.Label(fix_frame, text="", fg='#51cf66', bg=self.cget('bg'), font=('', 8))
        self.status_fix.pack()

        # Right: file info
        info_frame = ttk.LabelFrame(mid, text="文件信息")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.info_label = tk.Label(info_frame, text="", justify=tk.LEFT,
                                    anchor=tk.NW, font=('Microsoft YaHei', 9),
                                    wraplength=280)
        self.info_label.pack(fill=tk.BOTH, expand=True)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # === Row 2: Options ===
        opt_frame = ttk.LabelFrame(self, text="选择处理方式")
        opt_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        self.choice_var = tk.StringVar(value='fix')
        ttk.Radiobutton(opt_frame, text="修复后缀 + 写入时间信息 -> 输出到正常修复目录",
                        variable=self.choice_var, value='fix').pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(opt_frame, text="保持原样，不修复后缀 -> 仅改名和时间 -> 输出到未处理目录",
                        variable=self.choice_var, value='skip').pack(anchor=tk.W, pady=1)

        # === Row 3: Buttons ===
        btn_frame = ttk.Frame(self, padding=(10, 5))
        btn_frame.pack(fill=tk.X)
        
        self.apply_all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(btn_frame, text="之后遇到相同格式伪装都按此处理",
                        variable=self.apply_all_var).pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="确定", command=self._on_confirm,
                   bootstyle="primary", width=10).pack(side=tk.RIGHT, padx=5)

    def _show_current_file(self):
        """显示当前文件"""
        if self.current_index >= len(self.mismatched_files):
            self._on_finish()
            return
        
        info = self.mismatched_files[self.current_index]
        total = len(self.mismatched_files)
        self.count_label.configure(text="文件 {} / {}".format(self.current_index + 1, total))
        
        # File info text
        impact = info.get('impact', '?')
        lines = [
            "文件名: {}".format(os.path.basename(info['filepath'])),
            "",
            "检测格式: {}".format(info['real_format']),
            "当前后缀: {}".format(info['current_ext']),
            "正确后缀: {}".format(info['correct_ext']),
            "",
            "[{}] 影响等级: {}".format(impact, impact),
            "",
            info.get('impact_reason', '格式不匹配'),
            "",
            "建议: {}".format('建议修复' if info.get('recommend_fix') else '可自行选择'),
        ]
        self.info_label.configure(text='\n'.join(lines))
        
        # Default choice
        self.choice_var.set('fix' if info.get('recommend_fix') else 'skip')
        
        # Load dual preview
        self._load_preview(info)

    def _load_preview(self, info: dict):
        """加载双缩略图"""
        filepath = info['filepath']
        preview_w, preview_h = 180, 155
        
        # Reset to loading state
        self.preview_cur.configure(image='', text='Loading...')
        self.preview_fix.configure(image='', text='Loading...')
        self.preview_cur.image = None
        self.preview_fix.image = None
        
        img, err = load_image(filepath)
        
        if img:
            try:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Create thumbnail for left preview
                img_left = img.copy()
                img_left.thumbnail((preview_w, preview_h), Image.Resampling.LANCZOS)
                photo_left = ImageTk.PhotoImage(img_left)
                self.preview_cur.configure(image=photo_left, text='', bg='#3a3030',
                                           width=preview_w, height=preview_h)
                self.preview_cur.image = photo_left
                
                # Create thumbnail for right preview
                img_right = img.copy()
                img_right.thumbnail((preview_w, preview_h), Image.Resampling.LANCZOS)
                photo_right = ImageTk.PhotoImage(img_right)
                self.preview_fix.configure(image=photo_right, text='', bg='#303a30',
                                           width=preview_w, height=preview_h)
                self.preview_fix.image = photo_right
                
                self.status_cur.configure(text="当前 {} - 格式混乱".format(info['current_ext']))
                self.status_fix.configure(text="修复后 {} - 格式正确".format(info['correct_ext']))
                
            finally:
                img.close()
        else:
            # Cannot preview
            self.preview_cur.configure(image='', text='Cannot preview', bg='#3a3a3a', fg='#ff9999')
            self.preview_cur.image = None
            self.status_cur.configure(text="无法预览当前格式")
            
            real_fmt = info.get('real_format', '')
            if real_fmt in ('MOV', 'MP4', 'AVI', 'WMV'):
                self.preview_fix.configure(image='', text='Video file', bg='#3a3a3a', fg='#ffaa66')
                self.status_fix.configure(text="实际为视频，非图片")
            else:
                self.preview_fix.configure(image='', text='May restore preview', bg='#3a3a3a', fg='#99ff99')
                self.status_fix.configure(text="修复后可能恢复预览")
            self.preview_fix.image = None

    def _on_confirm(self):
        """确认当前选择"""
        info = self.mismatched_files[self.current_index]
        self.decisions[info['filepath']] = self.choice_var.get()
        
        if self.apply_all_var.get():
            key = "{}->{}".format(info['real_format'], info['current_ext'])
            self.batch_rules[key] = self.choice_var.get()
        
        # Apply batch rule to remaining files
        if self.apply_all_var.get():
            choice = self.choice_var.get()
            for i in range(self.current_index + 1, len(self.mismatched_files)):
                remaining = self.mismatched_files[i]
                remaining_key = "{}->{}".format(remaining['real_format'], remaining['current_ext'])
                if remaining_key == key:
                    self.decisions[remaining['filepath']] = choice
        
        self.current_index += 1
        self.apply_all_var.set(False)
        self._show_current_file()

    def _on_skip_current(self):
        """跳过当前"""
        info = self.mismatched_files[self.current_index]
        self.decisions[info['filepath']] = 'skip'
        self.current_index += 1
        self._show_current_file()

    def _on_finish(self):
        """完成"""
        self.result = {'decisions': self.decisions, 'batch_rules': self.batch_rules}
        self.destroy()

    def _on_close(self):
        """关闭"""
        for i in range(self.current_index, len(self.mismatched_files)):
            self.decisions[self.mismatched_files[i]['filepath']] = 'skip'
        self._on_finish()

    def _on_browse_file(self):
        """打开文件"""
        try:
            os.startfile(self.mismatched_files[self.current_index]['filepath'])
        except Exception:
            logger.warning("打开文件失败", exc_info=True)


def collect_mismatched_files(file_list: List[str]) -> List[dict]:
    """收集格式不匹配且需要弹窗的文件"""
    from ..api import get_api
    api = get_api()
    from ..utils.format_impact import get_impact, should_prompt_user
    
    mismatched = []
    for fp in file_list:
        if not os.path.exists(fp):
            continue
        
        format_info = api.detect_format(fp)
        header_format = format_info.get('format') if format_info else None
        ext_format = os.path.splitext(fp)[1].lstrip('.').upper()
        
        if header_format and ext_format and header_format != ext_format:
            impact_info = get_impact(header_format, ext_format)
            if should_prompt_user(header_format, ext_format):
                current_ext = os.path.splitext(fp)[1].lower()
                correct_ext = ".{}".format(header_format.lower())
                
                mismatched.append({
                    'filepath': fp,
                    'real_format': header_format,
                    'current_ext': current_ext,
                    'correct_ext': correct_ext,
                    'impact': impact_info['level'],
                    'impact_reason': impact_info['reason'],
                    'recommend_fix': impact_info['recommend_fix']
                })
    
    return mismatched
