from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import MessageEvent
from typing import Dict, List
import aiohttp


class CoupletPlugin(Plugin):
    async def command_couplet(self, plugin, args: List[str], raw_string: str, context, evt: MessageEvent):
        try:
            in_str = args[0]
            # Supported by https://ai.binwang.me/couplet/
            async with self.aioclient.get(f"https://ai-backend.binwang.me/chat/couplet/{in_str}") as resp:
                out_str = (await resp.json())["output"]
            await self.bot.client_async.send(context, f"上联：{in_str}\n下联：{out_str}")
        except Exception as ex:
            self.bot.logger.exception(ex)
            await self.bot.client_async.send(context, f"Error: {ex}")

    def on_enable(self):
        self.aioclient = aiohttp.ClientSession()
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="couplet",
            command_handler=self.command_couplet,
            help_string="对联机 | couplet 上联",
            chats=ChatType.all(),
            alias=["对联"],
            is_async=True
        )

def get_plugin_class():
    return CoupletPlugin


def get_plugin_meta():
    return PluginMeta(
        "Antares", 1.0, "对联机"
    )