"""
King_photo - 水印扩展插件示例
演示如何创建扩展插件
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.api.plugin_interfaces import IExtensionPlugin

# 获取日志记录器
logger = logging.getLogger(__name__)


class WatermarkExtensionPlugin(IExtensionPlugin):
    """水印扩展插件"""
    
    @property
    def extension_name(self) -> str:
        """扩展名称"""
        return "watermark"
    
    @property
    def target_module(self) -> str:
        """目标模块"""
        return "metadata_writer"
    
    @property
    def description(self) -> str:
        """扩展描述"""
        return "为图片添加水印的扩展插件"
    
    @property
    def priority(self) -> int:
        """扩展优先级"""
        return 10  # 中等优先级
    
    def before_execute(self, *args, **kwargs) -> Any:
        """
        执行前钩子
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            处理后的参数
        """
        # 在写入元数据前添加水印逻辑
        logger.debug("水印扩展：执行前钩子")
        
        # 这里可以添加水印处理逻辑
        # 例如：检查是否需要添加水印，配置水印参数等
        
        return args, kwargs
    
    def after_execute(self, result: Any, *args, **kwargs) -> Any:
        """
        执行后钩子
        
        Args:
            result: 执行结果
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            处理后的结果
        """
        # 在写入元数据后添加水印逻辑
        logger.debug("水印扩展：执行后钩子")
        
        # 这里可以添加水印处理逻辑
        # 例如：根据元数据信息添加水印，保存水印配置等
        
        return result
    
    def on_error(self, error: Exception, *args, **kwargs) -> Any:
        """
        错误处理钩子
        
        Args:
            error: 异常对象
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            处理结果
        """
        # 错误处理逻辑
        logger.warning(f"水印扩展：处理错误 - {str(error)}")
        
        # 这里可以添加错误恢复逻辑
        # 例如：回滚操作，记录错误日志，发送通知等
        
        return None
    
    def is_enabled(self) -> bool:
        """检查扩展是否启用"""
        return True
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的插件列表"""
        return []  # 无依赖


class WatermarkConfig:
    """水印配置类"""
    
    def __init__(self):
        self.text = "King_photo"
        self.position = "bottom-right"  # bottom-right, bottom-left, top-right, top-left, center
        self.opacity = 0.5
        self.font_size = 20
        self.font_color = (255, 255, 255)  # 白色
        self.font_path = None  # 使用默认字体
        self.margin = 10
        self.angle = 0  # 旋转角度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "text": self.text,
            "position": self.position,
            "opacity": self.opacity,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "font_path": self.font_path,
            "margin": self.margin,
            "angle": self.angle
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatermarkConfig':
        """从字典创建配置"""
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
    "name": "Watermark Extension Plugin",
    "version": "1.0.0",
    "author": "King_photo Team",
    "description": "图片水印扩展插件",
    "extension_name": "watermark"
}