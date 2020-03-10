from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import MessageEvent
from typing import Dict, List
from io import StringIO
import aiohttp


class OIWikiPlugin(Plugin):
    async def search_oiwiki(self, keywords: str) -> List[dict]:
        try:
            async with self.aioclient.get("https://search.oi-wiki.org:8443", params={
                "s": keywords
            }) as resp:
                resp: aiohttp.ClientResponse
                result = await resp.json()
            return result
        except Exception as ex:
            self.logger.exception(ex)

    async def command_oiwiki(self, plugin, args: List[str], raw_string: str, context, evt: MessageEvent):
        if len(args) == 0:
            await self.bot.client_async.send(context, "请输入查询内容")
            return
        keywords = " ".join(args)
        try:
            result = await self.search_oiwiki(keywords)
        except Exception:
            await self.bot.client_async.send(context,"连接查询服务器出错")
            return
        buf = StringIO()
        buf.write(f"查询到{len(result)}条相关内容：\n")
        for index, item in enumerate(result):
            buf.write(f"{item['title']}: https://oi-wiki.org{item['url']}\n\n")
        await self.bot.client_async.send(context, buf.getvalue())

    def on_enable(self):
        self.aioclient = aiohttp.ClientSession()
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="oiwiki",
            command_handler=self.command_oiwiki,
            help_string="OI-Wiki查询 | oiwiki [查询关键字]",
            chats=ChatType.all(),
            is_async=True
        )


def get_plugin_class():
    return OIWikiPlugin


def get_plugin_meta():
    return PluginMeta(
        "Antares", 1.0, "OI-Wiki查询"
    )
