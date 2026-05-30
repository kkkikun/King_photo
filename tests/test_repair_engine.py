"""
King_photo - 修复引擎测试
测试 RepairEngine 类的所有方法
"""

import os
import shutil
import pytest
from datetime import datetime
from src.core.repair_engine import RepairEngine


class TestCheckFileExtension:
    """测试 check_file_extension 方法"""

    def test_check_extension_returns_dict(self, sample_jpg):
        """测试返回字典"""
        result = RepairEngine.check_file_extension(sample_jpg)
        assert isinstance(result, dict)
        assert 'needs_fix' in result
        assert 'current_ext' in result
        assert 'correct_ext' in result
        assert 'real_format' in result
        assert 'is_consistent' in result

    def test_check_extension_jpg(self, sample_jpg):
        """测试 JPG 文件"""
        result = RepairEngine.check_file_extension(sample_jpg)
        assert result['current_ext'] == '.jpg'


class TestFixExtension:
    """测试 fix_extension 方法"""

    def test_fix_extension_returns_dict(self, sample_jpg, tmp_output_dir):
        """测试返回字典"""
        result = RepairEngine.fix_extension(sample_jpg, tmp_output_dir)
        assert isinstance(result, dict)
        assert 'success' in result

    def test_fix_extension_nonexistent(self):
        """测试不存在的文件"""
        result = RepairEngine.fix_extension('/nonexistent/file.jpg')
        assert result['success'] is False


class TestExtractTimeInfo:
    """测试 extract_time_info 方法"""

    def test_extract_time_info_returns_dict(self, sample_jpg):
        """测试返回字典"""
        result = RepairEngine.extract_time_info(sample_jpg)
        assert isinstance(result, dict)
        assert 'from_filename' in result
        assert 'from_metadata' in result
        assert 'best_match' in result
        assert 'source' in result

    def test_extract_time_info_mmexport(self):
        """测试 mmexport 格式的文件名时间提取"""
        # mmexport1693274216447.jpg
        import tempfile
        tmp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(tmp_dir, 'mmexport1693274216447.jpg')
            with open(test_file, 'w') as f:
                f.write('test')
            result = RepairEngine.extract_time_info(test_file)
            assert result['from_filename'] is not None
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_extract_time_info_date_format(self):
        """测试日期格式的文件名时间提取"""
        import tempfile
        tmp_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(tmp_dir, '20230816_193756.jpg')
            with open(test_file, 'w') as f:
                f.write('test')
            result = RepairEngine.extract_time_info(test_file)
            assert result['from_filename'] is not None
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
