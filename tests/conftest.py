"""
King_photo - pytest 配置和共享 fixtures
"""

import os
import sys
import shutil
import tempfile
import pytest

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 测试图片目录 - 使用绝对路径避免编码问题
TEST_IMAGES_DIR = r'f:\Download\temp(King)\图片处理\test'
TEST_FIX_DIR = os.path.join(TEST_IMAGES_DIR, '修复前')
TEST_OTHER_DIR = os.path.join(TEST_IMAGES_DIR, '其他')


@pytest.fixture(scope='session')
def test_images_dir():
    """测试图片根目录"""
    return TEST_IMAGES_DIR


@pytest.fixture(scope='session')
def test_fix_dir():
    """修复前测试图片目录"""
    return TEST_FIX_DIR


@pytest.fixture(scope='session')
def test_other_dir():
    """其他测试图片目录"""
    return TEST_OTHER_DIR


@pytest.fixture(scope='session')
def sample_jpg():
    """获取一个测试用的 JPG 文件路径"""
    # 从 test/其他 目录找一个 jpg
    for f in os.listdir(TEST_OTHER_DIR):
        if f.lower().endswith('.jpg'):
            return os.path.join(TEST_OTHER_DIR, f)
    pytest.skip("没有找到测试用的 JPG 文件")


@pytest.fixture(scope='session')
def sample_png():
    """获取一个测试用的 PNG 文件路径"""
    for f in os.listdir(TEST_OTHER_DIR):
        if f.lower().endswith('.png'):
            return os.path.join(TEST_OTHER_DIR, f)
    pytest.skip("没有找到测试用的 PNG 文件")


@pytest.fixture(scope='session')
def sample_jpeg():
    """获取一个测试用的 JPEG 文件路径"""
    for f in os.listdir(TEST_OTHER_DIR):
        if f.lower().endswith('.jpeg'):
            return os.path.join(TEST_OTHER_DIR, f)
    pytest.skip("没有找到测试用的 JPEG 文件")


@pytest.fixture(scope='session')
def sample_webp():
    """获取一个测试用的 WebP 文件路径"""
    for f in os.listdir(TEST_OTHER_DIR):
        if f.lower().endswith('.webp'):
            return os.path.join(TEST_OTHER_DIR, f)
    pytest.skip("没有找到测试用的 WebP 文件")


@pytest.fixture
def tmp_output_dir():
    """创建临时输出目录，测试结束后删除"""
    tmp_dir = tempfile.mkdtemp(prefix='king_photo_test_')
    yield tmp_dir
    # 清理
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def tmp_copy_jpg(sample_jpg, tmp_output_dir):
    """复制一份 JPG 到临时目录，避免修改原始测试文件"""
    dst = os.path.join(tmp_output_dir, os.path.basename(sample_jpg))
    shutil.copy2(sample_jpg, dst)
    return dst


@pytest.fixture
def tmp_copy_png(sample_png, tmp_output_dir):
    """复制一份 PNG 到临时目录"""
    dst = os.path.join(tmp_output_dir, os.path.basename(sample_png))
    shutil.copy2(sample_png, dst)
    return dst
