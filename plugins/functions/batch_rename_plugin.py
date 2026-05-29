"""
King_photo - 批量重命名插件示例
演示如何创建功能插件
"""

import os
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.api.plugin_interfaces import IFunctionPlugin

# 获取日志记录器
logger = logging.getLogger(__name__)


class BatchRenamePlugin(IFunctionPlugin):
    """批量重命名插件"""
    
    @property
    def plugin_name(self) -> str:
        """插件名称"""
        return "batch_rename"
    
    @property
    def plugin_type(self) -> str:
        """插件类型"""
        return "rename"
    
    @property
    def description(self) -> str:
        """插件描述"""
        return "批量重命名图片文件，支持多种命名模式"
    
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
                - pattern: 命名模式
                - output_dir: 输出目录
                - start_seq: 起始序号
                - sequence_length: 序号位数
                
        Returns:
            执行结果字典
        """
        # 获取参数
        pattern = kwargs.get("pattern", "{datetime}_{seq}")
        output_dir = kwargs.get("output_dir", None)
        start_seq = kwargs.get("start_seq", 1)
        sequence_length = kwargs.get("sequence_length", 3)
        
        results = {
            "total": len(file_list),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        # 创建输出目录
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        seq = start_seq
        
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
                
                # 生成新文件名
                new_filename = self._generate_filename(filepath, pattern, seq, sequence_length)
                
                # 确定输出路径
                if output_dir:
                    new_path = os.path.join(output_dir, new_filename)
                else:
                    dir_name = os.path.dirname(filepath)
                    new_path = os.path.join(dir_name, new_filename)
                
                # 检查目标文件是否已存在
                if os.path.exists(new_path):
                    # 添加序号避免冲突
                    base, ext = os.path.splitext(new_path)
                    counter = 1
                    while os.path.exists(f"{base}_{counter}{ext}"):
                        counter += 1
                    new_path = f"{base}_{counter}{ext}"
                
                # 重命名文件
                os.rename(filepath, new_path)
                
                results["success"] += 1
                results["details"].append({
                    "file": filepath,
                    "new_path": new_path,
                    "status": "success"
                })
                
                seq += 1
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "file": filepath,
                    "status": "failed",
                    "error": str(e)
                })
                logger.error(f"重命名文件失败: {filepath}, 错误: {str(e)}")
        
        logger.info(f"批量重命名完成: 成功 {results['success']}, "
                   f"失败 {results['failed']}, 跳过 {results['skipped']}")
        
        return results
    
    def _generate_filename(self, filepath: str, pattern: str, seq: int, sequence_length: int) -> str:
        """
        生成新文件名
        
        Args:
            filepath: 原文件路径
            pattern: 命名模式
            seq: 序号
            sequence_length: 序号位数
            
        Returns:
            新文件名
        """
        # 获取原文件信息
        original_name = os.path.splitext(os.path.basename(filepath))[0]
        ext = os.path.splitext(filepath)[1]
        
        # 尝试从文件名中提取日期时间
        datetime_info = self._extract_datetime_from_filename(original_name)
        
        # 替换模式中的变量
        new_name = pattern
        
        # 时间变量
        if datetime_info:
            new_name = new_name.replace("{date}", datetime_info.strftime("%Y%m%d"))
            new_name = new_name.replace("{time}", datetime_info.strftime("%H%M%S"))
            new_name = new_name.replace("{datetime}", datetime_info.strftime("%Y%m%d_%H%M%S"))
            new_name = new_name.replace("{year}", datetime_info.strftime("%Y"))
            new_name = new_name.replace("{month}", datetime_info.strftime("%m"))
            new_name = new_name.replace("{day}", datetime_info.strftime("%d"))
            new_name = new_name.replace("{hour}", datetime_info.strftime("%H"))
            new_name = new_name.replace("{minute}", datetime_info.strftime("%M"))
            new_name = new_name.replace("{second}", datetime_info.strftime("%S"))
            new_name = new_name.replace("{timestamp}", str(int(datetime_info.timestamp())))
        else:
            # 如果没有日期时间信息，使用当前时间
            now = datetime.now()
            new_name = new_name.replace("{date}", now.strftime("%Y%m%d"))
            new_name = new_name.replace("{time}", now.strftime("%H%M%S"))
            new_name = new_name.replace("{datetime}", now.strftime("%Y%m%d_%H%M%S"))
            new_name = new_name.replace("{year}", now.strftime("%Y"))
            new_name = new_name.replace("{month}", now.strftime("%m"))
            new_name = new_name.replace("{day}", now.strftime("%d"))
            new_name = new_name.replace("{hour}", now.strftime("%H"))
            new_name = new_name.replace("{minute}", now.strftime("%M"))
            new_name = new_name.replace("{second}", now.strftime("%S"))
            new_name = new_name.replace("{timestamp}", str(int(now.timestamp())))
        
        # 文件变量
        new_name = new_name.replace("{original}", original_name)
        new_name = new_name.replace("{ext}", ext[1:])  # 去掉点号
        
        # 序号变量
        seq_str = str(seq).zfill(sequence_length)
        new_name = new_name.replace("{seq}", seq_str)
        
        # 确保文件名合法
        new_name = self._sanitize_filename(new_name)
        
        # 添加扩展名
        if not new_name.endswith(ext):
            new_name += ext
        
        return new_name
    
    def _extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        """
        从文件名中提取日期时间
        
        Args:
            filename: 文件名（不含扩展名）
            
        Returns:
            提取的日期时间，如果提取失败返回None
        """
        # 常见的日期时间格式
        patterns = [
            r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})',  # 20240101_120000
            r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})',    # 20240101120000
            r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})',  # 2024-01-01 12:00:00
            r'(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})',  # 2024-01-01_12-00-00
            r'(\d{4})\.(\d{2})\.(\d{2})_(\d{2})\.(\d{2})\.(\d{2})',  # 2024.01.01_12.00.00
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    hour = int(match.group(4))
                    minute = int(match.group(5))
                    second = int(match.group(6))
                    
                    # 验证日期时间有效性
                    if (1900 <= year <= 2100 and 1 <= month <= 12 and 
                        1 <= day <= 31 and 0 <= hour <= 23 and 
                        0 <= minute <= 59 and 0 <= second <= 59):
                        return datetime(year, month, day, hour, minute, second)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的非法字符
        
        Args:
            filename: 原文件名
            
        Returns:
            清理后的文件名
        """
        # Windows文件名非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        # 替换非法字符为下划线
        sanitized = re.sub(illegal_chars, '_', filename)
        
        # 移除前后空格和点号
        sanitized = sanitized.strip(' .')
        
        # 如果文件名为空，使用默认名称
        if not sanitized:
            sanitized = "unnamed"
        
        return sanitized
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        获取插件参数定义
        
        Returns:
            参数字典
        """
        return {
            "pattern": {
                "type": "str",
                "default": "{datetime}_{seq}",
                "required": False,
                "description": "命名模式，支持变量：{date}, {time}, {datetime}, {year}, {month}, {day}, {hour}, {minute}, {second}, {timestamp}, {original}, {ext}, {seq}"
            },
            "output_dir": {
                "type": "str",
                "default": None,
                "required": False,
                "description": "输出目录，None表示重命名到原目录"
            },
            "start_seq": {
                "type": "int",
                "default": 1,
                "required": False,
                "description": "起始序号"
            },
            "sequence_length": {
                "type": "int",
                "default": 3,
                "required": False,
                "description": "序号位数"
            }
        }
    
    def is_available(self) -> bool:
        """检查插件是否可用"""
        return True


# 插件元数据
PLUGIN_METADATA = {
    "name": "Batch Rename Plugin",
    "version": "1.0.0",
    "author": "King_photo Team",
    "description": "批量重命名图片文件插件",
    "plugin_name": "batch_rename"
}