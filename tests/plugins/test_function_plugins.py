"""
King_photo - 功能插件测试
测试所有已注册的功能插件
"""

import os
import sys
import pytest

from src.api.plugin_interfaces import IFunctionPlugin


def get_function_plugins():
    """获取所有功能插件"""
    project_dir = None
    for p in sys.path:
        if os.path.basename(p) == 'King_photo':
            project_dir = p
            break
    if project_dir is None:
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    plugins_dir = os.path.join(project_dir, "plugins", "functions")
    plugins = []
    if os.path.exists(plugins_dir):
        for f in os.listdir(plugins_dir):
            if f.endswith('.py') and not f.startswith('__'):
                plugins.append(f[:-3])
    return plugins


FUNCTION_PLUGINS = get_function_plugins()


class TestFunctionPluginInterface:
    """功能插件接口一致性测试"""

    @pytest.mark.parametrize("plugin_name", FUNCTION_PLUGINS)
    def test_plugin_can_import(self, plugin_name):
        """测试插件可导入"""
        module = __import__(f"plugins.functions.{plugin_name}", fromlist=["*"])
        assert module is not None

    @pytest.mark.parametrize("plugin_name", FUNCTION_PLUGINS)
    def test_plugin_has_plugin_name(self, plugin_name):
        """测试插件有 plugin_name 属性"""
        module = __import__(f"plugins.functions.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFunctionPlugin) and 
                attr is not IFunctionPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'plugin_name')
                assert isinstance(plugin_instance.plugin_name, str)
                assert len(plugin_instance.plugin_name) > 0

    @pytest.mark.parametrize("plugin_name", FUNCTION_PLUGINS)
    def test_plugin_has_plugin_type(self, plugin_name):
        """测试插件有 plugin_type 属性"""
        module = __import__(f"plugins.functions.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFunctionPlugin) and 
                attr is not IFunctionPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'plugin_type')
                assert isinstance(plugin_instance.plugin_type, str)

    @pytest.mark.parametrize("plugin_name", FUNCTION_PLUGINS)
    def test_plugin_has_description(self, plugin_name):
        """测试插件有 description 属性"""
        module = __import__(f"plugins.functions.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFunctionPlugin) and 
                attr is not IFunctionPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'description')
                assert isinstance(plugin_instance.description, str)

    @pytest.mark.parametrize("plugin_name", FUNCTION_PLUGINS)
    def test_plugin_has_execute(self, plugin_name):
        """测试插件有 execute 方法"""
        module = __import__(f"plugins.functions.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFunctionPlugin) and 
                attr is not IFunctionPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'execute')

    @pytest.mark.parametrize("plugin_name", FUNCTION_PLUGINS)
    def test_plugin_has_version(self, plugin_name):
        """测试插件有 version 属性"""
        module = __import__(f"plugins.functions.{plugin_name}", fromlist=["*"])
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, IFunctionPlugin) and 
                attr is not IFunctionPlugin):
                plugin_instance = attr()
                assert hasattr(plugin_instance, 'version')
                assert isinstance(plugin_instance.version, str)


class TestFunctionPluginRegistration:
    """功能插件注册测试"""

    def test_register_all_function_plugins(self):
        """测试所有功能插件都能注册到 PluginManager"""
        from src.api.plugin_manager import PluginManager
        
        pm = PluginManager()
        project_dir = None
        for p in sys.path:
            if os.path.basename(p) == 'King_photo':
                project_dir = p
                break
        if project_dir is None:
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        plugins_dir = os.path.join(project_dir, "plugins", "functions")
        
        if os.path.exists(plugins_dir):
            for f in os.listdir(plugins_dir):
                if f.endswith('.py') and not f.startswith('__'):
                    module_name = f[:-3]
                    module = __import__(f"plugins.functions.{module_name}", fromlist=["*"])
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, IFunctionPlugin) and 
                            attr is not IFunctionPlugin):
                            plugin_instance = attr()
                            pm.register_function_plugin(plugin_instance)
                            assert pm.get_function_plugin(plugin_instance.plugin_name) is not None
