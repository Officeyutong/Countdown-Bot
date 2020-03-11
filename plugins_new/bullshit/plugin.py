from common.datatypes import PluginMeta
from common.plugin import Plugin
from common.event import MessageEvent
from common.countdown_bot import CountdownBot
from common.command import ChatType
from typing import List
import jieba
import random


class BullshitPlugin(Plugin):

    def on_enable(self):
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="shit",
            command_handler=self.shit,
            help_string="将输入字符串分词后随机打乱 | shit [字符串]",
            chats={ChatType.discuss, ChatType.group, ChatType.private}
        )
        self.register_command_wrapped(
            command_name="bullshit",
            command_handler=self.bullshit,
            help_string="狗屁不通文章生成 | bullshit [关键词]",
            chats={ChatType.discuss, ChatType.group, ChatType.private}
        )

    def shit(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        string = " ".join(args)[:500]
        items = list(jieba.cut(string))
        # print(items)
        random.shuffle(items)
        self.bot.client.send(context, "".join((x.strip()
                                          for x in items if x.strip())))

    def bullshit(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):

        if not args:
            self.bot.client.send(context, "请输入主题")
            return
        theme = " ".join(args)
        self.bot.client.send(context, self.generate_bullshit(theme))

    def generate_bullshit(self, 主题: str):
        import math
        import random
        from .data import 初始主题, 前面垫话, 名人名言, 后面垫话, 论述
        下取整 = math.floor
        同余乘数 = 214013
        同余加数 = 2531011
        同余模 = 2**32
        随机种子 = random.randint(10**7, 10**8)

        def 同余发生器():
            nonlocal 随机种子
            随机种子 = (随机种子 * 同余乘数 + 同余加数) % 同余模
            return 随机种子 / 同余模

        def 随便取一句(列表: List[str]):
            坐标 = 下取整(同余发生器() * len(列表))
            return 列表[坐标]

        def 随便取一个数(最小值=0, 最大值=100, 随机数函数=同余发生器):
            数字 = 随机数函数() * (最大值 - 最小值) + 最小值
            return 数字

        def 来点名人名言():
            名言 = 随便取一句(名人名言)
            名言 = 名言.replace('曾经说过', 随便取一句(前面垫话))
            名言 = 名言.replace('这不禁令我深思', 随便取一句(后面垫话))
            return 名言

        def 来点论述():
            句子 = 随便取一句(论述)
            句子 = 句子.replace("主题", 主题)
            return 句子

        def 增加段落(段落):
            if 段落[-1] == ' ':
                段落 = 段落[0:-2]
            return '　　' + 段落 + '。 '

        文章 = []
        段落 = ''
        文章长度 = 0
        while 文章长度 < 340:
            随机数 = 随便取一个数()
            if 随机数 < 5 and len(段落) > 200:
                段落 = 增加段落(段落)
                文章.append(段落)
                段落 = ''
            elif 随机数 < 20:
                句子 = 来点名人名言()
                文章长度 = 文章长度 + len(句子)
                段落 = 段落 + 句子
            else:
                句子 = 来点论述()
                文章长度 = 文章长度 + len(句子)
                段落 = 段落 + 句子
        段落 = 增加段落(段落)
        文章.append(段落)
        return "".join(文章)

# print(generate_bullshit("test"))


def get_plugin_class():
    return BullshitPlugin


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="狗屁不通文章生成器"
    )
