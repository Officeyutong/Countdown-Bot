from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import GroupMessageEvent
from typing import List
import base64
from aip import AipSpeech


class ReadConfig(ConfigBase):
    MAX_STRING_LENGTH = 300

    # Baidu AI Apps
    APP_ID = ""
    API_KEY = ""
    SECRET_KEY = ""

    # Volume 1(low)-10(high)
    VOLUME = 8
    # Speech rate 1(slow)-10(quick)
    SPEED = 4


class ReadPlugin(Plugin):
    def get_voice(self, text: str) -> str:
        result = self.client.synthesis(text, 'zh', 1, {
            'vol': self.config.VOLUME,
            'per': 4,
            'spd': self.config.SPEED
        })
        if isinstance(result, dict):
            return ""
        else:
            return base64.encodebytes(result).decode().replace("\n", "")

    def command_read(self, plugin, args: List[str], raw_string: str, context, evt: GroupMessageEvent):
        def wrapper():
            text = " ".join(args)
            if len(text) > self.config.MAX_STRING_LENGTH:
                self.bot.send(context, "字符串过长")
            else:
                b64voice = self.get_voice(text)
                if b64voice:
                    self.bot.send(
                        context, f"[CQ:record,file=base64://{b64voice}]")
                else:
                    self.bot.send(context, "生成错误，请检查是否含有非法字符")
        self.bot.submit_multithread_task(wrapper)

    def on_enable(self):
        self.client = AipSpeech(
            self.config.APP_ID, self.config.API_KEY, self.config.SECRET_KEY)
        self.config: ReadConfig
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="read",
            command_handler=self.command_read,
            help_string="文字转语音",
            chats={ChatType.discuss, ChatType.group, ChatType.private},
        )


def get_plugin_class():
    return ReadPlugin


def get_config_class():
    return ReadConfig


def get_plugin_meta():
    return PluginMeta(
        "Antares", 2.0, "文字转语音"
    )
