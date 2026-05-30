"""
King_photo - 自定义UI组件

此文件为兼容层，所有组件已拆分为子模块:
  - widgets/thumbnail.py    → ThumbnailWidget
  - widgets/preview.py      → ImagePreviewWidget
  - widgets/metadata.py     → MetadataEditorWidget
  - widgets/progress.py     → ProgressDialog
  - widgets/scrollable.py   → ScrollableFrame

直接导入仍然可用: from .widgets import ThumbnailWidget
"""

from .widgets import (
    ThumbnailWidget,
    ImagePreviewWidget,
    MetadataEditorWidget,
    ProgressDialog,
    ScrollableFrame,
)

__all__ = [
    'ThumbnailWidget',
    'ImagePreviewWidget',
    'MetadataEditorWidget',
    'ProgressDialog',
    'ScrollableFrame',
]
