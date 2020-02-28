from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.countdown_bot import CountdownBot
from typing import List, Dict
from . import ds_drawer
import base64


class DSDrawerConfig(ConfigBase):
    MAX_STRING_LENGTH = 20


class DSDrawerPlugin(Plugin):
    def on_enable(self):
        self.bot: CountdownBot
        self.config: DSDrawerConfig
        self.register_command_wrapped(
            command_name="sam",
            command_handler=self.sam,
            help_string="绘制后缀自动机 | sam [字符串]",
            chats={ChatType.group},
        )

    def sam(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        def wrapper():
            if not args:
                self.bot.client.send(context, "请输入字符串")
                return
            string = " ".join(args)
            if len(string) > self.config.MAX_STRING_LENGTH:
                self.bot.client.send(context, "字符串过长")
                return
            self.logger.info(f"Started... {string}")
            imgpath = ds_drawer.generate_graph(string, "png")
            self.logger.info(f"Done... {string}")
            result = ""
            with open(imgpath, "rb") as file:
                result = base64.encodebytes(
                    file.read()).decode().replace("\n", "")
            self.bot.client.send(
                context, "[CQ:image,file=base64://{}]".format(result))
        self.bot.submit_multithread_task(wrapper)


def get_plugin_class():
    return DSDrawerPlugin


def get_config_class():
    return DSDrawerConfig


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="SAM绘制器"
    )
