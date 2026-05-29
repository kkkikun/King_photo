"""
King_photo - EXIF 处理模块测试
测试 ExifHandler 类的所有方法
"""

import os
import pytest
from datetime import datetime
from src.core.exif_handler import ExifHandler


class TestReadExif:
    """测试 read_exif 方法"""

    def test_read_exif_returns_dict(self, sample_jpg):
        """测试读取 EXIF 返回字典"""
        result = ExifHandler.read_exif(sample_jpg)
        assert isinstance(result, dict)

    def test_read_exif_on_jpg(self, sample_jpg):
        """测试读取 JPG 文件的 EXIF"""
        result = ExifHandler.read_exif(sample_jpg)
        # 返回字典，可能包含或不包含 make/model 等字段
        assert isinstance(result, dict)

    def test_read_exif_nonexistent_file(self):
        """测试读取不存在文件的 EXIF"""
        result = ExifHandler.read_exif('/nonexistent/file.jpg')
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_read_exif_empty_file(self, tmp_output_dir):
        """测试读取空文件的 EXIF"""
        empty_file = os.path.join(tmp_output_dir, 'empty.jpg')
        with open(empty_file, 'wb') as f:
            f.write(b'\xff\xd8\xff')  # JPEG 头但没有 EXIF
        result = ExifHandler.read_exif(empty_file)
        assert isinstance(result, dict)


class TestWriteExif:
    """测试 write_exif 方法"""

    def test_write_artist(self, tmp_copy_jpg):
        """测试写入作者字段"""
        metadata = {'artist': 'Test Author'}
        result = ExifHandler.write_exif(tmp_copy_jpg, metadata)
        assert result is True

        # 验证写入成功
        exif_data = ExifHandler.read_exif(tmp_copy_jpg)
        assert 'artist' in exif_data
        assert exif_data['artist'] == 'Test Author'

    def test_write_copyright(self, tmp_copy_jpg):
        """测试写入版权字段"""
        metadata = {'copyright': 'Test Copyright 2024'}
        result = ExifHandler.write_exif(tmp_copy_jpg, metadata)
        assert result is True

        exif_data = ExifHandler.read_exif(tmp_copy_jpg)
        assert 'copyright' in exif_data
        assert exif_data['copyright'] == 'Test Copyright 2024'

    def test_write_description(self, tmp_copy_jpg):
        """测试写入描述字段"""
        metadata = {'description': 'Test Description'}
        result = ExifHandler.write_exif(tmp_copy_jpg, metadata)
        assert result is True

        exif_data = ExifHandler.read_exif(tmp_copy_jpg)
        assert 'description' in exif_data
        assert exif_data['description'] == 'Test Description'

    def test_write_make_model(self, tmp_copy_jpg):
        """测试写入相机品牌和型号"""
        metadata = {
            'make': 'TestMake',
            'model': 'TestModel',
        }
        result = ExifHandler.write_exif(tmp_copy_jpg, metadata)
        assert result is True

        exif_data = ExifHandler.read_exif(tmp_copy_jpg)
        assert 'make' in exif_data
        assert exif_data['make'] == 'TestMake'
        assert 'model' in exif_data
        assert exif_data['model'] == 'TestModel'

    def test_write_datetime(self, tmp_copy_jpg):
        """测试写入时间字段"""
        metadata = {'datetime': '2024:06:15 12:30:00'}
        result = ExifHandler.write_exif(tmp_copy_jpg, metadata)
        assert result is True

    def test_write_nonexistent_file(self):
        """测试写入不存在文件的 EXIF"""
        result = ExifHandler.write_exif('/nonexistent/file.jpg', {'artist': 'Test'})
        assert result is False

    def test_write_multiple_fields(self, tmp_copy_jpg):
        """测试一次写入多个字段"""
        metadata = {
            'artist': 'Multi Author',
            'copyright': 'Multi Copyright',
            'make': 'MultiMake',
            'model': 'MultiModel',
        }
        result = ExifHandler.write_exif(tmp_copy_jpg, metadata)
        assert result is True

        exif_data = ExifHandler.read_exif(tmp_copy_jpg)
        assert exif_data.get('artist') == 'Multi Author'
        assert exif_data.get('copyright') == 'Multi Copyright'


class TestGetDatetime:
    """测试 get_datetime 方法"""

    def test_get_datetime_returns_datetime_or_none(self, sample_jpg):
        """测试返回值类型"""
        result = ExifHandler.get_datetime(sample_jpg)
        assert result is None or isinstance(result, datetime)

    def test_get_datetime_nonexistent_file(self):
        """测试不存在文件"""
        result = ExifHandler.get_datetime('/nonexistent/file.jpg')
        assert result is None


class TestHasExif:
    """测试 has_exif 方法"""

    def test_has_exif_returns_bool(self, sample_jpg):
        """测试返回布尔值"""
        result = ExifHandler.has_exif(sample_jpg)
        assert isinstance(result, bool)

    def test_has_exif_nonexistent_file(self):
        """测试不存在文件"""
        result = ExifHandler.has_exif('/nonexistent/file.jpg')
        assert result is False

    def test_has_exif_after_write(self, tmp_copy_jpg):
        """测试写入后检查 EXIF"""
        # 写入一些 EXIF 数据
        ExifHandler.write_exif(tmp_copy_jpg, {'artist': 'Test'})
        assert ExifHandler.has_exif(tmp_copy_jpg) is True
