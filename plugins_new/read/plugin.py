from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import MessageEvent
from typing import List

import urllib
import base64
import aiohttp
import json


class ReadConfig(ConfigBase):
    MAX_STRING_LENGTH = 300

    # Baidu AI Apps
    APP_ID = ""
    API_KEY = ""
    SECRET_KEY = ""

    # Volume 1(low)-10(high)
    VOLUME = 8
    # Speech rate 1(slow)-10(quick)
    SPEED = 4


class ReadPlugin(Plugin):
    async def get_voice(self, text: str, token: str) -> bytes:
        async with self.aioclient.post("https://tsn.baidu.com/text2audio", data={
            "tex": urllib.parse.quote(text),
            "tok": token,
            "cuid": "qwqqwqqwq",
            "ctp": 1,
            "spd": self.config.SPEED,
            "per": 4,
            "vol": self.config.VOLUME,
            "lan": "zh"
        }) as resp:
            resp: aiohttp.ClientResponse
            result = await resp.read()
        return result

    async def get_token(self) -> str:
        async with self.aioclient.get("https://openapi.baidu.com/oauth/2.0/token", params={
            "grant_type": "client_credentials",
            "client_id": self.config.API_KEY,
            "client_secret": self.config.SECRET_KEY
        }) as resp:
            resp: aiohttp.ClientResponse
            result = await resp.json()
        return result['access_token']

    async def command_read(self, plugin, args: List[str], raw_string: str, context, evt: MessageEvent):
        text = " ".join(args)
        if len(text) > self.config.MAX_STRING_LENGTH:
            await self.bot.client_async.send(context, "字符串过长")
        else:
            try:
                token = await self.get_token()
            except Exception:
                self.logger.error("Read: 获取token失败,请检查API_KEY和SECRET_KEY")
                return
            data = await self.get_voice(text, token)
            try:
                info = json.loads(data.decode())
            except Exception:
                b64voice = base64.encodebytes(data).decode().replace('\n', '')
                await self.bot.client_async.send(
                    context, f"[CQ:record,file=base64://{b64voice}]")
                return
            await self.bot.client_async.send(context, f"Error: {info}")

    def on_enable(self):
        self.aioclient = aiohttp.ClientSession()
        self.config: ReadConfig
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="read",
            command_handler=self.command_read,
            help_string="文字转语音",
            chats={ChatType.discuss, ChatType.group, ChatType.private},
            is_async=True
        )


def get_plugin_class():
    return ReadPlugin


def get_config_class():
    return ReadConfig


def get_plugin_meta():
    return PluginMeta(
        "Antares", 3.0, "文字转语音"
    )
