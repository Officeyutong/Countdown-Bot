from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import GroupMessageEvent
import aiohttp
import requests
import bs4
from typing import List


class HitokotoConfig(ConfigBase):
    # 一言广播(小时)
    HITOKOTO_HOUR = 6
    # 分钟
    HITOKOTO_MINUTE = 30
    USING_URL_LIST = True
    # 启用HITOKOTO的群
    # list 或者URL的文本
    HITOKOTO_BROADCAST_LIST = "https://gitee.com/ZhehaoMi/countdown/raw/master/hitokoto.json"
    HITOKOTO_BROADCAST_LOCAL_LIST = [
        # "群号"
    ]


class HitokotoPlugin(Plugin):
    def generate_hitokoto_message(self, text: str, source: str, id: str) -> str:
        return f"""{text}
            
--- {source}
    
(Hitokoto ID:{id} https://hitokoto.cn/?id={id})"""

    async def fetch_hitokoto_by_id(self, id: str) -> str:
        async with self.aioclient.get("https://hitokoto.cn", params={"id": id}) as resp:
            soup = bs4.BeautifulSoup(await resp.text(), "lxml")
        return self.generate_hitokoto_message(
            text=soup.select_one("#hitokoto_text").get_text(),
            source=soup.select_one("#hitokoto_author").get_text(),
            id=id
        )

    async def fetch_random_hitokoto(self) -> str:
        async with self.aioclient.get("https://v1.hitokoto.cn/") as resp:
            data = await resp.json()
        return self.generate_hitokoto_message(
            text=data["hitokoto"],
            source=data["from"],
            id=data['id']
        )

    def command_hitokoto(self, plugin, args: List[str], raw_string: str, context, evt: GroupMessageEvent):
        async def wrapper():
            if len(args) == 0:
                self.bot.client_async.send(context, await self.fetch_random_hitokoto())
            else:
                self.bot.client_async.send(context, await self.fetch_hitokoto_by_id(args[0]))
        self.bot.submit_async_task(wrapper())

    async def schedule_loop(self):
        if self.config.USING_URL_LIST:
            async with self.aioclient.get(self.config.HITOKOTO_BROADCAST_LIST) as resp:
                broadcast_list = await resp.json()
        else:
            broadcast_list = self.config.HITOKOTO_BROADCAST_LOCAL_LIST
        for group in broadcast_list:
            try:
                self.bot.client_async.send_group_msg(group_id=int(group), message=await self.fetch_random_hitokoto())
            except:
                import traceback
                traceback.print_exc()

    def on_enable(self):
        self.aioclient = aiohttp.ClientSession()
        self.bot: CountdownBot
        self.config: HitokotoConfig
        self.register_command_wrapped(
            command_name="hitokoto",
            command_handler=self.command_hitokoto,
            help_string="查询一言 | hitokoto - 随机 | hitokoto [ID] 指定ID查询",
            chats={ChatType.discuss, ChatType.group, ChatType.private},
        )
        self.register_schedule_loop(
            time=TimeTuple(hour=self.config.HITOKOTO_HOUR,
                           minute=self.config.HITOKOTO_MINUTE),
            coro=self.schedule_loop(),
            name="Hitokoto定时广播"
        )
        self.register_state_handler(
            lambda: f"Hitokoto广播时间: {self.config.HITOKOTO_HOUR}:{self.config.HITOKOTO_MINUTE}")


def get_plugin_class():
    return HitokotoPlugin


def get_config_class():
    return HitokotoConfig


def get_plugin_meta():
    return PluginMeta(
        "officeyutong", 2.0, "一言广播 & 查询"
    )
