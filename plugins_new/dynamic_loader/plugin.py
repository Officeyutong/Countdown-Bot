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

    def _process_str(self, command: str, to_replace: str) -> str:
        text: str = command.replace(to_replace, "", 1)
        return text.lstrip()

    async def command_load_async(self, plugin: "DynamicLoaderPlugin", args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        if not self.has_permission(evt.user_id):
            await self.bot.client_async.send(context, "你没有权限这样做")
            return
        to_execute = self._process_str(raw_string, "load-async")
        self.bot.logger.debug(to_execute)
        module = compile(to_execute,
                         mode="exec", filename="<dynamic-loader>")
        my_globals = dict()
        exec(module, my_globals)
        resp = await my_globals["run"](self, evt)
        if resp:
            await self.bot.client_async.send(context, str(resp))

    def command_load_sync(self, plugin: "DynamicLoaderPlugin", args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        if not self.has_permission(evt.user_id):
            self.bot.client.send(context, "你没有权限这样做")
            return
        my_globals = {
            "plugin": self,
            "evt": evt,
            "client": self.bot.client
        }
        to_execute = self._process_str(raw_string, "load-sync")
        self.bot.logger.debug(to_execute)
        exec(to_execute, my_globals)
        result = my_globals.get("result", "")
        if result:
            self.bot.client.send(context, str(result))

    def on_enable(self):
        self.config: DynamicLoaderConfig
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="load-async",
            command_handler=self.command_load_async,
            help_string="在Bot同环境下运行异步代码(实现run函数,提供plugin作为插件对象,evt作为MessageEvent对象)",
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
