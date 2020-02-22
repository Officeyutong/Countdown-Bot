from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import GroupMessageEvent
import aiohttp
import requests
from typing import List


class BroadcastConfig(ConfigBase):
    BROADCAST_HOUR: int = 6
    BROADCAST_MINUTE = 0
    USING_URL_LIST = True  # 为True时使用LIST_URL，否则使用LIST
    LIST_URL = "https://gitee.com/ZhehaoMi/countdown/raw/master/countdown.json"
    LIST = {}
    # LIST = {
    #     "群号": [
    #         {
    #             "name": "广播名",
    #             "date": "年-月-日"
    #         }
    #     ]
    # }


class BroadcastPlugin(Plugin):
    def get_broadcast_content(self, broadcast_list: List[dict]) -> List[str]:
        # print_log("broadcasting..")
        result: List[str] = []
        countdown_list = broadcast_list
        from datetime import datetime
        from datetime import timedelta
        today = datetime.now()
        for item in countdown_list:
            self.bot.logger.info(item)
            name = item["name"]
            exp_time = datetime.strptime(item["date"], "%Y-%m-%d")
            delta: timedelta = exp_time-today+timedelta(days=1)
            # days=delta.days+1
            mouths = delta.days//30
            days = delta.days % 30
            if delta.days < 0:
                continue
            if delta.days > 0:
                if mouths > 0:
                    text = f'距离 {name} 还有 {delta.days} 天 ({mouths}个月{f"{days}天"  if days != 0 else "整"}).'
                else:
                    text = f"距离 {name} 还有 {delta.days} 天."
            else:
                text = f"今天是 {name} ."
            self.bot.logger.info(text)
            result.append(text)
        return result

    def broadcast_at_group(self, group: str, broadcasts: List[dict]):
        for item in self.get_broadcast_content(broadcasts):
            try:
                self.bot.send_group_msg(group_id=group, message=item)
            except:
                import traceback
                traceback.print_exc()

    async def schedule_loop(self):
        if self.config.USING_URL_LIST:
            async with aiohttp.ClientSession() as client:
                async with client.get(self.config.USING_URL_LIST) as resp:
                    data = await resp.json()
        else:
            data = self.config.LIST
        for group, broadcast_data in data.items():
            self.broadcast_at_group(group, broadcast_data)

    def command_broadcast(self, plugin, args: List[str], raw_string: str, context, evt: GroupMessageEvent):
        group = str(evt.group_id)
        if self.config.USING_URL_LIST:
            with self.client.get(self.config.LIST_URL) as resp:
                data = resp.json()
        else:
            data = self.config.LIST
        if group in data:
            self.broadcast_at_group(group, data[group])
        else:
            self.bot.send(context, "当前群不存在广播数据")

    def on_enable(self):
        self.config: BroadcastConfig
        self.bot: CountdownBot
        self.register_state_handler(
            lambda: f"广播时间: {self.config.BROADCAST_HOUR}:{self.config.BROADCAST_MINUTE}"
        )
        self.client = requests.session()
        self.register_schedule_loop(
            TimeTuple(self.config.BROADCAST_HOUR,
                      self.config.BROADCAST_MINUTE),
            self.schedule_loop(),
            "定时群倒计时广播"
        )
        self.register_command_wrapped(
            command_name="broadcast",
            command_handler=self.command_broadcast,
            help_string="在当前群进行广播",
            chats={ChatType.group},
            alias=["广播"]
        )


def get_plugin_class():
    return BroadcastPlugin


def get_config_class():
    return BroadcastConfig


def get_plugin_meta():
    return PluginMeta(
        "broadcast", 2.0, "群广播"
    )
