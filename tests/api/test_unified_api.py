"""
King_photo - 统一API测试
测试 KingPhotoAPI 类的所有公共方法
"""

import os
import shutil
import tempfile
import pytest

from src.api import KingPhotoAPI, get_api, reset_api
from src.api.interfaces import (
    IFormatDetector,
    IMetadataReader,
    IMetadataWriter,
    IRepairEngine,
    IFileProcessor,
)


class TestKingPhotoAPI:
    """统一API测试"""

    def test_api_singleton(self):
        """测试API单例模式"""
        reset_api()
        api1 = get_api()
        api2 = get_api()
        assert api1 is api2, "get_api() 应该返回同一实例"

    def test_api_creation(self):
        """测试创建API实例"""
        reset_api()
        api = KingPhotoAPI()
        assert api is not None
        assert isinstance(api, KingPhotoAPI)

    def test_lazy_initialization(self):
        """测试延迟初始化"""
        reset_api()
        api = KingPhotoAPI()
        # 尚未初始化，核心模块应为 None
        assert api._format_detector is None
        assert api._metadata_reader is None
        assert api._metadata_writer is None
        assert api._repair_engine is None
        assert api._file_processor is None

    def test_ensure_initialized(self):
        """测试初始化触发"""
        reset_api()
        api = KingPhotoAPI()
        api._ensure_initialized()
        # 初始化后，核心模块不应为 None
        assert api._format_detector is not None
        assert api._metadata_reader is not None
        assert api._metadata_writer is not None
        assert api._repair_engine is not None
        assert api._file_processor is not None

    def test_reset_api(self):
        """测试重置API单例"""
        reset_api()
        api1 = get_api()
        reset_api()
        api2 = get_api()
        assert api1 is not api2, "reset_api() 后应创建新实例"


class TestFormatDetectionAPI:
    """格式检测API测试"""

    def test_detect_format_jpg(self, sample_jpg):
        """测试检测JPG格式"""
        api = KingPhotoAPI()
        format_info = api.detect_format(sample_jpg)
        assert isinstance(format_info, dict)
        assert "format" in format_info or "extension" in format_info

    def test_detect_format_png(self, sample_png):
        """测试检测PNG格式"""
        api = KingPhotoAPI()
        format_info = api.detect_format(sample_png)
        assert isinstance(format_info, dict)

    def test_is_supported(self, sample_jpg):
        """测试检查文件是否支持"""
        api = KingPhotoAPI()
        assert api.is_supported(sample_jpg) is True

    def test_is_supported_nonexistent(self):
        """测试不存在的文件"""
        api = KingPhotoAPI()
        assert api.is_supported("/nonexistent/file.xyz") is False

    def test_get_supported_formats(self):
        """测试获取支持的格式列表"""
        api = KingPhotoAPI()
        formats = api.get_supported_formats()
        assert isinstance(formats, dict)
        assert len(formats) > 0


class TestMetadataReadAPI:
    """元数据读取API测试"""

    def test_read_metadata_jpg(self, sample_jpg):
        """测试读取JPG元数据"""
        api = KingPhotoAPI()
        metadata = api.read_metadata(sample_jpg)
        assert isinstance(metadata, dict)

    def test_read_metadata_png(self, sample_png):
        """测试读取PNG元数据"""
        api = KingPhotoAPI()
        metadata = api.read_metadata(sample_png)
        assert isinstance(metadata, dict)

    def test_get_datetime_jpg(self, sample_jpg):
        """测试获取JPG拍摄时间"""
        api = KingPhotoAPI()
        dt = api.get_datetime(sample_jpg)
        # 可能为 None（无EXIF），但不应抛异常
        assert dt is None or hasattr(dt, 'strftime')

    def test_get_metadata_summary(self, sample_jpg):
        """测试获取元数据摘要"""
        api = KingPhotoAPI()
        summary = api.get_metadata_summary(sample_jpg)
        assert isinstance(summary, dict)

    def test_get_editable_fields(self, sample_jpg):
        """测试获取可编辑字段"""
        api = KingPhotoAPI()
        fields = api.get_editable_fields(sample_jpg)
        assert isinstance(fields, dict)

    def test_read_exif(self, sample_jpg):
        """测试读取EXIF数据"""
        api = KingPhotoAPI()
        exif_data = api.read_exif(sample_jpg)
        assert isinstance(exif_data, dict)

    def test_read_xmp(self, sample_jpg):
        """测试读取XMP数据"""
        api = KingPhotoAPI()
        xmp_data = api.read_xmp(sample_jpg)
        assert isinstance(xmp_data, dict)


class TestMetadataWriteAPI:
    """元数据写入API测试"""

    def test_write_metadata_copy_mode(self, sample_jpg, tmp_output_dir):
        """测试复制模式下写入元数据"""
        api = KingPhotoAPI()
        result = api.write_metadata(
            sample_jpg,
            {"title": "Test Title", "author": "Test Author"},
            copy_mode=True,
            output_dir=tmp_output_dir,
        )
        assert isinstance(result, dict)

    def test_write_exif(self, sample_jpg):
        """测试写入EXIF"""
        api = KingPhotoAPI()
        result = api.write_exif(sample_jpg, {"ImageDescription": "test"})
        assert isinstance(result, bool)


