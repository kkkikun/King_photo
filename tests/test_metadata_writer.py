"""
King_photo - 元信息写入引擎测试
测试 MetadataWriter 类的所有方法
"""

import os
import pytest
from datetime import datetime
from src.core.metadata_writer import MetadataWriter


class TestWriteMetadata:
    """测试 write_metadata 方法"""

    def test_write_metadata_returns_dict(self, tmp_copy_jpg):
        """测试写入元信息返回字典"""
        metadata = {'artist': 'Test Author'}
        result = MetadataWriter.write_metadata(tmp_copy_jpg, metadata)
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'message' in result

    def test_write_metadata_success(self, tmp_copy_jpg):
        """测试写入成功"""
        metadata = {'artist': 'Write Test'}
        result = MetadataWriter.write_metadata(tmp_copy_jpg, metadata, copy_mode=False)
        assert result['success'] is True

    def test_write_metadata_copy_mode(self, tmp_copy_jpg, tmp_output_dir):
        """测试复制模式"""
        metadata = {'artist': 'Copy Test'}
        result = MetadataWriter.write_metadata(
            tmp_copy_jpg, metadata, copy_mode=True, output_dir=tmp_output_dir
        )
        assert result['success'] is True
        assert result['output_path'] != tmp_copy_jpg
        assert os.path.exists(result['output_path'])

    def test_write_metadata_nonexistent_file(self):
        """测试不存在的文件"""
        result = MetadataWriter.write_metadata('/nonexistent/file.jpg', {'artist': 'Test'})
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_write_metadata_multiple_fields(self, tmp_copy_jpg):
        """测试写入多个字段"""
        metadata = {
            'artist': 'Multi Author',
            'copyright': '2024 Test',
            'description': 'Test Description',
        }
        result = MetadataWriter.write_metadata(tmp_copy_jpg, metadata, copy_mode=False)
        assert result['success'] is True

    def test_write_metadata_with_datetime(self, tmp_copy_jpg):
        """测试写入时间字段"""
        metadata = {
            'datetime': datetime(2024, 6, 15, 12, 30, 0),
        }
        result = MetadataWriter.write_metadata(tmp_copy_jpg, metadata, copy_mode=False)
        assert result['success'] is True


class TestBatchWriteMetadata:
    """测试 batch_write_metadata 方法"""

    def test_batch_write_returns_dict(self, sample_jpg, tmp_output_dir):
        """测试批量写入返回字典"""
        metadata = {'artist': 'Batch Test'}
        result = MetadataWriter.batch_write_metadata(
            [sample_jpg], metadata, output_dir=tmp_output_dir
        )
        assert isinstance(result, dict)
        assert 'total' in result
        assert 'success' in result
        assert 'failed' in result

    def test_batch_write_counts(self, sample_jpg, tmp_output_dir):
        """测试批量写入计数"""
        metadata = {'artist': 'Count Test'}
        result = MetadataWriter.batch_write_metadata(
            [sample_jpg], metadata, output_dir=tmp_output_dir
        )
        assert result['total'] == 1
        assert result['success'] + result['failed'] == 1

    def test_batch_write_with_progress_callback(self, sample_jpg, tmp_output_dir):
        """测试带进度回调"""
        metadata = {'artist': 'Progress Test'}
        progress_calls = []

        def callback(current, total, filename):
            progress_calls.append((current, total, filename))

        result = MetadataWriter.batch_write_metadata(
            [sample_jpg], metadata, output_dir=tmp_output_dir,
            progress_callback=callback
        )
        assert len(progress_calls) == 1
        assert progress_calls[0][0] == 1
        assert progress_calls[0][1] == 1

    def test_batch_write_empty_list(self, tmp_output_dir):
        """测试空文件列表"""
        metadata = {'artist': 'Empty Test'}
        result = MetadataWriter.batch_write_metadata(
            [], metadata, output_dir=tmp_output_dir
        )
        assert result['total'] == 0
        assert result['success'] == 0
        assert result['failed'] == 0
