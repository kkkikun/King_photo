"""
King_photo - 文件处理模块测试
测试 FileProcessor 类的所有方法
"""

import os
import shutil
import pytest
from datetime import datetime
from src.core.file_processor import FileProcessor


class TestRenameFile:
    """测试 rename_file 方法"""

    def test_rename_returns_dict(self, tmp_copy_jpg):
        """测试返回字典"""
        result = FileProcessor.rename_file(tmp_copy_jpg, '{original}')
        assert isinstance(result, dict)
        assert 'success' in result

    def test_rename_success(self, tmp_copy_jpg, tmp_output_dir):
        """测试重命名成功"""
        result = FileProcessor.rename_file(
            tmp_copy_jpg, '{original}', output_dir=tmp_output_dir
        )
        assert result['success'] is True
        assert 'new_path' in result
        assert os.path.exists(result['new_path'])

    def test_rename_with_datetime_format(self, tmp_copy_jpg, tmp_output_dir):
        """测试使用日期时间格式重命名"""
        result = FileProcessor.rename_file(
            tmp_copy_jpg, '{datetime}', output_dir=tmp_output_dir
        )
        assert result['success'] is True

    def test_rename_nonexistent_file(self):
        """测试不存在的文件"""
        result = FileProcessor.rename_file('/nonexistent/file.jpg')
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_rename_with_sequence(self, tmp_copy_jpg, tmp_output_dir):
        """测试带序号重命名"""
        result = FileProcessor.rename_file(
            tmp_copy_jpg, 'photo_{seq}', output_dir=tmp_output_dir, sequence=5
        )
        assert result['success'] is True

    def test_rename_preserves_original(self, tmp_copy_jpg, tmp_output_dir):
        """测试复制模式保留原文件"""
        original_path = tmp_copy_jpg
        result = FileProcessor.rename_file(
            original_path, '{original}', output_dir=tmp_output_dir, copy_mode=True
        )
        assert result['success'] is True
        assert os.path.exists(original_path)  # 原文件还在


class TestFixFileTime:
    """测试 fix_file_time 方法"""

    def test_fix_time_returns_dict(self, sample_jpg, tmp_output_dir):
        """测试返回字典"""
        result = FileProcessor.fix_file_time(sample_jpg, output_dir=tmp_output_dir)
        assert isinstance(result, dict)
        assert 'success' in result

    def test_fix_time_nonexistent_file(self):
        """测试不存在的文件"""
        result = FileProcessor.fix_file_time('/nonexistent/file.jpg')
        assert result['success'] is False

    def test_fix_time_with_exif(self, sample_jpg, tmp_output_dir):
        """测试修复有 EXIF 时间的文件"""
        result = FileProcessor.fix_file_time(sample_jpg, output_dir=tmp_output_dir)
        # 可能成功也可能失败（取决于是否有拍摄时间）
        assert isinstance(result, dict)


class TestBatchRename:
    """测试 batch_rename 方法"""

    def test_batch_rename_returns_dict(self, sample_jpg, tmp_output_dir):
        """测试返回字典"""
        result = FileProcessor.batch_rename(
            [sample_jpg], '{original}', output_dir=tmp_output_dir
        )
        assert isinstance(result, dict)
        assert 'total' in result
        assert 'success' in result
        assert 'failed' in result

    def test_batch_rename_empty_list(self, tmp_output_dir):
        """测试空文件列表"""
        result = FileProcessor.batch_rename([], output_dir=tmp_output_dir)
        assert result['total'] == 0

    def test_batch_rename_with_callback(self, sample_jpg, tmp_output_dir):
        """测试带进度回调"""
        progress_calls = []

        def callback(current, total, filename):
            progress_calls.append((current, total, filename))

        result = FileProcessor.batch_rename(
            [sample_jpg], '{original}', output_dir=tmp_output_dir,
            progress_callback=callback
        )
        assert len(progress_calls) == 1


class TestBatchFixTime:
    """测试 batch_fix_time 方法"""

    def test_batch_fix_time_returns_dict(self, sample_jpg, tmp_output_dir):
        """测试返回字典"""
        result = FileProcessor.batch_fix_time(
            [sample_jpg], output_dir=tmp_output_dir
        )
        assert isinstance(result, dict)
        assert 'total' in result
        assert 'success' in result
        assert 'failed' in result
        assert 'skipped' in result

    def test_batch_fix_time_empty_list(self):
        """测试空文件列表"""
        result = FileProcessor.batch_fix_time([])
        assert result['total'] == 0


class TestCopyFiles:
    """测试 copy_files 方法"""

    def test_copy_returns_dict(self, sample_jpg, tmp_output_dir):
        """测试返回字典"""
        result = FileProcessor.copy_files([sample_jpg], tmp_output_dir)
        assert isinstance(result, dict)
        assert 'total' in result
        assert 'success' in result
        assert 'failed' in result

    def test_copy_success(self, sample_jpg, tmp_output_dir):
        """测试复制成功"""
        result = FileProcessor.copy_files([sample_jpg], tmp_output_dir)
        assert result['success'] == 1
        # 检查文件确实被复制
        dest = os.path.join(tmp_output_dir, os.path.basename(sample_jpg))
        assert os.path.exists(dest)

    def test_copy_multiple_files(self, sample_jpg, sample_png, tmp_output_dir):
        """测试复制多个文件"""
        files = [sample_jpg, sample_png]
        result = FileProcessor.copy_files(files, tmp_output_dir)
        assert result['total'] == 2
        assert result['success'] == 2