class TestRepairAPI:
    """修复API测试"""

    def test_check_file_extension(self, sample_jpg):
        """测试检查文件后缀"""
        api = KingPhotoAPI()
        result = api.check_file_extension(sample_jpg)
        assert isinstance(result, dict)

    def test_extract_time_info(self, sample_jpg):
        """测试提取时间信息"""
        api = KingPhotoAPI()
        result = api.extract_time_info(sample_jpg)
        assert isinstance(result, dict)

    def test_extract_time_info_with_source(self, sample_jpg):
        """测试指定时间来源提取时间"""
        api = KingPhotoAPI()
        result = api.extract_time_info(sample_jpg, time_source="auto")
        assert isinstance(result, dict)

    def test_repair_file_copy_mode(self, sample_jpg, tmp_output_dir):
        """测试复制模式下修复文件"""
        api = KingPhotoAPI()
        result = api.repair_file(
            sample_jpg,
            output_dir=tmp_output_dir,
            fix_extension=True,
            fix_time=False,
        )
        assert isinstance(result, dict)

    def test_fix_extension(self, sample_jpg, tmp_output_dir):
        """测试修复文件后缀"""
        api = KingPhotoAPI()
        result = api.fix_extension(sample_jpg, output_dir=tmp_output_dir)
        assert isinstance(result, dict)


class TestFileProcessingAPI:
    """文件处理API测试"""

    def test_get_image_files(self, test_other_dir):
        """测试获取文件夹中的图片文件"""
        api = KingPhotoAPI()
        files = api.get_image_files(test_other_dir, recursive=False)
        assert isinstance(files, list)
        assert len(files) > 0

    def test_get_image_files_recursive(self, test_images_dir):
        """测试递归获取图片文件"""
        api = KingPhotoAPI()
        files = api.get_image_files(test_images_dir, recursive=True)
        assert isinstance(files, list)
        assert len(files) > 0

    def test_rename_files(self, sample_jpg, tmp_output_dir):
        """测试重命名文件"""
        api = KingPhotoAPI()
        result = api.rename_files(
            [sample_jpg],
            pattern="{original}_renamed",
            output_dir=tmp_output_dir,
        )
        assert isinstance(result, dict)

    def test_copy_files(self, sample_jpg, tmp_output_dir):
        """测试复制文件"""
        api = KingPhotoAPI()
        result = api.copy_files([sample_jpg], tmp_output_dir)
        assert isinstance(result, dict)

    def test_move_files(self, sample_jpg, tmp_output_dir):
        """测试移动文件"""
        # 先在临时目录复制一份再移动
        tmp_src = tempfile.mkdtemp(prefix='king_photo_move_')
        dst_file = os.path.join(tmp_src, os.path.basename(sample_jpg))
        shutil.copy2(sample_jpg, dst_file)

        api = KingPhotoAPI()
        result = api.move_files([dst_file], tmp_output_dir)
        assert isinstance(result, dict)

        # 清理
        if os.path.exists(tmp_src):
            shutil.rmtree(tmp_src, ignore_errors=True)


class TestPluginAPI:
    """插件管理API测试"""

    def test_get_plugins(self):
        """测试获取已注册插件列表"""
        api = KingPhotoAPI()
        plugins = api.get_plugins()
        assert isinstance(plugins, list)

    def test_enable_disable_plugin(self):
        """测试启用/禁用插件"""
        api = KingPhotoAPI()
        # 尝试对不存在的插件操作
        result = api.disable_plugin("nonexistent_plugin")
        assert isinstance(result, bool)

    def test_register_none_plugin(self):
        """测试注册无效插件"""
        api = KingPhotoAPI()
        with pytest.raises((ValueError, TypeError, AttributeError)):
            api.register_plugin(None)


class TestConfigAPI:
    """配置管理API测试"""

    def test_get_config_default(self):
        """测试获取配置（默认值）"""
        api = KingPhotoAPI()
        value = api.get_config("nonexistent.key", "default_value")
        assert value == "default_value"

    def test_set_and_get_config(self):
        """测试设置和获取配置"""
        api = KingPhotoAPI()
        api.set_config("test.key", "test_value")
        value = api.get_config("test.key")
        assert value == "test_value"

    def test_load_config(self):
        """测试加载配置"""
        api = KingPhotoAPI()
        api.load_config()  # 不应抛异常


class TestUtilityAPI:
    """工具函数API测试"""

    def test_format_file_size(self):
        """测试格式化文件大小"""
        api = KingPhotoAPI()
        result = api.format_file_size(1024)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_datetime(self):
        """测试格式化日期时间"""
        from datetime import datetime
        api = KingPhotoAPI()
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = api.format_datetime(dt)
        assert isinstance(result, str)
        assert "2024" in result

    def test_parse_datetime(self):
        """测试解析日期时间字符串"""
        api = KingPhotoAPI()
        result = api.parse_datetime("2024-01-01 12:00:00")
        from datetime import datetime
        assert result is None or isinstance(result, datetime)

    def test_sanitize_filename(self):
        """测试清理文件名"""
        api = KingPhotoAPI()
        result = api.sanitize_filename("test<file>:name?.jpg")
        assert isinstance(result, str)
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "?" not in result
