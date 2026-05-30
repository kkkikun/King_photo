"""
King_photo - 格式检测模块测试
测试 FormatDetector 类的所有方法
"""

import os
import pytest
from src.core.format_detector import FormatDetector


class TestDetectByHeader:
    """测试 detect_by_header 方法"""

    def test_jpg_detection(self, sample_jpg):
        """测试 JPG 文件头检测"""
        result = FormatDetector.detect_by_header(sample_jpg)
        assert result == 'JPEG'

    def test_png_detection(self, sample_png):
        """测试 PNG 文件头检测"""
        result = FormatDetector.detect_by_header(sample_png)
        assert result == 'PNG'

    def test_webp_detection(self, sample_webp):
        """测试 WebP 文件头检测"""
        result = FormatDetector.detect_by_header(sample_webp)
        assert result == 'WebP'

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        result = FormatDetector.detect_by_header('/nonexistent/file.jpg')
        assert result is None

    def test_empty_file(self, tmp_output_dir):
        """测试空文件"""
        empty_file = os.path.join(tmp_output_dir, 'empty.jpg')
        with open(empty_file, 'wb') as f:
            f.write(b'')
        result = FormatDetector.detect_by_header(empty_file)
        assert result is None

    def test_jpeg_detection(self, sample_jpeg):
        """测试 JPEG 文件头检测"""
        result = FormatDetector.detect_by_header(sample_jpeg)
        assert result == 'JPEG'


class TestDetectByExtension:
    """测试 detect_by_extension 方法"""

    def test_jpg_extension(self):
        """测试 .jpg 扩展名"""
        result = FormatDetector.detect_by_extension('test.jpg')
        assert result == 'JPEG'

    def test_jpeg_extension(self):
        """测试 .jpeg 扩展名"""
        result = FormatDetector.detect_by_extension('test.jpeg')
        assert result == 'JPEG'

    def test_png_extension(self):
        """测试 .png 扩展名"""
        result = FormatDetector.detect_by_extension('test.png')
        assert result == 'PNG'

    def test_gif_extension(self):
        """测试 .gif 扩展名"""
        result = FormatDetector.detect_by_extension('test.gif')
        assert result == 'GIF'

    def test_webp_extension(self):
        """测试 .webp 扩展名"""
        result = FormatDetector.detect_by_extension('test.webp')
        assert result == 'WebP'

    def test_tiff_extension(self):
        """测试 .tiff 扩展名"""
        result = FormatDetector.detect_by_extension('test.tiff')
        assert result == 'TIFF'

    def test_bmp_extension(self):
        """测试 .bmp 扩展名"""
        result = FormatDetector.detect_by_extension('test.bmp')
        assert result == 'BMP'

    def test_svg_extension(self):
        """测试 .svg 扩展名"""
        result = FormatDetector.detect_by_extension('test.svg')
        assert result == 'SVG'

    def test_heic_extension(self):
        """测试 .heic 扩展名"""
        result = FormatDetector.detect_by_extension('test.heic')
        assert result == 'HEIF'

    def test_unknown_extension(self):
        """测试未知扩展名"""
        result = FormatDetector.detect_by_extension('test.xyz')
        assert result is None

    def test_uppercase_extension(self):
        """测试大写扩展名"""
        result = FormatDetector.detect_by_extension('test.JPG')
        assert result == 'JPEG'


class TestGetRealFormat:
    """测试 get_real_format 方法"""

    def test_consistent_jpg(self, sample_jpg):
        """测试一致的 JPG 文件"""
        format_name, is_consistent = FormatDetector.get_real_format(sample_jpg)
        assert format_name == 'JPEG'
        # 真实格式是 JPEG，扩展名也是 jpg，应该一致
        assert is_consistent is True

    def test_consistent_png(self, sample_png):
        """测试一致的 PNG 文件"""
        format_name, is_consistent = FormatDetector.get_real_format(sample_png)
        assert format_name == 'PNG'
        assert is_consistent is True

    def test_returns_tuple(self, sample_jpg):
        """测试返回值是元组"""
        result = FormatDetector.get_real_format(sample_jpg)
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestGetCorrectExtension:
    """测试 get_correct_extension 方法"""

    def test_jpg_extension(self, sample_jpg):
        """测试 JPG 的正确扩展名"""
        ext = FormatDetector.get_correct_extension(sample_jpg)
        assert ext in ['.jpg', '.jpeg']

    def test_png_extension(self, sample_png):
        """测试 PNG 的正确扩展名"""
        ext = FormatDetector.get_correct_extension(sample_png)
        assert ext == '.png'


