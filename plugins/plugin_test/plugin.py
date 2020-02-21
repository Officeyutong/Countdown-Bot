from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.command import Command
from common.event import Listener, MessageEvent
from typing import List


class MyEventListener(Listener):
    def __init__(self, plugin):
        self.plugin = plugin

    def message(self, evt: MessageEvent):
        self.plugin.logger.info(evt.message)
        self.plugin.logger.info(evt)


class MyPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_enable(self):
        # self.bot
        self.logger.info("You are loading Me!")
        self.logger.info(self.config.TEST_URL)
        self.register_command(
            self.wrap_command(
                "test",
                self.simple_command,
                "帮助qwqqwq",
                ["test1", "test2", "test3"]
            )
        )
        self.register_command(Command(
            self.plugin_id,
            "qwq",
            self.simple_console_command,
            self,
            "qwqqwq",
            is_console=True
        ))
        self.register_all_event_listeners(
            MyEventListener(self)
        )

    def simple_command(self, plugin: 'MyPlugin', args: List[str], raw_string: str, context: dict):
        print(locals())

    def simple_console_command(self, plugin: 'MyPlugin', args: List[str], raw_string: str, context: dict):
        print("qwqqwq")
        print(locals())

        async def qwqqwq():
            import asyncio
            await asyncio.sleep(5)
            self.logger.info("Meow~")
        self.bot.submit_async_task(qwqqwq())


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
