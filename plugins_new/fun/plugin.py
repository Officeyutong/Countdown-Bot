from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.countdown_bot import CountdownBot
from typing import List, Dict

import time


class FunPluginConfig(ConfigBase):
    ENABLE_REPEATER = True
    BLACKLIST_GROUPS = []
    REPEAT_TIME_LIMIT = 3
    REPEAT_DELAY = 3 * 60  # 两次复读的最短时间间隔,s


class FunPlugin(Plugin):

    def repeater_listener(self, event: GroupMessageEvent):
        if event.group_id in self.config.BLACKLIST_GROUPS:
            self.bot.logger.debug(
                f"Ignoring message from blocked group: {event.group_id}")
            return
        group = event.group_id
        if group not in self.last_message:
            self.last_message[group] = None
            self.repeat_times[group] = 0
        if event.raw_message == self.last_message[group]:
            self.repeat_times[group] += 1
        else:
            self.repeat_times[group] = 1
            self.last_message[group] = event.raw_message
        if self.repeat_times[group] >= self.config.REPEAT_TIME_LIMIT:
            if time.time()-self.last_repeat_time.get(group, 0) < self.config.REPEAT_DELAY:
                self.logger.info(
                    f"Ignoring repeat at group {group} for too short interval.")
                return
            self.logger.info(f"Repeating at group {group}")
            self.last_repeat_time[group] = time.time()
            self.bot.send(event.context, self.last_message[group])
            self.last_message[group] = None
            self.repeat_times[group] = 0

    def on_enable(self):
        self.last_message: Dict[int, str] = dict()
        self.repeat_times: Dict[int, int] = dict()
        self.last_repeat_time: Dict[int, float] = dict()
        self.config: FunPluginConfig
        self.bot: CountdownBot
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
        self.register_event_listener(GroupMessageEvent, self.repeater_listener)

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
