from common.plugin import Plugin
from common.countdown_bot import CountdownBot
from common.datatypes import PluginMeta
from common.event import MessageEvent
from common.command import ChatType
from typing import List, Dict
import re
import aiohttp
import io
import bs4
import ujson
import time
import datetime


class COVID19QueryPlugin(Plugin):

    def on_enable(self):
        self.client = aiohttp.ClientSession()
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="covnews",
            command_handler=self.command_covid2019_news,
            help_string="查询 COVID19 最近五条新闻",
            chats=ChatType.all(),
            is_async=True
        )
        self.register_command_wrapped(
            command_name="covid19",
            command_handler=self.command_covi19_query,
            help_string="查询国内 COVID19 疫情 | covid19 [省份]",
            chats=ChatType.all(),
            is_async=True
        )

    async def command_covi19_query(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        async with self.client.get("https://3g.dxy.cn/newh5/view/pneumonia") as resp:
            resp: aiohttp.ClientResponse
            soup = bs4.BeautifulSoup(await resp.text(encoding="utf-8"), "lxml")
        script = soup.select_one("#getAreaStat")
        expr = re.compile(r"(\[.*\])")

        data: List[Dict[str, dict]] = ujson.decode(
            expr.search(script.string).groups()[0])
        statistics = ujson.decode(re.compile(
            r"= (\{.*\})\}catch").search(soup.select_one("#getStatisticsService").string).groups()[0])
        self.bot.logger.debug(ujson.encode(statistics, ensure_ascii=False))
        update_time: time.struct_time = time.localtime(
            statistics["modifyTime"]//1000)

        def make_increase_string(key: str):
            if key not in statistics:
                return ""
            val = statistics[key]
            if val == 0:
                return f"{str(val)}"
            elif val < 0:
                return f"{str(val)}"
            else:
                return f"(+{val})"
        broadcast = f"{statistics['confirmedCount']} 累计确诊{make_increase_string('confirmedIncr')} |\
 {statistics['currentConfirmedCount']} 当前确诊{make_increase_string('currentConfirmedIncr')} |\
 {statistics['suspectedCount']} 疑似{make_increase_string('suspectedIncr')} |\
 {statistics['curedCount']} 治愈{make_increase_string('curedIncr')} |\
 {statistics['seriousCount']} 重症{make_increase_string('seriousIncr')} |\
 {statistics['deadCount']} 死亡{make_increase_string('deadIncr')}\n\
更新于{time.strftime('%Y.%m.%d %H:%M:%S', update_time)}"
        from io import StringIO
        buf = StringIO()
        buf.write("数据来源: 丁香医生\n")
        # buf.write(str(soup.select_one(".title___2d1_B").cmd.text)+"\n")
        buf.write(broadcast)
        buf.write("\n\n")

        def generate_line(obj):
            return f"{obj['provinceName'] if 'provinceName' in obj else obj['cityName']} 已确认 {obj['confirmedCount']} 疑似 {obj['suspectedCount']} 治愈 {obj['curedCount']} 死亡 {obj['deadCount']}"

        async def handle_province(obj):
            buf.write(generate_line(obj))
            buf.write("\n\n")
            for city in obj["cities"]:
                buf.write(generate_line(city)+"\n")
            await self.bot.client_async.send(context, buf.getvalue())

        async def handle_global():
            for item in data:
                buf.write(generate_line(item)+"\n")
            await self.bot.client_async.send(context, buf.getvalue())

        if not args:
            await handle_global()
        else:
            for item in data:
                if args[0] in item["provinceName"]:
                    await handle_province(item)
                    return
            await self.bot.client_async.send(context, "请输入正确的省份名称")

    async def command_covid2019_news(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        async with self.client.get("https://3g.dxy.cn/newh5/view/pneumonia") as resp:
            soup = bs4.BeautifulSoup(await resp.text(), "lxml")
            script = soup.select_one("#getTimelineService")
        expr = re.compile(r"(\[.*\])")

        data: List[Dict[str, dict]] = ujson.decode(
            expr.search(script.string).groups()[0])
        statistics = ujson.decode(re.compile(
            r"= (\{.*\})\}catch").search(soup.select_one("#getStatisticsService").string).groups()[0])
        update_time: time.struct_time = time.localtime(
            statistics["modifyTime"]//1000)
        # print(broadcast.text)
        from io import StringIO
        buf = StringIO()
        buf.write(
            f"数据来源: 丁香医生\n更新于{time.strftime('%Y.%m.%d %H:%M:%S', update_time)}")
        # buf.write(str(soup.select_one(".mapTitle___2QtRg").text)+"\n")
        buf.write("\n\n")
        for item in data[:5]:
            buf.write(f"""{item["title"]} - {item["infoSource"]} - {item["pubDateStr"]}
            {item["sourceUrl"]}
            {item["summary"]}

            """)
        await self.bot.client_async.send(context, buf.getvalue())


def get_plugin_class():
    return COVID19QueryPlugin


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="丁香园COVID19数据查询"
    )
