from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.countdown_bot import CountdownBot
from typing import List, Dict

import qrcode
import base64
import tempfile
import os


class QRcodeConfig(ConfigBase):
    MAX_STRING_LENGTH = 500


class QRcodePlugin(Plugin):
    def make_qrcode(self, text: str) -> str:
        tergent = os.path.join(tempfile.mkdtemp(), "qrcode.png")
        image = qrcode.make(text)
        image.save(tergent)
        with open(tergent, "rb") as file:
            result = base64.encodebytes(
                file.read()).decode().replace("\n", "")
        return result

    def command_qrcode(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        def wrapper():
            text = evt.raw_message
            text = text.lstrip("--qrcode")
            text = text.lstrip("--二维码")
            text = text.strip()
            if len(text) > self.config.MAX_STRING_LENGTH:
                self.bot.client_async.send(context, "字符串超过限制")
                return
            self.bot.client_async.send(
                context, f"[CQ:image,file=base64://{self.make_qrcode(text)}]")
        self.bot.submit_multithread_task(wrapper)

    def on_enable(self):
        self.bot: CountdownBot
        self.config: QRcodeConfig
        self.register_command_wrapped(
            command_name="qrcode",
            command_handler=self.command_qrcode,
            help_string="生成二维码 | qrcode [字符串]",
            chats=ChatType.all(),
            alias=["二维码"]
        )


def get_plugin_class():
    return QRcodePlugin


def get_config_class():
    return QRcodeConfig


def get_plugin_meta():
    return PluginMeta(
        author="Antares",
        version=1.0,
        description="二维码生成器"
    )
