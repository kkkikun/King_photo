"""
King_photo - 打包脚本
使用PyInstaller打包为exe
"""

import os
import sys
import subprocess
import shutil


def build_exe():
    """打包为exe"""
    print("=" * 50)
    print("King_photo 打包脚本")
    print("=" * 50)

    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: 请先安装PyInstaller")
        print("运行: pip install pyinstaller")
        sys.exit(1)

    # 清理旧的构建文件
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"清理 {folder} 文件夹...")
            shutil.rmtree(folder)

    if os.path.exists('King_photo.spec'):
        os.remove('King_photo.spec')

    # PyInstaller参数
    args = [
        'pyinstaller',
        '--name=King_photo',
        '--windowed',  # 无控制台窗口
        '--onefile',   # 单文件
        '--clean',     # 清理缓存
        '--noconfirm', # 不确认覆盖
    ]

    # 添加图标（如果存在）
    icon_path = os.path.join('assets', 'icon.ico')
    if os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
        print(f"使用图标: {icon_path}")

    # 添加数据文件
    # args.append('--add-data=assets;assets')

    # 入口文件
    args.append('src/main.py')

    # 执行打包
    print("\n开始打包...")
    print(f"命令: {' '.join(args)}")
    print("-" * 50)

    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        print(result.stdout)

        # 检查输出文件
        exe_path = os.path.join('dist', 'King_photo.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print("\n" + "=" * 50)
            print(f"打包成功!")
            print(f"输出文件: {exe_path}")
            print(f"文件大小: {size_mb:.1f} MB")
            print("=" * 50)
        else:
            print("\n错误: 未找到输出文件")

    except subprocess.CalledProcessError as e:
        print(f"\n打包失败!")
        print(f"错误信息: {e.stderr}")
        sys.exit(1)


def create_assets():
    """创建资源文件夹"""
    assets_dir = 'assets'
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        print(f"创建 {assets_dir} 文件夹")

        # 创建简单的图标提示文件
        readme_path = os.path.join(assets_dir, 'README.txt')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("请在此文件夹放置 icon.ico 作为应用图标\n")
            f.write("图标建议尺寸: 256x256 像素\n")


def install_dependencies():
    """安装依赖"""
    print("安装依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                      check=True, capture_output=True, text=True)
        print("依赖安装成功!")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e.stderr}")
        sys.exit(1)


if __name__ == '__main__':
    # 创建资源文件夹
    create_assets()

    # 安装依赖
    if '--install' in sys.argv:
        install_dependencies()

    # 打包
    build_exe()
