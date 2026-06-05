"""
King_photo - 水印插件（双接口：扩展 + 功能）
- 作为 IExtensionPlugin：自动伴随元数据写入触发
- 作为 IFunctionPlugin：独立运行，对选中图片直接加水印
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from src.api.plugin_interfaces import IExtensionPlugin, IFunctionPlugin

# 获取日志记录器
logger = logging.getLogger(__name__)


class WatermarkPlugin(IExtensionPlugin, IFunctionPlugin):
    """水印插件 — 同时支持嵌入钩子和独立运行"""

    # 水印运行时配置
    _auto_trigger = True  # 是否自动伴随 metadata_writer 触发

    # ============================================================
    # IExtensionPlugin 接口（嵌入模式）
    # ============================================================
    @property
    def extension_name(self) -> str:
        return "watermark"

    @property
    def target_module(self) -> str:
        return "metadata_writer"

    @property
    def priority(self) -> int:
        return 10

    def before_execute(self, *args, **kwargs) -> Any:
        if not self._auto_trigger:
            return args, kwargs
        logger.debug("水印扩展：执行前钩子")
        return args, kwargs

    def after_execute(self, result: Any, *args, **kwargs) -> Any:
        if not self._auto_trigger:
            return result
        logger.debug("水印扩展：执行后钩子")
        # 尝试给输出文件加水印
        output_path = kwargs.get('output_dir') or (
            result.get('output_path') if isinstance(result, dict) else None
        )
        filepath = args[0] if args else kwargs.get('filepath')
        target = output_path or filepath
        if target and os.path.isfile(target):
            try:
                self._apply_watermark(target, WatermarkConfig())
            except Exception as e:
                logger.warning(f"水印扩展自动加水印失败: {e}")
        return result

    def on_error(self, error: Exception, *args, **kwargs) -> Any:
        logger.warning(f"水印扩展：处理错误 - {str(error)}")
        return None

    def is_enabled(self) -> bool:
        return True

    def get_dependencies(self) -> List[str]:
        return []

    # ============================================================
    # IFunctionPlugin 接口（独立模式）
    # ============================================================
    @property
    def plugin_name(self) -> str:
        return "watermark"

    @property
    def plugin_type(self) -> str:
        return "image"

    @property
    def description(self) -> str:
        return "对选中图片添加文字水印，支持自定义文字、位置、透明度"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def author(self) -> str:
        return "King_photo Team"

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "text": {
                "type": "str",
                "default": "King_photo",
                "required": False,
                "description": "水印文字内容"
            },
            "position": {
                "type": "str",
                "default": "bottom-right",
                "required": False,
                "description": "水印位置 (bottom-right / bottom-left / top-right / top-left / center)"
            },
            "opacity": {
                "type": "int",
                "default": 50,
                "required": False,
                "description": "水印透明度 (0-100，0=全透明，100=不透明)"
            },
            "font_size": {
                "type": "int",
                "default": 20,
                "required": False,
                "description": "字体大小（像素）"
            },
            "output_dir": {
                "type": "str",
                "default": None,
                "required": False,
                "description": "输出目录，留空则覆盖原文件（建议设置以避免原图丢失）"
            }
        }

    def execute(self, file_list: List[str], **kwargs) -> Dict[str, Any]:
        config = WatermarkConfig()
        config.text = kwargs.get("text", config.text)
        config.position = kwargs.get("position", config.position)
        config.opacity = kwargs.get("opacity", config.opacity) / 100.0
        config.font_size = kwargs.get("font_size", config.font_size)
        output_dir = kwargs.get("output_dir")

        results = {"total": len(file_list), "success": 0, "failed": 0, "details": []}

        for filepath in file_list:
            try:
                dest = filepath
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    dest = os.path.join(output_dir, os.path.basename(filepath))
                    if os.path.exists(dest):
                        base, ext = os.path.splitext(dest)
                        counter = 1
                        while os.path.exists(f"{base}_{counter}{ext}"):
                            counter += 1
                        dest = f"{base}_{counter}{ext}"

                self._apply_watermark(filepath, config, dest)
                results["success"] += 1
                results["details"].append({"file": filepath, "output": dest, "status": "success"})
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"file": filepath, "status": "failed", "error": str(e)})
                logger.error(f"水印添加失败 [{filepath}]: {e}")

        logger.info(f"水印执行完成: 成功 {results['success']}, 失败 {results['failed']}")
        return results

    # ============================================================
    # 水印核心逻辑
    # ============================================================
    def _apply_watermark(self, filepath: str, config: 'WatermarkConfig', dest: str = None):
        """实际加水印"""
        img = Image.open(filepath).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 字体
        try:
            font = ImageFont.truetype("simhei.ttf", config.font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", config.font_size)
            except Exception:
                font = ImageFont.load_default()

        # 计算位置
        bbox = draw.textbbox((0, 0), config.text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        margin = 15
        pos_map = {
            "bottom-right": (img.width - tw - margin, img.height - th - margin),
            "bottom-left":  (margin, img.height - th - margin),
            "top-right":    (img.width - tw - margin, margin),
            "top-left":     (margin, margin),
            "center":       ((img.width - tw) // 2, (img.height - th) // 2),
        }
        pos = pos_map.get(config.position, pos_map["bottom-right"])

        # 绘制
        alpha = int(255 * config.opacity)
        draw.text(pos, config.text, fill=(255, 255, 255, alpha), font=font)

        # 合并
        watermarked = Image.alpha_composite(img, overlay).convert("RGB")
        watermarked.save(dest or filepath)
        logger.info(f"水印已添加: {os.path.basename(dest or filepath)}")


class WatermarkConfig:
    """水印配置类"""

    def __init__(self):
        self.text = "King_photo"
        self.position = "bottom-right"
        self.opacity = 0.5
        self.font_size = 20
        self.font_color = (255, 255, 255)
        self.font_path = None
        self.margin = 10
        self.angle = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text, "position": self.position,
            "opacity": self.opacity, "font_size": self.font_size,
            "font_color": self.font_color, "font_path": self.font_path,
            "margin": self.margin, "angle": self.angle
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatermarkConfig':
        config = cls()
        config.text = data.get("text", config.text)
        config.position = data.get("position", config.position)
        config.opacity = data.get("opacity", config.opacity)
        config.font_size = data.get("font_size", config.font_size)
        config.font_color = data.get("font_color", config.font_color)
        config.font_path = data.get("font_path", config.font_path)
        config.margin = data.get("margin", config.margin)
        config.angle = data.get("angle", config.angle)
        return config


# 插件元数据
PLUGIN_METADATA = {
    "name": "Watermark Plugin",
    "version": "1.0.0",
    "author": "King_photo Team",
    "description": "图片水印插件（支持独立运行和自动伴随）",
    "extension_name": "watermark",
    "plugin_name": "watermark"
}