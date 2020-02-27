from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import MessageEvent
from typing import Dict, List
import aiohttp

class Music163Config(ConfigBase):
    # https://github.com/Binaryify/NeteaseCloudMusicApi
    API_URL = "http://localhost:3000"
    SEARCH_LIMIT = 10
    LOGIN_MODE = "phone"  # "phone" or "email" 其他则不登录
    PHONE = ""
    EMAIL = ""
    PASSWORD = ""


class Music163Plugin(Plugin):

    async def login(self) -> bool:
        if self.config.LOGIN_MODE == "phone":
            async with self.aioclient.get(f"{self.config.API_URL}/login/cellphone", params={
                "phone": self.config.PHONE,
                "password": self.config.PASSWORD
            }) as resp:
                result = await resp.json()
            return result["code"] == 200
        elif self.config.LOGIN_MODE == "email":
            async with self.aioclient.get(f"{self.config.API_URL}/login", params={
                "email": self.config.EMAIL,
                "password": self.config.PASSWORD
            }) as resp:
                result = await resp.json()
            return result["code"] == 200
        else:
            return False

    async def check_login_status(self) -> bool:
        if self.config.LOGIN_MODE != "phone" and self.config.LOGIN_MODE != "email":
            return True
        async with self.aioclient.get(f"{self.config.API_URL}/login/refresh") as resp:
            result = await resp.json()
        return result["code"] == 200

    async def check_music_available(self, music_id: int) -> bool:
        async with self.aioclient.get(f"{self.config.API_URL}/check/music", params={"id": music_id}) as resp:
            result = await resp.json()
        return result["success"]

    async def get_music_url(self, music_id: int) -> str:
        async with self.aioclient.get(f"{self.config.API_URL}/song/url", params={
            "id": music_id,
            "br": 320000
        }) as resp:
            result = await resp.json()
        return result['data'][0]['url']

    async def search_music(self, key_words: str) -> List[dict]:
        async with self.aioclient.get(f"{self.config.API_URL}/search", params={
            "keywords": key_words,
            "limit": self.config.SEARCH_LIMIT
        }) as resp:
            result = await resp.json()
        if result["code"] != 200 or result["result"]["songCount"] == 0:
            return []
        else:
            return result["result"]["songs"]

    async def command_music(self, plugin, args: List[str], raw_string: str, context, evt: MessageEvent):
        if len(args) == 0:
            await self.bot.client_async.send(context, "输入不合法")
            return
        
        raw = False
        link = False
        if args[-1] == "raw":
            raw = True
            del args[-1]
        elif args[-1] == "link":
            link = True
            del args[-1]

        if len(args) == 0:
            await self.bot.client_async.send(context, "输入不合法")
            return

        if not await self.check_login_status():
            if not await self.login():
                await self.bot.client_async.send(context, "网易云账号登陆失败, 请检查账号密码！")
            elif not await self.check_login_status():
                await self.bot.client_async.send(context, "网易云账号登陆失败！")

        if args[0] == "id":
            try:
                query_id = int(args[1])
            except ValueError:
                await self.bot.client_async.send(context, "请输入正确的id")
                return

            if not await self.check_music_available(query_id):
                await self.bot.client_async.send(context, "id对应的音乐不存在或无版权")
                return

            if raw:
                await self.bot.client_async.send(context, f"[CQ:music,type=163,id={query_id}]")
            else:
                music_url = await self.get_music_url(query_id)
                if not music_url:
                    await self.bot.client_async.send(context, "无法取得音乐链接，请检查是否为VIP歌曲")
                    return
                if link:
                    await self.bot.client_async.send(context, music_url)
                else:
                    await self.bot.client_async.send(context, f"[CQ:record,file={music_url}]")
            return

        key_words = " ".join(args)
        musics_list = await self.search_music(key_words)

        for music in musics_list:
            music_id = music['id']
            if await self.check_music_available(music_id):
                if raw:
                    await self.bot.client_async.send(
                        context, f"[CQ:music,type=163,id={music_id}]")
                else:
                    music_url = await self.get_music_url(music_id)
                    if not music_url:
                        continue
                    if link:
                        await self.bot.client_async.send(context, music_url)
                    else:
                        await self.bot.client_async.send(context, f"[CQ:record,file={music_url}]")
                return

        await self.bot.client_async.send(context, "您搜索的歌曲可能不存在、无版权或为VIP歌曲")

    def on_enable(self):
        self.aioclient = aiohttp.ClientSession()
        self.bot: CountdownBot
        self.config: Music163Config
        self.register_command_wrapped(
            command_name="music",
            command_handler=self.command_music,
            help_string="网易云音乐查询 | music [歌名] [raw/link](可选) | music id [歌曲id] [raw/link](可选)",
            chats=ChatType.all(),
            is_async=True
        )


def get_plugin_class():
    return Music163Plugin


def get_config_class():
    return Music163Config


def get_plugin_meta():
    return PluginMeta(
        "Antares", 2.0, "网易云音乐推歌"
    )
