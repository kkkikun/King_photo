"""
King_photo - 核心接口定义
定义所有核心模块的抽象接口，支持依赖倒置和插件扩展
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union


class IFormatDetector(ABC):
    """格式检测接口"""
    
    @abstractmethod
    def detect_by_header(self, filepath: str) -> Optional[str]:
        """
        通过文件头检测真实格式
        
        Args:
            filepath: 文件路径
            
        Returns:
            格式名称，如 'JPEG', 'PNG'，如果无法检测则返回 None
        """
        pass
    
    @abstractmethod
    def detect_by_extension(self, filepath: str) -> Optional[str]:
        """
        通过扩展名检测格式
        
        Args:
            filepath: 文件路径
            
        Returns:
            格式名称，如 'JPEG', 'PNG'，如果无法检测则返回 None
        """
        pass
    
    @abstractmethod
    def get_real_format(self, filepath: str) -> Tuple[Optional[str], bool]:
        """
        获取真实格式
        
        Args:
            filepath: 文件路径
            
        Returns:
            (格式名称, 格式是否与扩展名匹配)
        """
        pass
    
    @abstractmethod
    def is_truly_image(self, filepath: str) -> Tuple[bool, str]:
        """
        检查是否为真正的图片
        
        Args:
            filepath: 文件路径
            
        Returns:
            (是否为图片, 错误信息或描述)
        """
        pass
    
    @abstractmethod
    def is_video_file(self, filepath: str) -> Tuple[bool, str]:
        """
        检查是否为视频文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            (是否为视频, 错误信息或描述)
        """
        pass
    
    @abstractmethod
    def get_format_info(self, filepath: str) -> Dict[str, Any]:
        """
        获取格式详细信息
        
        Args:
            filepath: 文件路径
            
        Returns:
            格式信息字典，包含：
            - format: 格式名称
            - extension: 扩展名
            - is_image: 是否为图片
            - is_video: 是否为视频
            - exif_support: 是否支持EXIF
            - xmp_support: 是否支持XMP
            - need_exiftool: 是否需要ExifTool
        """
        pass
    
    @abstractmethod
    def register_format(self, format_name: str, format_config: Dict[str, Any]) -> None:
        """
        注册新格式（插件机制）
        
        Args:
            format_name: 格式名称
            format_config: 格式配置，包含：
                - extensions: 扩展名列表
                - magic_numbers: 文件头魔数列表
                - exif_support: 是否支持EXIF
                - xmp_support: 是否支持XMP
                - need_exiftool: 是否需要ExifTool
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有支持的格式
        
        Returns:
            格式字典，键为格式名称，值为格式配置
        """
        pass


class IMetadataReader(ABC):
    """元数据读取接口"""
    
    @abstractmethod
    def read_metadata(self, filepath: str) -> Dict[str, Any]:
        """
        读取完整元信息
        
        Args:
            filepath: 图片路径
            
        Returns:
            元数据字典，包含：
            - filepath: 文件路径
            - filename: 文件名
            - extension: 扩展名
            - filesize: 文件大小
            - format: 格式信息
            - width: 宽度
            - height: 高度
            - datetime: 拍摄时间
            - exif: EXIF数据
            - xmp: XMP数据
            - file_created: 文件创建时间
            - file_modified: 文件修改时间
        """
        pass
    
    @abstractmethod
    def get_datetime(self, filepath: str) -> Optional[datetime]:
        """
        快速获取拍摄时间
        
        Args:
            filepath: 图片路径
            
        Returns:
            拍摄时间，如果无法获取则返回 None
        """
        pass
    
    @abstractmethod
    def get_summary(self, filepath: str) -> Dict[str, Any]:
        """
        获取元信息摘要
        
        Args:
            filepath: 图片路径
            
        Returns:
            摘要字典，包含关键元数据
        """
        pass
    
    @abstractmethod
    def get_editable_fields(self, filepath: str) -> Dict[str, Any]:
        """
        获取可编辑字段
        
        Args:
            filepath: 图片路径
            
        Returns:
            可编辑字段字典，按类别分组
        """
        pass
    
    @abstractmethod
    def read_exif(self, filepath: str) -> Dict[str, Any]:
        """
        读取EXIF数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            EXIF数据字典
        """
        pass
    
    @abstractmethod
    def read_xmp(self, filepath: str) -> Dict[str, Any]:
        """
        读取XMP数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            XMP数据字典
        """
        pass
    
    @abstractmethod
    def read_iptc(self, filepath: str) -> Dict[str, Any]:
        """
        读取IPTC数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            IPTC数据字典
        """
        pass
    
    @abstractmethod
    def read_with_exiftool(self, filepath: str) -> Dict[str, Any]:
        """
        使用ExifTool读取元数据
        
        Args:
            filepath: 图片路径
            
        Returns:
            ExifTool读取的元数据字典
        """
        pass


class IMetadataWriter(ABC):
    """元数据写入接口"""
    
    @abstractmethod
    def write_metadata(self, filepath: str, metadata: Dict[str, Any], 
                      copy_mode: bool = False, output_dir: str = None) -> Dict[str, Any]:
        """
        写入元信息
        
        Args:
            filepath: 图片路径
            metadata: 元数据字典
            copy_mode: 是否复制模式（保留原文件）
            output_dir: 输出目录（copy_mode=True时使用）
            
        Returns:
            操作结果字典，包含：
            - success: 是否成功
            - message: 结果消息
            - output_path: 输出文件路径
            - modified_fields: 修改的字段列表
        """
        pass
    
    @abstractmethod
    def write_metadata_from_filetime(self, filepath: str, 
                                   copy_mode: bool = False, output_dir: str = None) -> Dict[str, Any]:
        """
        将文件时间复制到EXIF
        
        Args:
            filepath: 图片路径
            copy_mode: 是否复制模式
            output_dir: 输出目录
            
        Returns:
            操作结果字典
        """
        pass
    
    @abstractmethod
    def batch_write_metadata(self, file_list: List[str], metadata: Dict[str, Any],
                           copy_mode: bool = False, output_dir: str = None,
                           progress_callback=None) -> Dict[str, Any]:
        """
        批量写入元信息
        
        Args:
            file_list: 文件列表
            metadata: 元数据字典
            copy_mode: 是否复制模式
            output_dir: 输出目录
            progress_callback: 进度回调函数
            
        Returns:
            批量操作结果字典，包含：
            - total: 总文件数
            - success: 成功数
            - failed: 失败数
            - skipped: 跳过数
            - details: 详细结果列表
        """
        pass
    
    @abstractmethod
    def write_exif(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入EXIF数据
        
        Args:
            filepath: 图片路径
            metadata: EXIF数据字典
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def write_xmp(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入XMP数据
        
        Args:
            filepath: 图片路径
            metadata: XMP数据字典
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def write_iptc(self, filepath: str, metadata: Dict[str, Any]) -> bool:
        """
        写入IPTC数据
        
        Args:
            filepath: 图片路径
            metadata: IPTC数据字典
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def copy_filetime_to_exif(self, filepath: str) -> bool:
        """
        复制文件时间到EXIF
        
        Args:
            filepath: 图片路径
            
        Returns:
            是否成功
        """
        pass


