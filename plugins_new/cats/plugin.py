from common.plugin import Plugin
from common.countdown_bot import CountdownBot
from common.datatypes import PluginMeta
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.config_loader import ConfigBase
from typing import List, Dict
import re
import aiohttp
import io
import bs4
import ujson
import time
import datetime
import random
import time
import base64


class CatsConfig(ConfigBase):
    IMAGE_SIZE_LIMIT = 8*1024*1024
    WHITE_LIST_GROUPS = [123456]


class CatsPlugin(Plugin):
    def list_cats(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        from io import StringIO
        buf = StringIO()
        if not args:
            buf.write("上传过猫片的用户:\n")
            for user_id in self.conn.execute("SELECT DISTINCT USER_ID FROM CATS"):
                buf.write(f"{user_id[0]}  ")
        else:
            buf.write(f"用户 {args[0]} 所上传的猫片:\n")
            for image_id in self.conn.execute("SELECT ID FROM CATS WHERE USER_ID = ?", (int(args[0]),)):
                buf.write(f"{image_id[0]} ")
        self.bot.client.send(context, buf.getvalue())

    def __reload_cache(self):
        id_cache = []
        for image_id in self.conn.execute("SELECT ID FROM CATS"):
            id_cache.append(image_id[0])
        self.__id_cache = id_cache

    def get_cat_image(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        ids = [x[0] for x in self.conn.execute("SELECT ID FROM CATS ")]
        if not ids:
            self.bot.client.send(context, "当前无人上传过猫片!")
            return
        selected = random.choice(ids)
        if args:
            selected = int(args[0])
        image = self.conn.execute(
            "SELECT ID,USER_ID,UPLOAD_TIME,DATA FROM CATS WHERE ID = ?", (selected,)).fetchone()
        if not image:
            self.bot.client.send(context, "猫片ID不存在")
            return
        upload_time: time.struct_time = time.localtime(image[2])
        b64_encoded = base64.encodebytes(image[3]).decode().replace("\n", "")
        self.bot.client_async.send(context,
                                   f"来自 {image[1]} 的猫片 {image[0]} (上传于 {upload_time.tm_year}年 {upload_time.tm_mon}月 {upload_time.tm_mday}日)\n[CQ:image,file=base64://{b64_encoded}]")

    def upload_cat_image(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        if evt.group_id not in self.config.WHITE_LIST_GROUPS:
            self.bot.client.send(context, "本群不被允许上传")
            return
        self.bot.logger.debug(args)
        if not args:
            self.bot.client.send(context, "请上传图片")
            return
        search_result = self.upload_pattern.search(args[0])
        if not search_result:
            self.bot.client.send(context, "请上传图片")
            return
        url = search_result.group("url")

        async def wrapper():
            await self.bot.client_async.send(context, "开始保存猫猫图片..")
            async with self.client.get(url) as resp:
                resp: aiohttp.ClientResponse
                image_data = await resp.read()
            ret = self.conn.execute("INSERT INTO CATS (USER_ID,UPLOAD_TIME,DATA) VALUES (?,?,?)", (
                evt.sender.user_id,
                int(time.time()),
                image_data
            ))
            self.conn.commit()
            await self.bot.client_async.send(context, f"{evt.sender.user_id} 的猫猫图片 {ret.lastrowid} 上传成功")
        self.bot.submit_async_task(wrapper())

    def on_enable(self):
        self.bot: CountdownBot
        self.config: CatsConfig
        self.conn = self.bot.db_conn
        self.client = aiohttp.ClientSession()
        self.upload_pattern = re.compile(
            r"\[CQ:image.+url\=(?P<url>[^\[^\]]+)\]")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS CATS(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USER_ID INTEGER NOT NULL,
            UPLOAD_TIME INTEGER,
            DATA BLOB NOT NULL
        )""")
        self.conn.commit()
        self.register_command_wrapped(
            command_name="吸猫",
            command_handler=self.get_cat_image,
            help_string="吸猫 | 吸猫 [猫片ID(可选)]",
            chats={ChatType.group},
            alias=["cat"],
        )
        self.register_command_wrapped(
            command_name="upload",
            command_handler=self.upload_cat_image,
            help_string="上传猫片 | upload [图片]",
            chats={ChatType.group},
        )
        self.register_command_wrapped(
            command_name="list-cats",
            command_handler=self.list_cats,
            help_string="查看上传过猫片的用户列表 | 查询某个用户上传的猫片 list-cats [QQ]",
            chats=ChatType.all(),
        )


def get_plugin_class():
    return CatsPlugin


def get_config_class():
    return CatsConfig


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="吸猫插件"
    )
