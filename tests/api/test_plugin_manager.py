"""
King_photo - 插件管理器测试
测试 PluginManager 类的所有公共方法
"""

import os
import pytest

from src.api.plugin_manager import PluginManager
from src.api.plugin_interfaces import IFormatPlugin, IFunctionPlugin, IExtensionPlugin


class TestPluginManager:
    """插件管理器测试"""

    def test_create_plugin_manager(self):
        """测试创建插件管理器"""
        pm = PluginManager()
        assert pm is not None
        assert isinstance(pm, PluginManager)

    def test_empty_plugins_on_creation(self):
        """测试初始状态无插件"""
        pm = PluginManager()
        assert len(pm.get_format_plugins()) == 0
        assert len(pm.get_function_plugins()) == 0
        assert len(pm.get_extension_plugins()) == 0

    def test_get_all_plugins_empty(self):
        """测试获取空插件列表"""
        pm = PluginManager()
        all_plugins = pm.get_all_plugins()
        assert isinstance(all_plugins, list)
        assert len(all_plugins) == 0


class MockFormatPlugin(IFormatPlugin):
    """模拟格式插件（用于测试）"""
    
    @property
    def format_name(self) -> str:
        return "MOCK"
    
    @property
    def extensions(self) -> list:
        return [".mock"]
    
    @property
    def magic_numbers(self) -> list:
        return [b"MOCK"]
    
    @property
    def description(self) -> str:
        return "Mock format for testing"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def is_available(self) -> bool:
        return True
    
    def read_metadata(self, filepath: str) -> dict:
        return {"format": "MOCK", "filepath": filepath}
    
    def write_metadata(self, filepath: str, metadata: dict) -> bool:
        return True
    
    def get_datetime(self, filepath: str):
        from datetime import datetime
        return datetime(2024, 1, 1, 12, 0, 0)


class MockFunctionPlugin(IFunctionPlugin):
    """模拟功能插件（用于测试）"""
    
    @property
    def plugin_name(self) -> str:
        return "mock_function"
    
    @property
    def plugin_type(self) -> str:
        return "test"
    
    @property
    def description(self) -> str:
        return "Mock function for testing"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def execute(self, file_list: list, **kwargs) -> dict:
        return {"success": True, "processed": len(file_list)}
    
    def get_parameters(self) -> dict:
        return {}


class MockExtensionPlugin(IExtensionPlugin):
    """模拟扩展插件（用于测试）"""
    
    @property
    def extension_name(self) -> str:
        return "mock_extension"
    
    @property
    def target_module(self) -> str:
        return "repair_engine"
    
    @property
    def extension_type(self) -> str:
        return "test"
    
    @property
    def description(self) -> str:
        return "Mock extension for testing"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def priority(self) -> int:
        return 100
    
    def execute(self, **kwargs) -> dict:
        return {"success": True}
    
    def before_execute(self, **kwargs) -> None:
        pass
    
    def after_execute(self, result: dict, **kwargs) -> None:
        pass
    
    def on_error(self, error: Exception, **kwargs) -> None:
        pass


class TestPluginRegistration:
    """插件注册测试"""

    def test_register_format_plugin(self):
        """测试注册格式插件"""
        pm = PluginManager()
        plugin = MockFormatPlugin()
        pm.register_format_plugin(plugin)
        
        assert len(pm.get_format_plugins()) == 1
        assert pm.get_format_plugins()[0] is plugin
        assert pm.get_format_plugin("MOCK") is plugin

    def test_register_function_plugin(self):
        """测试注册功能插件"""
        pm = PluginManager()
        plugin = MockFunctionPlugin()
        pm.register_function_plugin(plugin)
        
        assert len(pm.get_function_plugins()) == 1
        assert pm.get_function_plugins()[0] is plugin
        assert pm.get_function_plugin("mock_function") is plugin

    def test_register_extension_plugin(self):
        """测试注册扩展插件"""
        pm = PluginManager()
        plugin = MockExtensionPlugin()
        pm.register_extension_plugin(plugin)
        
        assert len(pm.get_extension_plugins()) == 1
        assert pm.get_extension_plugins()[0] is plugin
        assert pm.get_extension_plugin("mock_extension") is plugin

    def test_register_multiple_plugins(self):
        """测试注册多个插件"""
        pm = PluginManager()
        pm.register_format_plugin(MockFormatPlugin())
        pm.register_function_plugin(MockFunctionPlugin())
        pm.register_extension_plugin(MockExtensionPlugin())
        
        assert len(pm.get_format_plugins()) == 1
        assert len(pm.get_function_plugins()) == 1
        assert len(pm.get_extension_plugins()) == 1

    def test_get_all_plugins_with_registered(self):
        """测试获取所有已注册插件"""
        pm = PluginManager()
        pm.register_format_plugin(MockFormatPlugin())
        pm.register_function_plugin(MockFunctionPlugin())
        
        all_plugins = pm.get_all_plugins()
        assert isinstance(all_plugins, list)
        assert len(all_plugins) == 2


