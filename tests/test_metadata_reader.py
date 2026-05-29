"""
King_photo - 元信息读取引擎测试
测试 MetadataReader 类的所有方法
"""

import os
import pytest
from datetime import datetime
from src.core.metadata_reader import MetadataReader


class TestReadMetadata:
    """测试 read_metadata 方法"""

    def test_read_metadata_returns_dict(self, sample_jpg):
        """测试读取元信息返回字典"""
        result = MetadataReader.read_metadata(sample_jpg)
        assert isinstance(result, dict)

    def test_read_metadata_has_basic_fields(self, sample_jpg):
        """测试返回结果包含基本字段"""
        result = MetadataReader.read_metadata(sample_jpg)
        assert 'filepath' in result
        assert 'filename' in result
        assert 'extension' in result
        assert 'filesize' in result

    def test_read_metadata_filesize(self, sample_jpg):
        """测试文件大小字段"""
        result = MetadataReader.read_metadata(sample_jpg)
        assert result['filesize'] > 0

    def test_read_metadata_has_format_info(self, sample_jpg):
        """测试包含格式信息"""
        result = MetadataReader.read_metadata(sample_jpg)
        assert 'format' in result
        assert 'supports_exif' in result
        assert 'supports_xmp' in result

    def test_read_metadata_has_dimensions(self, sample_jpg):
        """测试包含图片尺寸"""
        result = MetadataReader.read_metadata(sample_jpg)
        assert 'width' in result
        assert 'height' in result

    def test_read_metadata_nonexistent_file(self):
        """测试不存在的文件"""
        result = MetadataReader.read_metadata('/nonexistent/file.jpg')
        assert 'error' in result
        assert result['error'] == '文件不存在'

    def test_read_metadata_png(self, sample_png):
        """测试读取 PNG 元信息"""
        result = MetadataReader.read_metadata(sample_png)
        assert result['format'] == 'PNG'
        assert 'width' in result
        assert 'height' in result

    def test_read_metadata_jpeg(self, sample_jpeg):
        """测试读取 JPEG 元信息"""
        result = MetadataReader.read_metadata(sample_jpeg)
        assert result['format'] == 'JPEG'

    def test_read_metadata_file_times(self, sample_jpg):
        """测试包含文件时间"""
        result = MetadataReader.read_metadata(sample_jpg)
        assert 'file_created' in result
        assert 'file_modified' in result
        assert isinstance(result['file_created'], datetime)
        assert isinstance(result['file_modified'], datetime)


class TestGetImageSize:
    """测试 _get_image_size 方法"""

    def test_get_image_size_returns_tuple(self, sample_jpg):
        """测试返回元组"""
        width, height = MetadataReader._get_image_size(sample_jpg)
        assert isinstance(width, int)
        assert isinstance(height, int)

    def test_get_image_size_positive(self, sample_jpg):
        """测试尺寸为正数"""
        width, height = MetadataReader._get_image_size(sample_jpg)
        assert width > 0
        assert height > 0

    def test_get_image_size_nonexistent(self):
        """测试不存在的文件"""
        width, height = MetadataReader._get_image_size('/nonexistent/file.jpg')
        assert width == 0
        assert height == 0


class TestGetDatetime:
    """测试 get_datetime 方法"""

    def test_get_datetime_returns_datetime_or_none(self, sample_jpg):
        """测试返回 datetime 或 None"""
        result = MetadataReader.get_datetime(sample_jpg)
        assert result is None or isinstance(result, datetime)

    def test_get_datetime_nonexistent(self):
        """测试不存在文件"""
        result = MetadataReader.get_datetime('/nonexistent/file.jpg')
        assert result is None


class TestGetSummary:
    """测试 get_summary 方法"""

    def test_get_summary_returns_dict(self, sample_jpg):
        """测试返回字典"""
        result = MetadataReader.get_summary(sample_jpg)
        assert isinstance(result, dict)

    def test_get_summary_has_required_fields(self, sample_jpg):
        """测试包含必要字段"""
        result = MetadataReader.get_summary(sample_jpg)
        required_fields = ['filename', 'extension', 'filesize', 'width', 'height',
                           'datetime', 'make', 'model', 'format', 'is_consistent']
        for field in required_fields:
            assert field in result, f"缺少字段: {field}"

    def test_get_summary_filename(self, sample_jpg):
        """测试文件名字段"""
        result = MetadataReader.get_summary(sample_jpg)
        expected_filename = os.path.basename(sample_jpg)
        assert result['filename'] == expected_filename


class TestGetEditableFields:
    """测试 get_editable_fields 方法"""

    def test_get_editable_fields_returns_dict(self, sample_jpg):
        """测试返回字典"""
        result = MetadataReader.get_editable_fields(sample_jpg)
        assert isinstance(result, dict)

    def test_get_editable_fields_structure(self, sample_jpg):
        """测试字段结构"""
        result = MetadataReader.get_editable_fields(sample_jpg)
        for key, value in result.items():
            assert 'value' in value
            assert 'label' in value
