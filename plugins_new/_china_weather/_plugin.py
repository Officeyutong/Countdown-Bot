"""
本插件暂时废弃
"""

from common.plugin import Plugin
from common.countdown_bot import CountdownBot
from common.datatypes import PluginMeta
from common.event import MessageEvent
from common.command import ChatType
from typing import List, Dict
import pyppeteer
import aiohttp
import ast


class ChinaWeatherPlugin(Plugin):

    async def command_weather(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        if not args:
            await self.bot.client_async.send(context, "请输入城市名")
            return
        async with self.client.get("http://toy1.weather.com.cn/search", params={
            "cityname": args[0]
        }) as resp:
            resp: aiohttp.ClientResponse
            data = ast.literal_eval(await resp.text())
        broswer = pyppeteer.launch()
        page = await broswer.newPage()

    def on_enable(self):
        self.bot: CountdownBot
        self.client = aiohttp.ClientSession()


def get_plugin_class():
    return ChinaWeatherPlugin


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="中国天气网爬虫"
    )
