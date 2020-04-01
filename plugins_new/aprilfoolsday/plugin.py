from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.countdown_bot import CountdownBot, APRIL_FOOL
from typing import List, Dict


class AprilFoolsDay(Plugin):
    async def like(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        import random
        if random.randint(1, 10) <= 5:
            await self.bot.client_async.send(context, "您给Bot点赞成功,点赞成功十次即可在明天继续使用Bot哦~")
        else:
            await self.bot.client_async.send(context, "您一不小心给Bot点了踩，自明天(2020-04-00)起，您不再具有使用本Bot的权限")

    def on_enable(self):
        self.register_command_wrapped(
            command_name="like",
            command_handler=self.like,
            help_string="给Bot点赞",
            chats={ChatType.group},
            is_async=True
        )


def get_plugin_class():
    if APRIL_FOOL:
        return AprilFoolsDay
    else:
        return None


def get_plugin_meta():
    return PluginMeta(
        "officeyutong", 2.0, "qwq"
    )
