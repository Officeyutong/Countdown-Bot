from common.plugin import Plugin, ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.command import ChatType
from common.event import MessageEvent
import aiohttp
from typing import List


class GeoQueryConfig(ConfigBase):
    # 高德地图API密钥
    API_KEY = "Qwqqwq"


class GeoQueryPlugin(Plugin):
    async def where_is(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        query_string = " ".join(args)
        async with self.client.get("https://restapi.amap.com/v3/place/text", params={
            "key": self.config.API_KEY,
            "keywords": query_string,
        }) as urlf:
            result = await urlf.json(encoding="utf-8")
            # print(result)
            if result["status"] != "1":
                self.bot.send(context, result["info"])
                return
            # print(result["pois"])
            if len(result["pois"]) == 0:
                self.bot.send(context, "搜索无结果")
                return

            target = (result["pois"][0])
            lon, lat = target["location"].split(",")
            await self.bot.client_async.send(
                context, f'[CQ:location,lat={lat},lon={lon},content={target["address"]},title={target["name"]}]')
            from io import StringIO
            buf = StringIO()
            for item in result["pois"][:5]:
                buf.write(
                    f'ID: {item["id"]} | 名称: {item["name"]} | 地址: {item["address"]} | 类型: {item["type"]}\n')
            await self.bot.client_async.send(context, buf.getvalue())

    async def where_id(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        spot_id = " ".join(args).strip()
        async with self.client.get("https://restapi.amap.com/v3/place/detail", params={
            "key": self.config.API_KEY,
            "id": spot_id
        }) as urlf:
            result = await urlf.json(encoding="utf-8")
            # print(result)
            if result["status"] != "1":
                await self.bot.client_async.send(context, result["info"])
                return
            # print(result["pois"])
            if len(result["pois"]) == 0:
                await self.bot.client_async.send(context, "搜索无结果")
                return
            target = (result["pois"][0])
            lon, lat = target["location"].split(",")
            await self.bot.client_async.send(
                context, f'[CQ:location,lat={lat},lon={lon},content={target["address"]},title={target["name"]}]')

    def on_enable(self):
        self.client = aiohttp.ClientSession()
        self.config: GeoQueryConfig
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="where",
            command_handler=self.where_is,
            help_string="高德地图搜索 | where [搜索内容(多个关键字以|分割)]",
            chats={ChatType.discuss, ChatType.group, ChatType.private},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="where-id",
            command_handler=self.where_id,
            help_string="高德地图精确查询 | where-id [地点ID]",
            chats={ChatType.discuss, ChatType.group, ChatType.private},
            is_async=True
        )


def get_plugin_class():
    return GeoQueryPlugin


def get_config_class():
    return GeoQueryConfig


def get_plugin_meta():
    return PluginMeta(
        "officeyutong", 2.0, "高德地图API查询"
    )
