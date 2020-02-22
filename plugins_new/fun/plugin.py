from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.event import MessageEvent
from common.command import ChatType
from typing import List


class FunPluginConfig(ConfigBase):
    ENABLE_REPEATER = True


class FunPlugin(Plugin):
    def on_enable(self):
        self.register_command_wrapped(
            command_name="阿克",
            command_handler=self.command_阿克,
            help_string="阿克",
            chats={ChatType.discuss, ChatType.group, ChatType.private}
        )
        self.register_command_wrapped(
            command_name="爆零",
            command_handler=self.command_爆零,
            help_string="qwq",
            chats={ChatType.discuss, ChatType.group, ChatType.private}
        )
        self.register_command_wrapped(
            command_name="凉了",
            command_handler=self.command_凉了,
            help_string="凉了？",
            chats={ChatType.discuss, ChatType.group, ChatType.private}
        )

    def command_阿克(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        self.bot.send(context, "您阿克了!")

    def command_爆零(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        self.bot.send(context, "您不会爆零的qwq")

    def command_凉了(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        self.bot.send(context, "qwq您不会凉的~")


def get_plugin_class():
    return FunPlugin


def get_config_class():
    return FunPluginConfig


def get_plugin_meta():
    return PluginMeta(
        "fun", 2.0, "包括复读机以及一些有意思的小指令"
    )