class TestNeedsExiftool:
    """测试 needs_exiftool 方法"""

    def test_jpg_not_needs_exiftool(self, sample_jpg):
        """测试 JPG 不需要 exiftool"""
        assert FormatDetector.needs_exiftool(sample_jpg) is False

    def test_png_not_needs_exiftool(self, sample_png):
        """测试 PNG 不需要 exiftool"""
        assert FormatDetector.needs_exiftool(sample_png) is False

    def test_heic_needs_exiftool(self):
        """测试 HEIC 需要 exiftool"""
        assert FormatDetector.needs_exiftool('test.heic') is True

    def test_cr2_needs_exiftool(self):
        """测试 CR2 需要 exiftool"""
        assert FormatDetector.needs_exiftool('test.cr2') is True


class TestSupportsExif:
    """测试 supports_exif 方法"""

    def test_jpg_supports_exif(self, sample_jpg):
        """测试 JPG 支持 EXIF"""
        assert FormatDetector.supports_exif(sample_jpg) is True

    def test_png_no_exif(self, sample_png):
        """测试 PNG 不支持 EXIF"""
        assert FormatDetector.supports_exif(sample_png) is False

    def test_gif_no_exif(self):
        """测试 GIF 不支持 EXIF"""
        assert FormatDetector.supports_exif('test.gif') is False

    def test_webp_supports_exif(self, sample_webp):
        """测试 WebP 支持 EXIF"""
        assert FormatDetector.supports_exif(sample_webp) is True


class TestSupportsXmp:
    """测试 supports_xmp 方法"""

    def test_jpg_supports_xmp(self, sample_jpg):
        """测试 JPG 支持 XMP"""
        assert FormatDetector.supports_xmp(sample_jpg) is True

    def test_png_supports_xmp(self, sample_png):
        """测试 PNG 支持 XMP"""
        assert FormatDetector.supports_xmp(sample_png) is True

    def test_gif_no_xmp(self):
        """测试 GIF 不支持 XMP"""
        assert FormatDetector.supports_xmp('test.gif') is False

    def test_svg_supports_xmp(self):
        """测试 SVG 支持 XMP"""
        assert FormatDetector.supports_xmp('test.svg') is True


class TestIsSupported:
    """测试 is_supported 方法"""

    def test_jpg_supported(self, sample_jpg):
        """测试 JPG 是支持的格式"""
        assert FormatDetector.is_supported(sample_jpg) is True

    def test_png_supported(self, sample_png):
        """测试 PNG 是支持的格式"""
        assert FormatDetector.is_supported(sample_png) is True

    def test_unknown_not_supported(self):
        """测试未知格式不支持"""
        assert FormatDetector.is_supported('test.xyz') is False


class TestGetFormatInfo:
    """测试 get_format_info 方法"""

    def test_jpg_format_info(self, sample_jpg):
        """测试 JPG 格式信息"""
        info = FormatDetector.get_format_info(sample_jpg)
        assert info['format'] == 'JPEG'
        assert info.get('exif_support') is True
        assert info.get('xmp_support') is True
        assert info.get('need_exiftool') is False

    def test_png_format_info(self, sample_png):
        """测试 PNG 格式信息"""
        info = FormatDetector.get_format_info(sample_png)
        assert info['format'] == 'PNG'
        assert info.get('exif_support') is False
        assert info.get('xmp_support') is True
        assert info.get('need_exiftool') is False

    def test_unknown_format_info(self):
        """测试未知格式信息"""
        info = FormatDetector.get_format_info('test.xyz')
        assert info['format'] == 'Unknown'
        assert info.get('exif_support') is False
        assert info.get('xmp_support') is False