class IRepairEngine(ABC):
    """修复引擎接口"""
    
    @abstractmethod
    def check_file_extension(self, filepath: str) -> Dict[str, Any]:
        """
        检查文件后缀
        
        Args:
            filepath: 文件路径
            
        Returns:
            检查结果字典，包含：
            - filepath: 文件路径
            - current_extension: 当前扩展名
            - real_format: 真实格式
            - need_fix: 是否需要修复
            - confidence: 置信度
        """
        pass
    
    @abstractmethod
    def fix_extension(self, filepath: str, output_dir: str = None) -> Dict[str, Any]:
        """
        修复文件后缀
        
        Args:
            filepath: 文件路径
            output_dir: 输出目录
            
        Returns:
            修复结果字典，包含：
            - success: 是否成功
            - original_path: 原始路径
            - new_path: 新路径
            - old_extension: 旧扩展名
            - new_extension: 新扩展名
        """
        pass
    
    @abstractmethod
    def extract_time_info(self, filepath: str, time_source: str = 'auto') -> Dict[str, Any]:
        """
        提取时间信息
        
        Args:
            filepath: 文件路径
            time_source: 时间来源 ('auto', 'filename', 'metadata', 'filetime')
            
        Returns:
            时间信息字典，包含：
            - datetime: 提取的时间
            - source: 时间来源
            - confidence: 置信度
        """
        pass
    
    @abstractmethod
    def repair(self, filepath: str, output_dir: str = None,
              fix_extension: bool = True, fix_time: bool = True,
              time_source: str = 'auto', rename_format: str = None) -> Dict[str, Any]:
        """
        完整修复流程
        
        Args:
            filepath: 文件路径
            output_dir: 输出目录
            fix_extension: 是否修复扩展名
            fix_time: 是否修复时间
            time_source: 时间来源
            rename_format: 重命名格式
            
        Returns:
            修复结果字典
        """
        pass
    
    @abstractmethod
    def batch_repair(self, file_list: List[str], output_dir: str = None,
                    fix_extension: bool = True, fix_time: bool = True,
                    time_source: str = 'auto', rename_format: str = None,
                    progress_callback=None) -> Dict[str, Any]:
        """
        批量修复
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            fix_extension: 是否修复扩展名
            fix_time: 是否修复时间
            time_source: 时间来源
            rename_format: 重命名格式
            progress_callback: 进度回调函数
            
        Returns:
            批量修复结果字典
        """
        pass
    
    @abstractmethod
    def batch_repair_extension(self, file_list: List[str], output_dir: str = None,
                             progress_callback=None) -> Dict[str, Any]:
        """
        批量修复后缀
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            progress_callback: 进度回调函数
            
        Returns:
            批量修复结果字典
        """
        pass


