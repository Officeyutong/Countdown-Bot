from common.plugin import Plugin
from common.countdown_bot import CountdownBot
from common.datatypes import PluginMeta
from common.event import MessageEvent
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
    WHITE_LIST_GROUPS = ["123456"]


class CatsPlugin(Plugin):
    def list_cats(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        from io import StringIO
        buf = StringIO()
        cursor = self.conn.cursor()
        if not args:
            buf.write("上传过猫片的用户:\n")
            for user_id in cursor.execute("SELECT DISTINCE USER_ID FROM CATS"):
                buf.write(f"{user_id[0]} ")
        else:
            buf.write(f"用户 {args[0]} 所上传的猫片")
            for image_id in cursor.execute("SELECT ID FROM CATS WHERE USER_ID = ?", (int(args[0]),)):
                buf.write(f"{image_id[0]} ")
        self.bot.client.send(context, buf.getvalue())

    def __reload_cache(self):
        cursor = self.conn.cursor()
        id_cache = []
        for image_id in cursor.execute("SELECT ID FROM CATS"):
            id_cache.append(image_id[0])
        self.__id_cache = id_cache

    def get_cat_image(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        cursor = self.conn.cursor()
        ids = [x[0] for x in cursor.execute("SELECT ID FROM CATS ")]
        selected = random.choice(ids)
        image = cursor.execute(
            "SELECT ID,USER_ID,UPLOAD_TIME,DATA FROM CATS WHERE ID = ?", (selected,))[0]
        upload_time: time.struct_time = time.localtime(image[2])
        b64_encoded = base64.encodebytes(image[3]).decode().replace("\n", "")
        self.bot.client_async.send(
            f"来自 {image[1]} 的猫片 {image[0]} (上传于 {upload_time.tm_year}年 {upload_time.tm_mon}月 {upload_time.tm_mday}日)\n[CQ:image,file=base64://{b64_encoded}]")
    # def 
    def on_enable(self):
        self.bot: CountdownBot
        self.conn = self.bot.db_conn
        cursor = self.conn.cursor()
        cursor.execute("""CREATE TABLE CATS IF NOT EXISTS(
            ID INTEGER PRIMARY KEY,
            USER_ID INTEGER NOT NULL,
            UPLOAD_TIME INTEGER,
            DATA BLOB NOT NULL
        )""")
        self.conn.commit()


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
