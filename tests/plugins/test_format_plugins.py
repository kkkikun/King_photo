"""
King_photo - 格式插件测试
测试所有已注册的格式插件
"""

import os
import sys
import pytest

from src.api.plugin_interfaces import IFormatPlugin


def get_format_plugins():
    """获取所有格式插件"""
    # 从 sys.path 获取项目根目录
    project_dir = None
    for p in sys.path:
        if os.path.basename(p) == 'King_photo':
            project_dir = p
            break
    if project_dir is None:
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    plugins_dir = os.path.join(project_dir, "plugins", "formats")
    plugins = []
    if os.path.exists(plugins_dir):
        for f in os.listdir(plugins_dir):
            if f.endswith('.py') and not f.startswith('__'):
                plugins.append(f[:-3])
    return plugins


# 动态获取可测试的插件列表
FORMAT_PLUGINS = get_format_plugins()


class TestFormatPluginInterface:
    """格式插件接口一致性测试"""

    @pytest.mark.parametrize("plugin_name", FORMAT_PLUGINS)
    def test_plugin_can_import(self, plugin_name):
        """测试插件可导入"""
        module = __import__(f"plugins.formats.{plugin_name}", fromlist=["*"])
        assert module is not None

    @pytest.mark.parametrize("plugin_name", FORMAT_PLUGINS)
    def test_plugin_has_format_name(self, plugin_name):
        """测试插件有 format_name 属性"""
        module = __import__(f"plugins.formats.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFormatPlugin) and 
                attr is not IFormatPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'format_name')
                assert isinstance(plugin_instance.format_name, str)
                assert len(plugin_instance.format_name) > 0

    @pytest.mark.parametrize("plugin_name", FORMAT_PLUGINS)
    def test_plugin_has_extensions(self, plugin_name):
        """测试插件有 extensions 属性"""
        module = __import__(f"plugins.formats.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFormatPlugin) and 
                attr is not IFormatPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'extensions')
                assert isinstance(plugin_instance.extensions, list)
                assert len(plugin_instance.extensions) > 0

    @pytest.mark.parametrize("plugin_name", FORMAT_PLUGINS)
    def test_plugin_has_description(self, plugin_name):
        """测试插件有 description 属性"""
        module = __import__(f"plugins.formats.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFormatPlugin) and 
                attr is not IFormatPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'description')
                assert isinstance(plugin_instance.description, str)

    @pytest.mark.parametrize("plugin_name", FORMAT_PLUGINS)
    def test_plugin_is_available(self, plugin_name):
        """测试插件 is_available 方法"""
        module = __import__(f"plugins.formats.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFormatPlugin) and 
                attr is not IFormatPlugin):
                plugin_instance = attr()
                result = plugin_instance.is_available()
                assert isinstance(result, bool)

    @pytest.mark.parametrize("plugin_name", FORMAT_PLUGINS)
    def test_plugin_read_metadata(self, plugin_name):
        """测试插件 read_metadata 方法签名"""
        module = __import__(f"plugins.formats.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFormatPlugin) and 
                attr is not IFormatPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'read_metadata')

    @pytest.mark.parametrize("plugin_name", FORMAT_PLUGINS)
    def test_plugin_get_datetime(self, plugin_name):
        """测试插件 get_datetime 方法签名"""
        module = __import__(f"plugins.formats.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFormatPlugin) and 
                attr is not IFormatPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'get_datetime')


class TestFormatPluginRegistration:
    """格式插件注册测试"""

    def test_register_all_format_plugins(self):
        """测试所有格式插件都能注册到 PluginManager"""
        from src.api.plugin_manager import PluginManager
        
        pm = PluginManager()
        # 从 sys.path 获取项目根目录
        project_dir = None
        for p in sys.path:
            if os.path.basename(p) == 'King_photo':
                project_dir = p
                break
        if project_dir is None:
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        plugins_dir = os.path.join(project_dir, "plugins", "formats")
        
        if os.path.exists(plugins_dir):
            for f in os.listdir(plugins_dir):
                if f.endswith('.py') and not f.startswith('__'):
                    module_name = f[:-3]
                    module = __import__(f"plugins.formats.{module_name}", fromlist=["*"])
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, IFormatPlugin) and 
                            attr is not IFormatPlugin):
                            plugin_instance = attr()
                            pm.register_format_plugin(plugin_instance)
                            assert pm.get_format_plugin(plugin_instance.format_name) is not None
