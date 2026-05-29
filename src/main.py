"""
King_photo - 程序入口
图片元信息编辑与修复工具
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 注册HEIC/HEIF格式支持
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    # HEIC/HEIF格式已注册，可以处理.heic和.heif文件
except ImportError:
    # pillow-heif未安装，HEIC/HEIF格式将无法预览
    pass

from src.utils.logging_config import setup_logging
from src.ui.app import MainWindow


def main():
    """主函数"""
    # 设置日志
    setup_logging()

    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
