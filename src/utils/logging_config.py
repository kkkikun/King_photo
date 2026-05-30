"""
King_photo - 日志配置模块
提供统一的日志配置和获取方式
每次运行只保留最新一次日志，按级别分类，报错信息在前
"""

import os
import logging
import atexit
from datetime import datetime
from typing import List


class CategorizedLogStorage:
    """分类日志存储，在程序退出时写入文件"""
    
    def __init__(self):
        self._errors: List[str] = []
        self._warnings: List[str] = []
        self._infos: List[str] = []
        self._debugs: List[str] = []
        self._formatter = None
        self._log_file = None
        
    def set_formatter(self, formatter: logging.Formatter):
        """设置日志格式化器"""
        self._formatter = formatter
        
    def set_log_file(self, log_file: str):
        """设置日志文件路径"""
        self._log_file = log_file
        
    def add_record(self, record: logging.LogRecord):
        """添加日志记录"""
        if self._formatter is None:
            self._formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
        msg = self._formatter.format(record)
        
        if record.levelno >= logging.ERROR:
            self._errors.append(msg)
        elif record.levelno >= logging.WARNING:
            self._warnings.append(msg)
        elif record.levelno >= logging.INFO:
            self._infos.append(msg)
        else:
            self._debugs.append(msg)
            
    def flush_to_file(self):
        """将分类的日志写入文件，错误信息在前"""
        if not self._log_file:
            return
            
        try:
            # 按级别顺序写入：ERROR -> WARNING -> INFO -> DEBUG
            all_logs = self._errors + self._warnings + self._infos + self._debugs
            
            # 使用覆盖模式写入
            with open(self._log_file, 'w', encoding='utf-8') as f:
                if all_logs:
                    f.write('\n'.join(all_logs) + '\n')
                    
        except Exception as e:
            print(f"写入日志文件失败: {e}")


# 全局分类日志存储实例
_log_storage = CategorizedLogStorage()


class CategorizedHandler(logging.Handler):
    """分类日志处理器"""
    
    def __init__(self, storage: CategorizedLogStorage):
        super().__init__()
        self._storage = storage
        
    def emit(self, record: logging.LogRecord):
        """将日志记录添加到分类存储"""
        self._storage.add_record(record)


def setup_logging(log_dir: str = None, log_level: int = logging.INFO):
    """
    设置日志配置

    Args:
        log_dir: 日志文件目录，默认为程序运行目录下的logs文件夹
        log_level: 日志级别
    """
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')

    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 生成日志文件名（固定名称，每次运行覆盖）
    log_file = os.path.join(log_dir, 'king_photo.log')
    
    # 设置分类日志存储
    _log_storage.set_log_file(log_file)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 分类文件处理器（按级别分类，错误在前）
    file_handler = CategorizedHandler(_log_storage)
    file_handler.setLevel(log_level)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    _log_storage.set_formatter(formatter)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 注册程序退出时刷新日志
    atexit.register(_log_storage.flush_to_file)


