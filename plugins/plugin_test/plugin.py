from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase


class MyPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_load(self):
        # self.bot
        print(self.config.TEST_URL)


class MyPluginConfig(ConfigBase):
    TEST_URL: str = "default_value"


def get_plugin_class():
    return MyPlugin


def get_config_class():
    return MyPluginConfig


def get_plugin_meta():
    return PluginMeta(
        "qwqqwwq", 1.0, "测试一下"
    )
