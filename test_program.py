"""
King_photo - 测试脚本
测试各个核心功能
"""

import os
import sys
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.format_detector import FormatDetector
from src.core.metadata_reader import MetadataReader
from src.core.file_processor import FileProcessor
from src.core.repair_engine import RepairEngine
from src.utils.helpers import extract_time_from_filename, format_datetime


def test_format_detection(test_dir):
    """测试格式检测"""
    print("\n" + "=" * 60)
    print("测试1: 格式检测")
    print("=" * 60)

    results = {
        'total': 0,
        'consistent': 0,
        'inconsistent': 0,
        'formats': {}
    }

    for filename in os.listdir(test_dir):
        filepath = os.path.join(test_dir, filename)
        if not os.path.isfile(filepath):
            continue

        results['total'] += 1

        # 检测格式
        format_name, is_consistent = FormatDetector.get_real_format(filepath)
        ext = os.path.splitext(filename)[1].lower()

        # 统计格式
        if format_name not in results['formats']:
            results['formats'][format_name] = 0
        results['formats'][format_name] += 1

        if is_consistent:
            results['consistent'] += 1
        else:
            results['inconsistent'] += 1
            print(f"  后缀不一致: {filename}")
            print(f"    扩展名: {ext}, 实际格式: {format_name}")

    print(f"\n统计结果:")
    print(f"  总文件数: {results['total']}")
    print(f"  后缀正确: {results['consistent']}")
    print(f"  后缀错误: {results['inconsistent']}")
    print(f"\n格式分布:")
    for fmt, count in sorted(results['formats'].items(), key=lambda x: -x[1]):
        print(f"  {fmt}: {count}")

    return results


def test_time_extraction(test_dir):
    """测试时间提取"""
    print("\n" + "=" * 60)
    print("测试2: 时间提取（从文件名）")
    print("=" * 60)

    results = {
        'total': 0,
        'extracted': 0,
        'failed': 0,
        'samples': []
    }

    for filename in os.listdir(test_dir):
        filepath = os.path.join(test_dir, filename)
        if not os.path.isfile(filepath):
            continue

        results['total'] += 1

        # 从文件名提取时间
        dt = extract_time_from_filename(filename)

        if dt:
            results['extracted'] += 1
            if len(results['samples']) < 10:
                results['samples'].append((filename, dt))
        else:
            results['failed'] += 1

    print(f"\n统计结果:")
    print(f"  总文件数: {results['total']}")
    print(f"  成功提取: {results['extracted']}")
    print(f"  提取失败: {results['failed']}")

    print(f"\n提取成功示例:")
    for filename, dt in results['samples']:
        print(f"  {filename}")
        print(f"    -> {format_datetime(dt)}")

    return results


def test_metadata_reading(test_dir):
    """测试元信息读取"""
    print("\n" + "=" * 60)
    print("测试3: 元信息读取")
    print("=" * 60)

    results = {
        'total': 0,
        'has_datetime': 0,
        'no_datetime': 0,
        'sources': {'exif': 0, 'xmp': 0, 'filename': 0, 'none': 0}
    }

    sample_files = []

    for filename in os.listdir(test_dir):
        filepath = os.path.join(test_dir, filename)
        if not os.path.isfile(filepath):
            continue

        results['total'] += 1

        # 读取元信息
        metadata = MetadataReader.read_metadata(filepath)

        if metadata.get('datetime'):
            results['has_datetime'] += 1
        else:
            results['no_datetime'] += 1

        # 每种格式取一个样本
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [s[0] for s in sample_files] and len(sample_files) < 5:
            sample_files.append((ext, filename, metadata))

    print(f"\n统计结果:")
    print(f"  总文件数: {results['total']}")
    print(f"  有拍摄时间: {results['has_datetime']}")
    print(f"  无拍摄时间: {results['no_datetime']}")

    print(f"\n样本详情:")
    for ext, filename, metadata in sample_files:
        print(f"\n  文件: {filename}")
        print(f"    格式: {metadata.get('format', 'Unknown')}")
        print(f"    尺寸: {metadata.get('width', 0)} x {metadata.get('height', 0)}")
        print(f"    拍摄时间: {format_datetime(metadata.get('datetime'))}")
        print(f"    相机: {metadata.get('make', '')} {metadata.get('model', '')}")

    return results


