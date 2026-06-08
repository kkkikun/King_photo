"""
King_photo API 使用示例（v1.7.1）
演示如何使用模块化API — 包括格式检测、元数据读写、修复、格式影响查询、图片加载
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api import KingPhotoAPI, get_api
from src.utils.image_loader import load_image, get_available_formats
from src.utils.format_impact import get_impact, should_prompt_user


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 创建API实例
    api = KingPhotoAPI()
    
    # 检测文件格式
    test_file = "test_image.jpg"
    if os.path.exists(test_file):
        format_info = api.detect_format(test_file)
        print(f"文件格式: {format_info.get('format', '未知')}")
        
        # 读取元数据
        metadata = api.read_metadata(test_file)
        print(f"拍摄时间: {metadata.get('datetime', '未知')}")
        print(f"文件大小: {metadata.get('filesize', 0)} 字节")
        
        # 获取拍摄时间
        dt = api.get_datetime(test_file)
        if dt:
            print(f"拍摄时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")


def example_metadata_operations():
    """元数据操作示例"""
    print("\n=== 元数据操作示例 ===")
    
    api = KingPhotoAPI()
    
    test_file = "test_image.jpg"
    if os.path.exists(test_file):
        # 读取EXIF数据
        exif_data = api.read_exif(test_file)
        print(f"EXIF数据: {len(exif_data)} 个字段")
        
        # 读取XMP数据
        xmp_data = api.read_xmp(test_file)
        print(f"XMP数据: {len(xmp_data)} 个字段")
        
        # 写入元数据
        new_metadata = {
            "title": "测试图片",
            "author": "King_photo",
            "description": "这是一个测试图片"
        }
        
        result = api.write_metadata(test_file, new_metadata, copy_mode=True)
        if result.get("success"):
            print(f"元数据写入成功: {result.get('output_path', '')}")
        else:
            print(f"元数据写入失败: {result.get('error', '')}")


def example_repair_operations():
    """修复操作示例"""
    print("\n=== 修复操作示例 ===")
    
    api = KingPhotoAPI()
    
    test_file = "test_image.jpg"
    if os.path.exists(test_file):
        # 检查文件后缀
        check_result = api.check_file_extension(test_file)
        print(f"文件后缀检查: {check_result.get('need_fix', False)}")
        
        # 提取时间信息
        time_info = api.extract_time_info(test_file)
        print(f"时间信息: {time_info.get('datetime', '未知')}")
        
        # 修复文件
        repair_result = api.repair_file(test_file, output_dir="repaired")
        print(f"修复结果: {repair_result.get('success', False)}")


def example_batch_operations():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===")
    
    api = KingPhotoAPI()
    
    # 获取文件夹中的图片
    folder = "test_images"
    if os.path.exists(folder):
        files = api.get_image_files(folder)
        print(f"找到 {len(files)} 个图片文件")
        
        if files:
            # 批量修复
            def progress_callback(current, total):
                print(f"进度: {current}/{total} ({current*100//total}%)")
            
            batch_result = api.batch_repair(
                files[:5],  # 只处理前5个文件
                output_dir="batch_repaired",
                progress_callback=progress_callback
            )
            
            print(f"批量修复完成:")
            print(f"  总数: {batch_result.get('total', 0)}")
            print(f"  成功: {batch_result.get('success', 0)}")
            print(f"  失败: {batch_result.get('failed', 0)}")


def example_plugin_operations():
    """插件操作示例"""
    print("\n=== 插件操作示例 ===")
    
    api = KingPhotoAPI()
    
    # 获取已注册的插件
    plugins = api.get_plugins()
    print(f"已注册插件: {len(plugins)} 个")
    
    for plugin in plugins:
        print(f"  - {plugin['name']} ({plugin['type']}): {plugin['description']}")
    
    # 获取支持的格式
    formats = api.get_supported_formats()
    print(f"支持的格式: {len(formats)} 个")
    
    # 使用功能插件（如果有）
    function_plugins = [p for p in plugins if p['type'] == 'function']
    if function_plugins:
        plugin_name = function_plugins[0]['name']
        print(f"执行功能插件: {plugin_name}")
        
        # 这里可以调用插件执行
        # result = api._plugin_manager.execute_function_plugin(plugin_name, file_list)


def example_configuration():
    """配置管理示例"""
    print("\n=== 配置管理示例 ===")
    
    api = KingPhotoAPI()
    
    # 获取配置
    window_width = api.get_config("window.width", 1200)
    print(f"窗口宽度: {window_width}")
    
    # 设置配置
    api.set_config("window.width", 1400)
    print("配置已更新")
    
    # 保存配置
    api.save_config()
    print("配置已保存")


def example_format_impact():
    """格式影响查询示例（v1.7.1）"""
    print("\n=== 格式影响查询 ===")
    
    # HEIC 伪装成 PNG → CRITICAL
    impact = get_impact("HEIF", "PNG")
    print("  HEIF→PNG: level={}, recommend_fix={}".format(impact['level'], impact['recommend_fix']))
    print("    {}".format(impact['reason']))
    
    # PNG 伪装成 JPEG → HIGH（透明通道丢失）
    impact2 = get_impact("PNG", "JPEG")
    print("  PNG→JPEG: level={}, recommend_fix={}".format(impact2['level'], impact2['recommend_fix']))
    
    # MOV 伪装成 JPG → NONE（不应修复）
    impact3 = get_impact("MOV", "JPEG")
    print("  MOV→JPEG: level={}, recommend_fix={}".format(impact3['level'], impact3['recommend_fix']))
    
    # 检查是否需要弹窗
    print("  should_prompt(HEIF,PNG) = {}".format(should_prompt_user("HEIF", "PNG")))  # True
    print("  should_prompt(JPEG,PNG) = {}".format(should_prompt_user("JPEG", "PNG")))  # False


def example_image_loader():
    """图片加载器示例（v1.7.1）"""
    print("\n=== 图片加载器 ===")
    
    fmt = get_available_formats()
    print("  可用格式: {}".format({k: v for k, v in fmt.items() if v}))
    
    # 示例：加载图片
    test_file = os.path.join(os.path.dirname(__file__), "test", "sample.jpg")
    if os.path.exists(test_file):
        img, err = load_image(test_file)
        if img:
            print("  加载成功: {}x{}".format(img.width, img.height))
            img.close()
        else:
            print("  加载失败: {}".format(err))


def main():
    """主函数"""
    print("King_photo API 使用示例")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_metadata_operations()
        example_repair_operations()
        example_batch_operations()
        example_plugin_operations()
        example_configuration()
        
        # v1.7.1 新增
        example_format_impact()
        example_image_loader()
        
        print("\n" + "=" * 50)
        print("所有示例执行完成")
        
    except Exception as e:
        print(f"执行示例时出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()