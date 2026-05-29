"""
King_photo - XMP 处理模块测试
测试 XmpHandler 类的所有方法
"""

import os
import pytest
from datetime import datetime
from src.core.xmp_handler import XmpHandler


class TestParseXmp:
    """测试 parse_xmp 方法"""

    def test_parse_xmp_returns_dict(self):
        """测试解析 XMP 返回字典"""
        xmp_str = '''<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:xmp="http://ns.adobe.com/xap/1.0/"
      dc:title="Test Title"
      xmp:CreatorTool="Test Tool"/>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''
        result = XmpHandler.parse_xmp(xmp_str)
        assert isinstance(result, dict)

    def test_parse_xmp_with_title(self):
        """测试解析带标题的 XMP"""
        xmp_str = '''<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      dc:title="My Photo"/>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''
        result = XmpHandler.parse_xmp(xmp_str)
        assert 'dc:title' in result
        assert result['dc:title'] == 'My Photo'

    def test_parse_xmp_empty(self):
        """测试解析空 XMP"""
        result = XmpHandler.parse_xmp('')
        assert isinstance(result, dict)

    def test_parse_xmp_invalid_xml(self):
        """测试解析无效 XML"""
        result = XmpHandler.parse_xmp('not xml at all')
        assert isinstance(result, dict)


class TestGetDatetime:
    """测试 get_datetime 方法"""

    def test_get_datetime_from_xmp_data(self):
        """测试从 XMP 数据获取时间"""
        xmp_data = {
            'xmp:CreateDate': '2024-06-15T12:30:00',
            'xmp:ModifyDate': '2024-06-16T10:00:00',
        }
        result = XmpHandler.get_datetime(xmp_data)
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 15

    def test_get_datetime_no_time_fields(self):
        """测试没有时间字段"""
        xmp_data = {'dc:title': 'Test'}
        result = XmpHandler.get_datetime(xmp_data)
        assert result is None

    def test_get_datetime_empty_dict(self):
        """测试空字典"""
        result = XmpHandler.get_datetime({})
        assert result is None


class TestGetBasicInfo:
    """测试 get_basic_info 方法"""

    def test_get_basic_info_with_data(self):
        """测试获取基本信息"""
        xmp_data = {
            'dc:title': 'My Title',
            'dc:description': 'My Description',
            'dc:creator': 'Test Artist',
            'tiff:Make': 'Canon',
            'tiff:Model': 'EOS R5',
        }
        result = XmpHandler.get_basic_info(xmp_data)
        assert result['title'] == 'My Title'
        assert result['description'] == 'My Description'
        assert result['artist'] == 'Test Artist'
        assert result['make'] == 'Canon'
        assert result['model'] == 'EOS R5'

    def test_get_basic_info_empty(self):
        """测试空 XMP 数据"""
        result = XmpHandler.get_basic_info({})
        assert isinstance(result, dict)
        assert len(result) == 0


class TestBuildXmpString:
    """测试 _build_xmp_string 方法"""

    def test_build_xmp_string_basic(self):
        """测试构建基本 XMP 字符串"""
        metadata = {
            'title': 'Test Title',
            'artist': 'Test Artist',
        }
        result = XmpHandler._build_xmp_string(metadata)
        assert result is not None
        assert isinstance(result, str)
        assert 'xmpmeta' in result
        assert 'Test Title' in result

    def test_build_xmp_string_empty(self):
        """测试构建空 XMP 字符串"""
        result = XmpHandler._build_xmp_string({})
        assert result is not None
        assert 'xmpmeta' in result

    def test_build_xmp_string_with_datetime(self):
        """测试包含时间字段"""
        metadata = {
            'datetime': datetime(2024, 6, 15, 12, 30, 0),
        }
        result = XmpHandler._build_xmp_string(metadata)
        assert result is not None
        assert '2024-06-15' in result


class TestWriteXmp:
    """测试 write_xmp 方法"""

    def test_write_xmp_to_png(self, tmp_copy_png):
        """测试写入 PNG 文件的 XMP"""
        metadata = {
            'title': 'PNG Test Title',
            'artist': 'PNG Test Artist',
        }
        result = XmpHandler.write_xmp(tmp_copy_png, metadata)
        assert result is True

        # 验证读取
        xmp_data = XmpHandler.read_xmp_from_png(tmp_copy_png)
        if xmp_data:  # XMP 可能被成功写入并读取
            assert isinstance(xmp_data, dict)

    def test_write_xmp_to_jpg_returns_false(self, tmp_copy_jpg):
        """测试 JPEG 文件返回 False（JPEG 使用 EXIF）"""
        metadata = {'title': 'Test'}
        result = XmpHandler.write_xmp(tmp_copy_jpg, metadata)
        # JPEG 返回 False，因为优先使用 EXIF
        assert result is False

    def test_write_xmp_nonexistent_file(self):
        """测试写入不存在文件"""
        result = XmpHandler.write_xmp('/nonexistent/file.png', {'title': 'Test'})
        assert result is False


class TestReadXmpFromPng:
    """测试 read_xmp_from_png 方法"""

    def test_read_xmp_from_png_returns_dict(self, sample_png):
        """测试读取 PNG XMP 返回字典"""
        result = XmpHandler.read_xmp_from_png(sample_png)
        assert isinstance(result, dict)

    def test_read_xmp_from_non_png(self):
        """测试读取非 PNG 文件"""
        result = XmpHandler.read_xmp_from_png('/nonexistent/file.png')
        assert isinstance(result, dict)


class TestReadXmpFromFile:
    """测试 read_xmp_from_file 方法"""

    def test_read_xmp_from_file_returns_dict(self, sample_jpg):
        """测试从 JPG 读取 XMP 返回字典"""
        result = XmpHandler.read_xmp_from_file(sample_jpg)
        assert isinstance(result, dict)

    def test_read_xmp_from_nonexistent(self):
        """测试读取不存在文件"""
        result = XmpHandler.read_xmp_from_file('/nonexistent/file.jpg')
        assert isinstance(result, dict)


class TestCleanAttrName:
    """测试 _clean_attr_name 方法"""

    def test_clean_known_namespace(self):
        """测试清理已知命名空间"""
        name = '{http://purl.org/dc/elements/1.1/}title'
        result = XmpHandler._clean_attr_name(name)
        assert result == 'dc:title'

    def test_clean_unknown_namespace(self):
        """测试清理未知命名空间"""
        name = '{http://unknown/namespace/}field'
        result = XmpHandler._clean_attr_name(name)
        # 未知命名空间返回 None
        assert result is None

    def test_clean_no_namespace(self):
        """测试无命名空间"""
        result = XmpHandler._clean_attr_name('simple_name')
        assert result is None