class IFileProcessor(ABC):
    """文件处理器接口"""
    
    @abstractmethod
    def get_image_files(self, folder_path: str, recursive: bool = False) -> List[str]:
        """
        获取文件夹中的图片文件
        
        Args:
            folder_path: 文件夹路径
            recursive: 是否递归查找子文件夹
            
        Returns:
            图片文件路径列表
        """
        pass
    
    @abstractmethod
    def process_files(self, file_list: List[str], operation: str, **kwargs) -> Dict[str, Any]:
        """
        批量处理文件
        
        Args:
            file_list: 文件列表
            operation: 操作类型 ('rename', 'repair', 'export' 等)
            **kwargs: 操作参数
            
        Returns:
            处理结果字典
        """
        pass
    
    @abstractmethod
    def rename_files(self, file_list: List[str], pattern: str, 
                    output_dir: str = None, **kwargs) -> Dict[str, Any]:
        """
        批量重命名文件
        
        Args:
            file_list: 文件列表
            pattern: 重命名模式
            output_dir: 输出目录
            **kwargs: 额外参数
            
        Returns:
            重命名结果字典
        """
        pass
    
    @abstractmethod
    def copy_files(self, file_list: List[str], output_dir: str, 
                  preserve_structure: bool = True) -> Dict[str, Any]:
        """
        批量复制文件
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            preserve_structure: 是否保持目录结构
            
        Returns:
            复制结果字典
        """
        pass
    
    @abstractmethod
    def move_files(self, file_list: List[str], output_dir: str,
                  preserve_structure: bool = True) -> Dict[str, Any]:
        """
        批量移动文件
        
        Args:
            file_list: 文件列表
            output_dir: 输出目录
            preserve_structure: 是否保持目录结构
            
        Returns:
            移动结果字典
        """
        pass
    
    @abstractmethod
    def delete_files(self, file_list: List[str], 
                    backup: bool = False, backup_dir: str = None) -> Dict[str, Any]:
        """
        批量删除文件
        
        Args:
            file_list: 文件列表
            backup: 是否备份
            backup_dir: 备份目录
            
        Returns:
            删除结果字典
        """
        pass