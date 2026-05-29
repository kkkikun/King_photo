"""
King_photo - 修复引擎测试
测试 RepairEngine 类的所有方法
"""

import os
import shutil
import pytest
from datetime import datetime
from src.core.repair_engine import RepairEngine


class TestBackupPath:
    """测试 get_backup_path 方法"""

    def test_backup_path_adds_res(self):
        """测试备份路径添加 .res 后缀"""
        result = RepairEngine.get_backup_path('/path/to/file.jpg')
        assert result == '/path/to/file.jpg.res'

    def test_backup_path_different_ext(self):
        """测试不同扩展名"""
        result = RepairEngine.get_backup_path('/path/to/file.png')
        assert result == '/path/to/file.png.res'


class TestHasBackup:
    """测试 has_backup 方法"""

    def test_has_backup_false(self, sample_jpg):
        """测试没有备份文件"""
        assert RepairEngine.has_backup(sample_jpg) is False

    def test_has_backup_true(self, sample_jpg):
        """测试有备份文件"""
        backup_path = sample_jpg + '.res'
        try:
            # 创建备份文件
            shutil.copy2(sample_jpg, backup_path)
            assert RepairEngine.has_backup(sample_jpg) is True
        finally:
            # 清理
            if os.path.exists(backup_path):
                os.remove(backup_path)


class TestCreateBackup:
    """测试 create_backup 方法"""

    def test_create_backup_success(self, sample_jpg, tmp_output_dir):
        """测试创建备份成功"""
        result = RepairEngine.create_backup(sample_jpg, tmp_output_dir)
        assert result['success'] is True
        assert os.path.exists(result['backup_path'])

    def test_create_backup_alread_exists(self, sample_jpg, tmp_output_dir):
        """测试备份已存在"""
        # 先创建一次
        RepairEngine.create_backup(sample_jpg, tmp_output_dir)
        # 再创建一次
        result = RepairEngine.create_backup(sample_jpg, tmp_output_dir)
        assert result['success'] is True
        assert result.get('already_exists') is True

    def test_create_backup_nonexistent(self):
        """测试不存在的文件"""
        result = RepairEngine.create_backup('/nonexistent/file.jpg')
        assert result['success'] is False

    def test_create_backup_in_same_dir(self, sample_jpg):
        """测试在同目录创建备份"""
        result = RepairEngine.create_backup(sample_jpg)
        assert result['success'] is True
        backup_path = sample_jpg + '.res'
        assert os.path.exists(backup_path)
        # 清理
        os.remove(backup_path)


class TestRestoreFromBackup:
    """测试 restore_from_backup 方法"""

    def test_restore_success(self, sample_jpg, tmp_output_dir):
        """测试恢复成功"""
        # 创建备份
        backup_result = RepairEngine.create_backup(sample_jpg, tmp_output_dir)
        assert backup_result['success']

        # 恢复
        restore_path = os.path.join(tmp_output_dir, 'restored_' + os.path.basename(sample_jpg))
        result = RepairEngine.restore_from_backup(backup_result['backup_path'], restore_path)
        assert result['success'] is True
        assert os.path.exists(restore_path)

    def test_restore_nonexistent_backup(self):
        """测试不存在的备份"""
        result = RepairEngine.restore_from_backup('/nonexistent/file.jpg.res')
        assert result['success'] is False

    def test_restore_auto_path(self, sample_jpg, tmp_output_dir):
        """测试自动确定恢复路径"""
        backup_result = RepairEngine.create_backup(sample_jpg, tmp_output_dir)
        assert backup_result['success']

        # 不指定恢复路径，自动去掉 .res
        backup_path = backup_result['backup_path']
        expected_restore = backup_path[:-4]  # 去掉 .res
        result = RepairEngine.restore_from_backup(backup_path)
        assert result['success'] is True
        assert os.path.exists(expected_restore)
        # 清理
        os.remove(expected_restore)


class TestDeleteBackup:
    """测试 delete_backup 方法"""

    def test_delete_backup_success(self, tmp_copy_jpg):
        """测试删除备份成功 - 在同目录创建备份"""
        backup_result = RepairEngine.create_backup(tmp_copy_jpg)
        assert backup_result['success']

        result = RepairEngine.delete_backup(tmp_copy_jpg)
        assert result['success'] is True
        assert not os.path.exists(backup_result['backup_path'])

    def test_delete_backup_not_found(self, sample_jpg):
        """测试备份不存在"""
        result = RepairEngine.delete_backup(sample_jpg)
        assert result['success'] is False


class TestDeleteBackups:
    """测试 delete_backups 方法"""

    def test_delete_backups_empty_folder(self, tmp_output_dir):
        """测试空文件夹"""
        result = RepairEngine.delete_backups(tmp_output_dir)
        assert result['total'] == 0
        assert result['deleted'] == 0

    def test_delete_backups_with_res_files(self, tmp_output_dir):
        """测试有 .res 文件"""
        # 创建一些 .res 文件
        for i in range(3):
            res_file = os.path.join(tmp_output_dir, f'test_{i}.jpg.res')
            with open(res_file, 'w') as f:
                f.write('test')

        result = RepairEngine.delete_backups(tmp_output_dir)
        assert result['total'] == 3
        assert result['deleted'] == 3


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