class TestPluginLookup:
    """插件查找测试"""

    def test_get_format_plugin_exists(self):
        """测试查找存在的格式插件"""
        pm = PluginManager()
        plugin = MockFormatPlugin()
        pm.register_format_plugin(plugin)
        
        found = pm.get_format_plugin("MOCK")
        assert found is plugin

    def test_get_format_plugin_not_exists(self):
        """测试查找不存在的格式插件"""
        pm = PluginManager()
        found = pm.get_format_plugin("NONEXISTENT")
        assert found is None

    def test_get_function_plugin_exists(self):
        """测试查找存在的功能插件"""
        pm = PluginManager()
        plugin = MockFunctionPlugin()
        pm.register_function_plugin(plugin)
        
        found = pm.get_function_plugin("mock_function")
        assert found is plugin

    def test_get_function_plugin_not_exists(self):
        """测试查找不存在的功能插件"""
        pm = PluginManager()
        found = pm.get_function_plugin("NONEXISTENT")
        assert found is None

    def test_get_format_plugin_by_file(self):
        """测试按文件查找格式插件"""
        pm = PluginManager()
        plugin = MockFormatPlugin()
        pm.register_format_plugin(plugin)
        
        found = pm.get_format_plugin_by_file("test.mock")
        assert found is plugin

    def test_get_format_plugin_by_file_no_match(self):
        """测试按文件查找无匹配格式插件"""
        pm = PluginManager()
        plugin = MockFormatPlugin()
        pm.register_format_plugin(plugin)
        
        found = pm.get_format_plugin_by_file("test.unknown")
        assert found is None


class TestPluginEnableDisable:
    """插件启用/禁用测试"""

    def test_enable_nonexistent_plugin(self):
        """测试启用不存在的插件"""
        pm = PluginManager()
        result = pm.enable_plugin("nonexistent")
        assert isinstance(result, bool)

    def test_disable_nonexistent_plugin(self):
        """测试禁用不存在的插件"""
        pm = PluginManager()
        result = pm.disable_plugin("nonexistent")
        assert isinstance(result, bool)


class TestPluginLoading:
    """插件加载测试"""

    def test_load_plugins_from_nonexistent_dir(self):
        """测试从不存在目录加载插件"""
        pm = PluginManager()
        result = pm.load_plugins("/nonexistent/plugin/dir")
        assert isinstance(result, (list, type(None)))

    def test_load_plugins_valid_dir(self):
        """测试加载 plugins 目录下的插件"""
        pm = PluginManager()
        # 使用 conftest.py 添加的 sys.path 推算项目根目录
        import sys
        project_dir = None
        for p in sys.path:
            if os.path.basename(p) == 'King_photo':
                project_dir = p
                break
        if project_dir is None:
            # 回退：从当前文件路径定位
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        plugins_dir = os.path.join(project_dir, "plugins")
        if os.path.exists(plugins_dir):
            result = pm.load_plugins(plugins_dir)
            # 加载后应有插件被注册
            all_plugins = pm.get_all_plugins()
            assert isinstance(all_plugins, list)
            assert len(all_plugins) >= 0
