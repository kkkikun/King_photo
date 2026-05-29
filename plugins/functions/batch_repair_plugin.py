"""
King_photo - 批量修复插件示例
演示如何创建功能插件
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.api.plugin_interfaces import IFunctionPlugin

# 获取日志记录器
logger = logging.getLogger(__name__)


class BatchRepairPlugin(IFunctionPlugin):
    """批量修复插件"""
    
    @property
    def plugin_name(self) -> str:
        """插件名称"""
        return "batch_repair"
    
    @property
    def plugin_type(self) -> str:
        """插件类型"""
        return "repair"
    
    @property
    def description(self) -> str:
        """插件描述"""
        return "批量修复图片文件，支持修复后缀和时间"
    
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
                - fix_extension: 是否修复扩展名
                - fix_time: 是否修复时间
                - time_source: 时间来源 ('auto', 'filename', 'filetime')
                - output_dir: 输出目录
                
        Returns:
            执行结果字典
        """
        # 获取参数
        fix_extension = kwargs.get("fix_extension", True)
        fix_time = kwargs.get("fix_time", True)
        time_source = kwargs.get("time_source", "auto")
        output_dir = kwargs.get("output_dir", None)
        
        results = {
            "total": len(file_list),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        try:
            # 延迟导入修复引擎
            from src.core.repair_engine import RepairEngine
            repair_engine = RepairEngine()
            
            # 创建输出目录
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
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
                    
                    # 执行修复
                    repair_result = repair_engine.repair(
                        filepath, 
                        output_dir=output_dir,
                        fix_extension=fix_extension,
                        fix_time=fix_time,
                        time_source=time_source
                    )
                    
                    if repair_result.get("success", False):
                        results["success"] += 1
                        results["details"].append({
                            "file": filepath,
                            "status": "success",
                            "details": repair_result
                        })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "file": filepath,
                            "status": "failed",
                            "error": repair_result.get("message", "修复失败")
                        })
                    
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "file": filepath,
                        "status": "failed",
                        "error": str(e)
                    })
                    logger.error(f"修复文件失败: {filepath}, 错误: {str(e)}")
            
            logger.info(f"批量修复完成: 成功 {results['success']}, "
                       f"失败 {results['failed']}, 跳过 {results['skipped']}")
            
        except ImportError as e:
            logger.error(f"导入修复引擎失败: {str(e)}")
            results["failed"] = len(file_list)
            results["details"] = [{
                "file": f,
                "status": "failed",
                "error": f"导入修复引擎失败: {str(e)}"
            } for f in file_list]
        
        return results
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        获取插件参数定义
        
        Returns:
            参数字典
        """
        return {
            "fix_extension": {
                "type": "bool",
                "default": True,
                "required": False,
                "description": "是否修复文件扩展名"
            },
            "fix_time": {
                "type": "bool",
                "default": True,
                "required": False,
                "description": "是否修复文件时间"
            },
            "time_source": {
                "type": "str",
                "default": "auto",
                "required": False,
                "description": "时间来源 ('auto', 'filename', 'filetime')"
            },
            "output_dir": {
                "type": "str",
                "default": None,
                "required": False,
                "description": "输出目录，None表示输出到原目录"
            }
        }
    
    def is_available(self) -> bool:
        """检查插件是否可用"""
        try:
            # 尝试导入修复引擎
            from src.core.repair_engine import RepairEngine
            return True
        except ImportError:
            return False


# 插件元数据
PLUGIN_METADATA = {
    "name": "Batch Repair Plugin",
    "version": "1.0.0",
    "author": "King_photo Team",
    "description": "批量修复图片文件插件",
    "plugin_name": "batch_repair"
}