"""
King_photo - 工具函数测试
测试 helpers.py 中的所有工具函数
"""

import os
import shutil
import tempfile
import pytest
from datetime import datetime
from src.utils.helpers import (
    get_file_extension,
    is_supported_image,
    get_image_files_in_folder,
    format_file_size,
    format_datetime,
    parse_datetime,
    extract_time_from_filename,
    generate_renamed_filename,
    sanitize_filename,
    set_file_times,
    get_file_times,
    ensure_output_folder,
    get_unique_filename,
    truncate_string,
)


class TestGetFileExtension:
    """测试 get_file_extension 函数"""

    def test_jpg_extension(self):
        assert get_file_extension('photo.jpg') == '.jpg'

    def test_uppercase_extension(self):
        assert get_file_extension('photo.JPG') == '.jpg'

    def test_no_extension(self):
        assert get_file_extension('photo') == ''

    def test_multiple_dots(self):
        assert get_file_extension('my.photo.jpg') == '.jpg'

    def test_path_with_dirs(self):
        assert get_file_extension('/path/to/photo.jpg') == '.jpg'


class TestIsSupportedImage:
    """测试 is_supported_image 函数"""

    def test_jpg_supported(self):
        assert is_supported_image('photo.jpg') is True

    def test_png_supported(self):
        assert is_supported_image('photo.png') is True

    def test_gif_supported(self):
        assert is_supported_image('photo.gif') is True

    def test_webp_supported(self):
        assert is_supported_image('photo.webp') is True

    def test_txt_not_supported(self):
        assert is_supported_image('file.txt') is False

    def test_unknown_not_supported(self):
        assert is_supported_image('file.xyz') is False


class TestGetImageFilesInFolder:
    """测试 get_image_files_in_folder 函数"""

    def test_finds_images(self, test_other_dir):
        """测试能找到图片文件"""
        files = get_image_files_in_folder(test_other_dir)
        assert len(files) > 0

    def test_returns_list_of_strings(self, test_other_dir):
        """测试返回字符串列表"""
        files = get_image_files_in_folder(test_other_dir)
        assert isinstance(files, list)
        for f in files:
            assert isinstance(f, str)

    def test_sorted_result(self, test_other_dir):
        """测试结果已排序"""
        files = get_image_files_in_folder(test_other_dir)
        assert files == sorted(files)

    def test_empty_folder(self, tmp_output_dir):
        """测试空文件夹"""
        files = get_image_files_in_folder(tmp_output_dir)
        assert len(files) == 0


class TestFormatFileSize:
    """测试 format_file_size 函数"""

    def test_bytes(self):
        assert format_file_size(500) == '500.0 B'

    def test_kilobytes(self):
        assert format_file_size(1024) == '1.0 KB'

    def test_megabytes(self):
        assert format_file_size(1024 * 1024) == '1.0 MB'

    def test_gigabytes(self):
        assert format_file_size(1024 * 1024 * 1024) == '1.0 GB'

    def test_zero(self):
        assert format_file_size(0) == '0.0 B'


class TestFormatDatetime:
    """测试 format_datetime 函数"""

    def test_valid_datetime(self):
        dt = datetime(2024, 6, 15, 12, 30, 45)
        assert format_datetime(dt) == '2024-06-15 12:30:45'

    def test_none(self):
        assert format_datetime(None) == '未知'


class TestParseDatetime:
    """测试 parse_datetime 函数"""

    def test_format_colon(self):
        result = parse_datetime('2024:06:15 12:30:00')
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_format_dash(self):
        result = parse_datetime('2024-06-15 12:30:00')
        assert isinstance(result, datetime)

    def test_format_compact(self):
        result = parse_datetime('20240615_123000')
        assert isinstance(result, datetime)

    def test_empty_string(self):
        assert parse_datetime('') is None

    def test_none(self):
        assert parse_datetime(None) is None

    def test_invalid_string(self):
        assert parse_datetime('not a date') is None


class TestExtractTimeFromFilename:
    """测试 extract_time_from_filename 函数"""

    def test_mmexport_format(self):
        result = extract_time_from_filename('mmexport1693274216447.jpg')
        assert isinstance(result, datetime)

    def test_date_time_format(self):
        result = extract_time_from_filename('20230816_193756.jpg')
        assert isinstance(result, datetime)
        assert result.year == 2023

    def test_date_only_format(self):
        result = extract_time_from_filename('20230816.jpg')
        assert isinstance(result, datetime)

    def test_img_format(self):
        result = extract_time_from_filename('img_1234567890_1647742406658.jpeg')
        assert isinstance(result, datetime)

    def test_no_time_in_name(self):
        result = extract_time_from_filename('photo.jpg')
        assert result is None

    def test_img_with_negative_id(self):
        result = extract_time_from_filename('img_-1083997888_1647742406658.jpeg')
        assert isinstance(result, datetime)


