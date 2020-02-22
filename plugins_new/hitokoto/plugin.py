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


class HitokotoConfig(ConfigBase):
    # 一言广播(小时)
    HITOKOTO_HOUR = 6
    # 分钟
    HITOKOTO_MINUTE = 30
    # 启用HITOKOTO的群
    # list 或者URL的文本
    HITOKOTO_BROADCAST_LIST = "https://gitee.com/ZhehaoMi/countdown/raw/master/hitokoto.json"


class HitokotoPlugin(Plugin):
    pass


def get_plugin_class():
    return HitokotoPlugin


def get_config_class():
    return HitokotoConfig


def get_plugin_meta():
    return PluginMeta(
        "hitokoto", 2.0, "一言广播 & 查询"
    )
