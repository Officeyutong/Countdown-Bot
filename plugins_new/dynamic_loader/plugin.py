from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.countdown_bot import CountdownBot
from typing import List, Dict, Set


class DynamicLoaderConfig(ConfigBase):
    ALLOWED_USERS: Set[int] = set()


class DynamicLoaderPlugin(Plugin):
    def has_permission(self, user_id: int) -> bool:
        return user_id in self.config.ALLOWED_USERS

    async def command_load_async(self, plugin: "DynamicLoaderPlugin", args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        if not self.has_permission(evt.user_id):
            await self.bot.client_async.send(context, "你没有权限这样做")
            return
        module = compile(raw_string.replace("load-async", "", 1),
                         mode="exec", filename="<dynamic-loader>")
        my_globals = dict()
        exec(module, my_globals)
        resp = await my_globals["func"](self, evt)
        if resp:
            await self.bot.client_async.send(context, repr(resp))

    def command_load_sync(self, plugin: "DynamicLoaderPlugin", args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        if not self.has_permission(evt.user_id):
            self.bot.client.send(context, "你没有权限这样做")
            return
        my_globals = {
            "plugin": self,
            "evt": evt,
            "client": self.bot.client
        }
        exec(raw_string.replace("load-sync", "", 1), my_globals)
        result = my_globals.get("result", "")
        if result:
            self.bot.client.send(context, repr(result))

    def on_enable(self):
        self.config: DynamicLoaderConfig
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="load-async",
            command_handler=self.command_load_async,
            help_string="在Bot同环境下运行异步代码(实现func函数,提供plugin作为插件对象,evt作为MessageEvent对象)",
            chats=ChatType.all(),
            is_async=True
        )
        self.register_command_wrapped(
            command_name="load-sync",
            command_handler=self.command_load_sync,
            help_string="在Bot同环境下运行代码(提供plugin和evt作为全局对象,result用于输出结果)",
            chats=ChatType.all(),
        )


def get_plugin_class():
    return DynamicLoaderPlugin


def get_config_class():
    return DynamicLoaderConfig


def get_plugin_meta():
    return PluginMeta(
        author="MikuNotFoundException",
        version=1.0,
        description="动态添加事件监听器/调用API"
    )
