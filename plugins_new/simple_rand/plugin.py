from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import GroupMessageEvent
from typing import List


class SimpleRandConfig(ConfigBase):
    MAX_NUMBER_COUNT = 20


class SimpleRandPlugin(Plugin):
    def on_enable(self):
        self.bot: CountdownBot
        self.config: SimpleRandConfig
        self.register_command_wrapped(
            command_name="rand",
            command_handler=self.command_rand,
            help_string="生成随机数 | rand [上限] [生成个数(可选)]",
            chats={ChatType.group, ChatType.discuss, ChatType.private},
            alias=["随机"]
        )

    def command_rand(self, plugin, args: List[str], raw_string: str, context, evt: GroupMessageEvent):
        try:
            upper, *other = (int(x) for x in args)
        except Exception as ex:
            self.bot.send(context, "请输入合法参数")
            raise ex
        if not other:
            count = 1
        else:
            count = other[0]
        if count > self.config.MAX_NUMBER_COUNT:
            self.bot.send(context, "您输入的数值过大")
            return
        from io import StringIO
        from random import randint
        buf = StringIO()
        buf.write("随机数结果:\n")
        for x in range(count):
            buf.write(f"{randint(1,upper)}\n")
        self.bot.send(context, buf.getvalue())


def get_plugin_class():
    return SimpleRandPlugin


def get_config_class():
    return SimpleRandConfig


def get_plugin_meta():
    return PluginMeta(
        "officeyutong", 2.0, "简单随机数产生器"
    )
