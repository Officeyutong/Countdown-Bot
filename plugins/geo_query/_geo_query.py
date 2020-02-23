from common.datatypes import PluginMeta
from common.plugin import dataclass_wrapper

from global_vars import CONFIG
from register import command

from cqhttp import CQHttp
from typing import List

import requests
config = CONFIG.get(__name__, None)
plugin = dataclass_wrapper(lambda: PluginMeta(
    author="officeyutong",
    version=1.0,
    description="高德地图API封装"
))


@command(name="where", help="高德地图搜索 | where [搜索内容(多个关键字以|分割)]")
def where_is(bot: CQHttp, context: dict, args: List[str]):
    query_string = " ".join(args[1:])
    with requests.get("https://restapi.amap.com/v3/place/text", params={
        "key": config.API_KEY,
        "keywords": query_string,
    }) as urlf:
        result = urlf.json(encoding="utf-8")
        # print(result)
        if result["status"] != "1":
            bot.send(context, result["info"])
            return
        # print(result["pois"])
        if len(result["pois"]) == 0:
            bot.send(context, "搜索无结果")
            return
        
        target = (result["pois"][0])
        lon, lat = target["location"].split(",")
        bot.send(
            context, f'[CQ:location,lat={lat},lon={lon},content={target["address"]},title={target["name"]}]')
        from io import StringIO
        buf = StringIO()
        for item in result["pois"][:5]:
            buf.write(
                f'ID: {item["id"]} | 名称: {item["name"]} | 地址: {item["address"]} | 类型: {item["type"]}\n')
        bot.send(context, buf.getvalue())


@command(name="where-id", help="高德地图精确查询 | where-id [地点ID]")
def where_id(bot: CQHttp, context: dict, args: List[str]):
    spot_id = " ".join(args[1:]).strip()
    with requests.get("https://restapi.amap.com/v3/place/detail", params={
        "key": config.API_KEY,
        "id": spot_id
    }) as urlf:
        result = urlf.json(encoding="utf-8")
        # print(result)
        if result["status"] != "1":
            bot.send(context, result["info"])
            return
        # print(result["pois"])
        if len(result["pois"]) == 0:
            bot.send(context, "搜索无结果")
            return
        target = (result["pois"][0])
        lon, lat = target["location"].split(",")
        bot.send(
            context, f'[CQ:location,lat={lat},lon={lon},content={target["address"]},title={target["name"]}]')
