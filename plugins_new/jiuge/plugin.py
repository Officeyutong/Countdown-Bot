from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.event import MessageEvent
from common.command import ChatType
import aiohttp
from typing import List
import uuid
import asyncio
import json


class JiugeConfig(ConfigBase):
    # 生成时限
    TIME_LIMIT = 10
    # 重试次数
    RETRY_TIMES = 50
    ROOT_URL = "http://118.190.162.99:8080"

class JiugePlugin(Plugin):
    def command_help(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        self.bot.client.send(context, HELP_STRING)

    async def command_jiuge(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        _args = {"genre": "1", "keyword": "关键词",
                 "yan": "5", "style": "0", "image": "off"}
        for item in args:
            item = item.strip()
            try:
                name, val = item.split(":", 1)
                if name not in _args:
                    raise NameError()
            except:
                await self.bot.client_async.send(context, f"非法参数: {item}")
                return
            _args[name] = val
        genre, keyword, yan, style, image = _args["genre"], _args[
            "keyword"], _args["yan"], _args["style"], _args["image"] == "on"
        self.bot.logger.info(f"Generating...{_args}")
        if genre not in "142753":
            await self.bot.client_async.send(context, "非法体裁")
            return
        user_id = str(uuid.uuid1())[:30]
        await self.bot.client_async.send(
            context, f"开始生成{user_id}\n体裁: {genre}\n关键词:{keyword}\n单句长度:{yan}\n样式:{style}")

        async def handle():
            try:
                # async with self.client.post(f"{self.config.ROOT_URL}/getKeyword", data={
                #     "level": 1,
                #     "genre": genre,
                #         "keywords": keyword}) as urlf:
                #     urlf: aiohttp.ClientResponse
                #     resp_json = await urlf.json(content_type="")
                #     if resp_json["code"] == "mgc":
                #         await self.bot.client_async.send(context, f"主题 {keyword} 无法作诗")
                #         return
                #     elif resp_json["code"] != '0':
                #         await self.bot.client_async.send(context, resp_json["info"])
                #         return
                #     keywords: List[dict] = resp_json["data"]
                # self.bot.logger.info(f"Keywords: {keywords}")
                async with self.client.post(f"{self.config.ROOT_URL}/sendPoem", data={
                    "style": style,
                    "genre": genre,
                    "yan": yan,
                    "user_id": user_id,
                    "keyword": keyword
                }) as urlf:
                    resp_json = await urlf.json(content_type="")
                    print("send response =", resp_json)
                    resp_json["code"] = str(resp_json["code"])
                    if resp_json["code"] == "mgc":
                        await self.bot.client_async.send(context, f"主题 {keyword} 无法作诗")
                        return
                    elif resp_json["code"] == "777":
                        await self.bot.client_async.send(context, f"九歌服务器出错")
                        return
                    elif resp_json["code"] != '0':
                        await self.bot.client_async.send(context, resp_json["info"])
                        return
                done = False
                for i in range(self.config.RETRY_TIMES):
                    async with self.client.post(f"{self.config.ROOT_URL}/getPoem", data={
                        "style": style,
                        "genre": genre,
                        "yan": yan,
                        "user_id": user_id,
                        "keywords": json.dumps(keywords)
                    }) as urlf:
                        self.logger.debug("Fetching...")
                        resp_json = await urlf.json(content_type="")
                        resp_json["code"] = str(resp_json["code"])
                        if resp_json["code"] == "mgc":
                            await self.bot.client_async.send(context, f"主题 {keyword} 无法作诗")
                            return
                        elif resp_json["code"] == "1":
                            await asyncio.sleep(0.5)
                            continue
                        if resp_json["code"] not in {"1", "0", "666"}:
                            await self.bot.client_async.send(context, "九歌服务器错误")
                            return
                        generate_result = resp_json
                        done = True
                        break
                    
                if not done:
                    raise Exception(f"{user_id} 重试次数过多")
                from io import StringIO
                buf = StringIO()
                buf.write(f"{user_id} 生成完成\n")
                result_data = generate_result["data"]
                if "score" in result_data:
                    buf.write(" ".join((f"{x}:{y}" for x, y in zip(
                        ["通顺性", "连贯性", "新颖性", "意境"], result_data["score"]))))
                    buf.write("\n")
                buf.write("\n")
                if str(genre) in {"1", "4", "2", "7"}:
                    buf.writelines((line+"\n" for line in result_data["poem"]))
                elif str(genre) == "5":
                    buf.writelines(
                        (f"{line} --- {src}\n" for line, src in zip(result_data["poem"], result_data["source"])))
                elif str(genre) == "3":
                    buf.writelines(
                        ("\n".join(section)+"\n\n" for section in result_data["poem"]))
                self.bot.logger.info(generate_result)
                if image:
                    async with self.client.post(f"{self.config.ROOT_URL}/share", data={
                        "style": style,
                        "genre": genre,
                        "yan": yan,
                        "keywords": keyword,
                        "user_id": user_id,
                        "lk": "",
                        "user_poem": json.dumps(result_data["poem"])
                    }) as urlf:
                        image_file = (await urlf.json(content_type=""))["data"]
                        buf.write(
                            f"[CQ:image,file={self.config.ROOT_URL}/share/new/{image_file}]")

                await self.bot.client_async.send(context, buf.getvalue())
            except Exception as ex:
                await self.bot.client_async.send(context, str(ex))
                raise ex

        # async def wrapper():
        try:
            await asyncio.wait_for(handle(), timeout=self.config.TIME_LIMIT)
        except asyncio.exceptions.TimeoutError:
            await self.bot.client_async.send(context, f"{user_id} 生成超时")

        # self.bot.submit_async_task(wrapper())

    def on_enable(self):
        self.bot: CountdownBot
        self.config: JiugeConfig
        self.client = aiohttp.ClientSession()
        self.register_command_wrapped(
            command_name="jiuge-help",
            command_handler=self.command_help,
            help_string="查看九歌爬虫帮助",
            chats={ChatType.discuss, ChatType.group, ChatType.private},
        )
        self.register_command_wrapped(
            command_name="jiuge",
            command_handler=self.command_jiuge,
            help_string="使用九歌作诗 | 输入jiuge-help查看帮助",
            chats={ChatType.discuss, ChatType.group},
            is_async=True
        )


def get_plugin_class():
    return JiugePlugin


def get_config_class():
    return JiugeConfig


def get_plugin_meta():
    return PluginMeta(
        "officeyutong", 2.0, "九歌(http://jiuge.thunlp.cn/)爬虫"
    )


HELP_STRING = """
此功能调用http://jiuge.thunlp.cn/生成诗歌。

使用方法:

jiuge 参数1:值1 参数2:值2 ....

参数取值为genre(默认为1) yan(默认为5) style(默认为0) keyword(默认为"关键词") image(默认为off) 其中keyword为作诗的关键词,image:{on,off}为是否输出图片

例如以下为部分合法的调用:

jiuge keyword:爱国 yan:5 genre:1 style:2 image:on
作主题为爱国，风格为孤寂惆怅的五言风格绝句并输出图像

jiuge keyword:喵喵喵 genre:3 style:18 image:on 
作 浣溪沙·喵喵喵 并输出图片

体裁 genre:
1 - 绝句    4 - 风格绝句    2 - 藏头诗  7 - 律诗    5 - 集句诗
3 - 词

每句长度 yan:
5 - 五言
7 - 七言

样式 style:
    风格绝句:
        0 - 萧瑟凄凉        1 - 忆旧感喟        2 - 孤寂惆怅        3 - 思乡忧老
        4 - 渺远孤逸
    藏头诗:
        0 - 悲伤        1 - 较悲伤        2 - 中性        3 - 较喜悦
        4 - 喜悦
    词牌:
        0 - 归字谣        1 - 如梦令        2 - 梧桐影        3 - 渔歌子
        4 - 捣练子        5 - 忆江南        6 - 秋风清        7 - 忆王孙
        8 - 河满子        9 - 思帝乡        10 - 望江怨        11 - 醉吟商
        12 - 卜算子        13 - 点绛唇        14 - 乌夜啼        15 - 江亭怨
        16 - 踏莎行        17 - 画堂春        18 - 浣溪沙        19 - 武陵春
        20 - 采桑子        21 - 城头月        22 - 玉楼春        23 - 海棠春
        24 - 苏幕遮        25 - 蝶恋花        26 - 江城子        27 - 八声甘州
        28 - 声声慢        29 - 水龙吟        30 - 满江红        31 - 沁园春
"""
