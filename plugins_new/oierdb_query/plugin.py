from common.plugin import Plugin
from common.countdown_bot import CountdownBot
from common.datatypes import PluginMeta
from common.event import MessageEvent
from common.command import ChatType
from typing import List
from random import shuffle
import re
import aiohttp
import io
import ast


class OIerdbQueryPlugin(Plugin):
    def on_enable(self):
        self.client = aiohttp.ClientSession()
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="oier",
            command_handler=self.oier_query,
            help_string="OIerDB(bytew.net/OIer) 查询 | oier [关键词]",
            chats={ChatType.group},
            is_async=True
        )

    async def oier_query(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        if not args:
            await self.bot.client_async.send(context, "请输入查询关键字qwq")
            return
        buf = io.StringIO()
        buf.write("查询到以下数据:\n")
        async with self.client.get("http://bytew.net/OIer/search.php", params={"method": "normal", "q": args[0]}) as resp:
            resp: aiohttp.ClientResponse
            items = (await resp.json(content_type=""))["result"]
        shuffle(items)
        for item in items[:5]:
            self.bot.logger.debug(f"Item: {item}")
            buf.write(
                f'姓名:{item["name"]}\n生理性别:{ {-1: "女", 1: "男"}.get(int(item["sex"]), "未知") }\n')
            for award in ast.literal_eval(item["awards"]):
                format_str = "在<{province}>{school}<{grade}>时参加<{contest}>以{score}分(全国排名{rank})的成绩获得<{type}>\n"
                buf.write(format_str.format(grade=award["grade"],
                                            province=award["province"],
                                            rank=award["rank"],
                                            score=award["score"],
                                            school=award["school"],
                                            type=award["award_type"],
                                            contest=award["identity"]
                                            ))
            buf.write("\n")
        if self.bot.april_fool:
            import random
            contests = random.choices(["CSP2019提高组", "IOI2019", "NOI2019", "NOIP2018", "IOI2018", "NOI2018", "NOIP2017", "IOI2017",
                                       "NOI2017", "NOIP2016", "IOI2016", "NOI2016", "NOIP2015", "IOI2015", "NOI2015"], k=5)
            grades = ["小学", "初一", "初二", "初三", "高一", "高二", "高三"]
            random.shuffle(contests)
            buf.write("\n姓名:咕咕倒计时\n生理性别:未知\n")
            for item in contests:
                group_name = (await self.bot.client_async.get_group_info(group_id=evt.group_id))["group_name"]
                buf.write(
                    f"在<QQ>{group_name}<{random.choice(grades)}>时参加<{item}>以600分(全国排名1)的成绩获得<金牌>\n")
        if len(items) > 5:
            buf.write("\n请去原网站查看完整数据")
        await self.bot.client_async.send(context, buf.getvalue())


def get_plugin_class():
    return OIerdbQueryPlugin


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="OIerDB(http://bytew.net/OIer)查询"
    )