class TestGenerateRenamedFilename:
    """测试 generate_renamed_filename 函数"""

    def test_original_variable(self):
        metadata = {'datetime': datetime(2024, 6, 15, 12, 30, 0)}
        result = generate_renamed_filename('test', '{original}', metadata)
        assert result == 'test.jpg'

    def test_datetime_variable(self):
        metadata = {'datetime': datetime(2024, 6, 15, 12, 30, 0)}
        result = generate_renamed_filename('test', '{datetime}', metadata)
        assert result == '20240615_123000.jpg'

    def test_seq_variable(self):
        metadata = {}
        result = generate_renamed_filename('test', '{seq}', metadata, sequence=5)
        assert result == '005.jpg'

    def test_seq_n_variable(self):
        metadata = {}
        result = generate_renamed_filename('test', '{seq:5}', metadata, sequence=5)
        assert result == '00005.jpg'

    def test_make_variable(self):
        metadata = {'make': 'Canon'}
        result = generate_renamed_filename('test', '{make}_{original}', metadata)
        assert result == 'Canon_test.jpg'

    def test_ext_variable(self):
        # generate_renamed_filename 会在末尾自动追加 ext 参数
        # 所以不使用 {ext} 变量，直接测试扩展名参数
        metadata = {}
        result = generate_renamed_filename('test', '{original}', metadata, ext='.png')
        assert result == 'test.png'


class TestSanitizeFilename:
    """测试 sanitize_filename 函数"""

    def test_clean_illegal_chars(self):
        result = sanitize_filename('test<>:"/\\|?*file')
        assert '<' not in result
        assert '>' not in result

    def test_strip_spaces(self):
        result = sanitize_filename('  test  ')
        assert result == 'test'

    def test_strip_dots(self):
        result = sanitize_filename('test...')
        assert result == 'test'

    def test_long_name_truncated(self):
        long_name = 'a' * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 200


class TestSetAndGetFileTimes:
    """测试 set_file_times 和 get_file_times 函数"""

    def test_set_and_get_times(self, tmp_output_dir):
        """测试设置和获取文件时间"""
        test_file = os.path.join(tmp_output_dir, 'time_test.txt')
        with open(test_file, 'w') as f:
            f.write('test')

        # 设置时间
        target_dt = datetime(2024, 6, 15, 12, 30, 0)
        success = set_file_times(test_file, target_dt)
        assert success is True

        # 获取时间
        times = get_file_times(test_file)
        assert 'created' in times
        assert 'modified' in times
        assert 'accessed' in times

    def test_set_file_times_nonexistent(self):
        """测试不存在的文件"""
        result = set_file_times('/nonexistent/file.txt', datetime.now())
        assert result is False


class TestEnsureOutputFolder:
    """测试 ensure_output_folder 函数"""

    def test_creates_folder(self, tmp_output_dir):
        """测试创建文件夹"""
        new_dir = os.path.join(tmp_output_dir, 'new_folder')
        result = ensure_output_folder(new_dir)
        assert os.path.exists(result)

    def test_existing_folder(self, tmp_output_dir):
        """测试已存在的文件夹"""
        result = ensure_output_folder(tmp_output_dir)
        assert os.path.exists(result)


class TestGetUniqueFilename:
    """测试 get_unique_filename 函数"""

    def test_unique_when_not_exists(self, tmp_output_dir):
        """测试文件不存在时直接返回"""
        filepath = os.path.join(tmp_output_dir, 'unique.txt')
        result = get_unique_filename(filepath)
        assert result == filepath

    def test_unique_when_exists(self, tmp_output_dir):
        """测试文件存在时添加序号"""
        filepath = os.path.join(tmp_output_dir, 'unique.txt')
        with open(filepath, 'w') as f:
            f.write('test')
        result = get_unique_filename(filepath)
        assert result != filepath
        assert '_1' in result

    def test_unique_multiple_exists(self, tmp_output_dir):
        """测试多个文件存在时"""
        filepath = os.path.join(tmp_output_dir, 'multi.txt')
        with open(filepath, 'w') as f:
            f.write('test')
        with open(os.path.join(tmp_output_dir, 'multi_1.txt'), 'w') as f:
            f.write('test')
        result = get_unique_filename(filepath)
        assert '_2' in result


class TestTruncateString:
    """测试 truncate_string 函数"""

    def test_short_string(self):
        assert truncate_string('hello', 10) == 'hello'

    def test_long_string(self):
        result = truncate_string('hello world', 8)
        assert len(result) == 8
        assert result.endswith('...')

    def test_exact_length(self):
        assert truncate_string('hello', 5) == 'hello'
