from register import command
from common.datatypes import PluginMeta
from common.plugin import dataclass_wrapper

from cqhttp import CQHttp
from typing import List

import requests
import threading
import time
import global_vars
from util import stop_thread
config = global_vars.CONFIG[__name__]
plugin = dataclass_wrapper(lambda: PluginMeta(
    "officeyutong",
    1.0,
    "九歌(http://jiuge.thunlp.cn/)爬虫"
))

HELP_STRING = """
此功能调用http://jiuge.thunlp.cn/生成诗歌。

使用方法:

jiuge 参数1:值1 参数2:值2 ....

参数取值为genre yan style keyword,image其中keyword为作诗的关键词,image:{on,off}为是否输出图片

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


@command(name="jiuge-help", help="查看九歌爬虫帮助")
def jiuge_help(bot: CQHttp, context, *args):
    bot.send(context, HELP_STRING)


@command(name="jiuge", help="使用九歌作诗 | 输入jiuge-help查看帮助")
def jiuge(bot: CQHttp, context: dict, input_args: List[str]):
    while input_args and not input_args[-1].strip():
        input_args.pop()

    args = {"genre": 1, "keyword": "关键词", "yan": 5, "style": 0, "image": "off"}
    for item in input_args[1:]:
        item = item.strip()
        try:
            name, val = item.split(":", 1)
            if name not in args:
                raise NameError()
        except:
            bot.send(context, f"非法参数: {item}")
            return
        args[name] = val
        # print(name, "=", val)
        # locals()[name] = val
    genre, keyword, yan, style, image = args["genre"], args[
        "keyword"], args["yan"], args["style"], args["image"] == "on"
    client = requests.session()
    begin_time = time.time()
    import uuid
    import json
    user_id = str(uuid.uuid1())[:30]
    bot.send(
        context, f"开始生成{user_id}\n体裁: {genre}\n关键词:{keyword}\n单句长度:{yan}\n样式:{style}")

    def time_monitor():

        def handle():
            try:
                with client.post("http://jiuge.thunlp.cn/getKeyword", data={
                    "level": 1,
                    "genre": genre,
                        "keywords": keyword}) as urlf:
                    resp_json = urlf.json()
                    if resp_json["code"] == "mgc":
                        bot.send(context, f"主题 {keyword} 无法作诗")
                        return
                    elif resp_json["code"] != '0':
                        bot.send(context, resp_json["info"])
                        return
                    keywords: List[dict] = resp_json["data"]
                print("keywords =", keywords)
                with client.post("http://jiuge.thunlp.cn/sendPoem", data={
                    "style": style,
                    "genre": genre,
                    "yan": yan,
                    "user_id": user_id,
                    "keywords": json.JSONEncoder().encode(keywords)
                }) as urlf:
                    resp_json = urlf.json()
                    print("send response =", resp_json)
                    resp_json["code"] = str(resp_json["code"])
                    if resp_json["code"] == "mgc":
                        bot.send(context, f"主题 {keyword} 无法作诗")
                        return
                    elif resp_json["code"] == "777":
                        bot.send(context, f"九歌服务器出错")
                        return
                    elif resp_json["code"] != '0':
                        bot.send(context, resp_json["info"])
                        return
                while True:
                    with client.post("http://jiuge.thunlp.cn/getPoem", data={
                        "style": style,
                        "genre": genre,
                        "yan": yan,
                        "user_id": user_id,
                        "keywords": json.JSONEncoder().encode(keywords)
                    }) as urlf:
                        resp_json = urlf.json()
                        resp_json["code"] = str(resp_json["code"])
                        if resp_json["code"] == "mgc":
                            bot.send(context, f"主题 {keyword} 无法作诗")
                            return
                        elif resp_json["code"] == "1":
                            continue
                        if resp_json["code"] not in {"1", "0", "666"}:
                            bot.send(context, "九歌服务器错误")
                            return
                        generate_result = resp_json
                        break

                    time.sleep(0.8)
                from io import StringIO
                buf = StringIO()
                buf.write(f"{user_id} 生成完成\n")
                result_data = generate_result["data"]
                if "scores" in result_data:
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
                print(generate_result)
                if image:
                    with requests.post("http://jiuge.thunlp.cn/share", data={
                        "style": style,
                        "genre": genre,
                        "yan": yan,
                        "keywords": keyword,
                        "user_id": user_id,
                        "lk": "",
                        "user_poem": json.JSONEncoder().encode(result_data["poem"])
                    }) as urlf:
                        print(urlf.text)
                        image_file = urlf.json()["data"]
                        buf.write(
                            f"http://47.52.252.160/pic_share/{image_file}")
                        buf.write(
                            f"[CQ:image,file=http://jiuge.thunlp.cn/share/new/{image_file}]")

                bot.send(context, buf.getvalue())
            except Exception as ex:
                # import traceback
                bot.send(context, str(ex))
                raise ex

        handle_thread = threading.Thread(target=handle)
        handle_thread.start()
        while time.time()-begin_time < config.TIME_LIMIT and handle_thread.is_alive():
            time.sleep(0.1)
        if handle_thread.is_alive():
            stop_thread(handle_thread)
            bot.send(context, f"{user_id}生成超时")
    threading.Thread(target=time_monitor).start()