def test_rename_format(test_dir):
    """测试重命名格式"""
    print("\n" + "=" * 60)
    print("测试4: 重命名格式生成")
    print("=" * 60)

    from src.utils.helpers import generate_renamed_filename

    # 测试格式
    test_formats = [
        "{datetime}_{original}",
        "{date}_{seq}",
        "{camera}_{datetime}",
        "{year}{month}{day}_{original}",
    ]

    # 取一个样本文件
    sample_file = None
    for filename in os.listdir(test_dir):
        if filename.lower().endswith(('.jpg', '.jpeg')):
            sample_file = os.path.join(test_dir, filename)
            break

    if not sample_file:
        print("未找到样本文件")
        return

    metadata = MetadataReader.read_metadata(sample_file)
    original_name = os.path.splitext(os.path.basename(sample_file))[0]

    print(f"\n样本文件: {os.path.basename(sample_file)}")
    print(f"拍摄时间: {format_datetime(metadata.get('datetime'))}")
    print(f"相机: {metadata.get('make', '')} {metadata.get('model', '')}")

    print(f"\n重命名格式测试:")
    for fmt in test_formats:
        new_name = generate_renamed_filename(
            original_name, fmt, metadata, 1, '.jpg'
        )
        print(f"  格式: {fmt}")
        print(f"    -> {new_name}")


def test_batch_operations(test_dir, output_dir):
    """测试批量操作"""
    print("\n" + "=" * 60)
    print("测试5: 批量操作")
    print("=" * 60)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 获取前5个文件进行测试
    test_files = []
    for filename in os.listdir(test_dir)[:5]:
        filepath = os.path.join(test_dir, filename)
        if os.path.isfile(filepath):
            test_files.append(filepath)

    print(f"\n测试文件数: {len(test_files)}")

    # 测试批量重命名
    print("\n[测试] 批量重命名...")
    rename_result = FileProcessor.batch_rename(
        test_files,
        rename_format="{datetime}_{original}",
        output_dir=output_dir,
        copy_mode=True
    )
    print(f"  成功: {rename_result['success']}")
    print(f"  失败: {rename_result['failed']}")

    # 测试批量时间修复
    print("\n[测试] 批量时间修复...")
    time_result = FileProcessor.batch_fix_time(
        test_files,
        output_dir=output_dir,
        copy_mode=True
    )
    print(f"  成功: {time_result['success']}")
    print(f"  失败: {time_result['failed']}")
    print(f"  跳过: {time_result['skipped']}")

    # 测试批量后缀修复
    print("\n[测试] 批量后缀修复...")
    ext_result = RepairEngine.batch_repair_extension(
        test_files,
        output_dir=output_dir,
        copy_mode=True
    )
    print(f"  修复: {ext_result['fixed']}")
    print(f"  跳过: {ext_result['skipped']}")
    print(f"  失败: {ext_result['failed']}")

    return {
        'rename': rename_result,
        'time': time_result,
        'extension': ext_result
    }


def main():
    """主测试函数"""
    print("King_photo 功能测试")
    print("=" * 60)

    test_dir = r"F:\Download\temp(King)\图片处理\test\修复前"
    output_dir = r"F:\Download\temp(King)\图片处理\test\修复后"

    if not os.path.exists(test_dir):
        print(f"错误: 测试目录不存在: {test_dir}")
        return

    # 运行测试
    start_time = time.time()

    format_results = test_format_detection(test_dir)
    time_results = test_time_extraction(test_dir)
    metadata_results = test_metadata_reading(test_dir)
    test_rename_format(test_dir)
    batch_results = test_batch_operations(test_dir, output_dir)

    elapsed = time.time() - start_time

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总耗时: {elapsed:.2f}秒")
    print(f"测试文件数: {format_results['total']}")
    print(f"格式检测: 后缀正确 {format_results['consistent']}, 错误 {format_results['inconsistent']}")
    print(f"时间提取: 成功 {time_results['extracted']}, 失败 {time_results['failed']}")
    print(f"元信息读取: 有时间 {metadata_results['has_datetime']}, 无时间 {metadata_results['no_datetime']}")
    print(f"\n批量操作结果:")
    print(f"  重命名: 成功 {batch_results['rename']['success']}")
    print(f"  时间修复: 成功 {batch_results['time']['success']}")
    print(f"  后缀修复: 修复 {batch_results['extension']['fixed']}")

    # 清理测试输出
    print(f"\n测试输出目录: {output_dir}")
    print("（测试文件已保存在输出目录，可手动查看）")


if __name__ == "__main__":
    main()
