"""
King_photo - 批量导出插件示例
演示如何创建功能插件
"""

import os
import logging
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.api.plugin_interfaces import IFunctionPlugin

# 获取日志记录器
logger = logging.getLogger(__name__)


class BatchExportPlugin(IFunctionPlugin):
    """批量导出插件"""
    
    @property
    def plugin_name(self) -> str:
        """插件名称"""
        return "batch_export"
    
    @property
    def plugin_type(self) -> str:
        """插件类型"""
        return "export"
    
    @property
    def description(self) -> str:
        """插件描述"""
        return "批量导出图片文件，支持多种导出格式和选项"
    
    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"
    
    def execute(self, file_list: List[str], **kwargs) -> Dict[str, Any]:
        """
        执行插件功能
        
        Args:
            file_list: 文件列表
            **kwargs: 额外参数
                - output_dir: 输出目录
                - format: 导出格式 ('original', 'jpeg', 'png')
                - quality: 质量 (1-100)
                - preserve_structure: 是否保持目录结构
                
        Returns:
            执行结果字典
        """
        # 获取参数
        output_dir = kwargs.get("output_dir", "exports")
        export_format = kwargs.get("format", "original")
        quality = kwargs.get("quality", 85)
        preserve_structure = kwargs.get("preserve_structure", True)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            "total": len(file_list),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        for filepath in file_list:
            try:
                # 检查文件是否存在
                if not os.path.exists(filepath):
                    results["skipped"] += 1
                    results["details"].append({
                        "file": filepath,
                        "status": "skipped",
                        "message": "文件不存在"
                    })
                    continue
                
                # 确定输出路径
                if preserve_structure:
                    # 保持相对路径结构
                    rel_path = os.path.relpath(filepath)
                    output_path = os.path.join(output_dir, rel_path)
                else:
                    # 只保留文件名
                    output_path = os.path.join(output_dir, os.path.basename(filepath))
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 根据格式处理
                if export_format == "original":
                    # 直接复制原文件
                    shutil.copy2(filepath, output_path)
                else:
                    # 这里可以添加格式转换逻辑
                    # 目前简单复制
                    shutil.copy2(filepath, output_path)
                
                results["success"] += 1
                results["details"].append({
                    "file": filepath,
                    "output": output_path,
                    "status": "success"
                })
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "file": filepath,
                    "status": "failed",
                    "error": str(e)
                })
                logger.error(f"导出文件失败: {filepath}, 错误: {str(e)}")
        
        logger.info(f"批量导出完成: 成功 {results['success']}, "
                   f"失败 {results['failed']}, 跳过 {results['skipped']}")
        
        return results
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        获取插件参数定义
        
        Returns:
            参数字典
        """
        return {
            "output_dir": {
                "type": "str",
                "default": "exports",
                "required": False,
                "description": "输出目录路径"
            },
            "format": {
                "type": "str",
                "default": "original",
                "required": False,
                "description": "导出格式 ('original', 'jpeg', 'png')"
            },
            "quality": {
                "type": "int",
                "default": 85,
                "required": False,
                "description": "导出质量 (1-100)"
            },
            "preserve_structure": {
                "type": "bool",
                "default": True,
                "required": False,
                "description": "是否保持目录结构"
            }
        }
    
    def is_available(self) -> bool:
        """检查插件是否可用"""
        return True


# 插件元数据
PLUGIN_METADATA = {
    "name": "Batch Export Plugin",
    "version": "1.0.0",
    "author": "King_photo Team",
    "description": "批量导出图片文件插件",
    "plugin_name": "batch_export"
}