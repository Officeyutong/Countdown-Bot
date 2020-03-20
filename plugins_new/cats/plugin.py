from common.plugin import Plugin
from common.countdown_bot import CountdownBot
from common.datatypes import PluginMeta
from common.event import MessageEvent, GroupMessageEvent, PrivateMessageEvent
from common.command import ChatType
from common.config_loader import ConfigBase
from typing import List, Dict, Tuple
from dataclasses import dataclass
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
import sqlite3
import time
import hashlib
import hmac
import ujson

from .tencent_cloud import make_header


class CatsConfig(ConfigBase):
    IMAGE_SIZE_LIMIT = 8*1024*1024
    WHITE_LIST_GROUPS: List[int] = []
    WHITE_LIST_USERS: List[int] = []
    SECRET_ID: str = ""
    SECRET_KEY: str = ""
    # 是否使用腾讯云AI识别猫片，若不启用则只能在白名单群里上传
    USE_TENCENT_CLOUD = False
    # 非白名单群用户尝试上传猫片的间隔(s)
    TRY_DELAY = 60
    # 非白名单群用户成功上传的间隔(s)
    SUCCESS_DELAY = 60*60


@dataclass
class RecognizeResult:
    ok: bool
    message: str


class CatsPlugin(Plugin):

    async def recognize_cat_image(self, imgdata: bytes) -> RecognizeResult:
        timestamp = int(time.time())
        params = {
            "ImageBase64": base64.encodebytes(imgdata).decode().replace("\n", ""),
            "Scenes": ["ALBUM"]
        }
        payload = ujson.dumps(params)
        headers = make_header(payload, timestamp,
                              self.config.SECRET_ID, self.config.SECRET_KEY)
        async with self.client.post("https://tiia.tencentcloudapi.com", headers=headers, data=payload.encode()) as resp:
            json_resp = (await resp.json())["Response"]
            self.logger.info(json_resp)
            if "Error" in json_resp:
                return RecognizeResult(False, json_resp["Error"]["Message"])
            if not json_resp["AlbumLabels"]:
                return RecognizeResult(False, "未识别到猫")
            for label in json_resp["AlbumLabels"]:
                if label["Name"] == "猫" and label["Confidence"] >= 30:
                    return RecognizeResult(True, "识别成功")

        return RecognizeResult(False, "未识别到猫")

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

    def delete_cat_image(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        if not args:
            self.bot.client.send(context, "请输入猫片ID")
            return
        line = self.conn.execute(
            "SELECT ID,USER_ID,UPLOAD_TIME,DATA FROM CATS WHERE ID = ?", (int(args[0]),)).fetchone()
        if not line:
            self.bot.client.send(context, "猫片不存在")
            return
        if line[1] != evt.sender.user_id:
            self.bot.client.send(context, "您只能删除自己上传的猫片")
            return
        self.conn.execute("DELETE FROM CATS WHERE ID = ?", (line[0],))
        self.conn.commit()
        self.bot.client.send(context, "删除完成")

    def get_cat_image(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):

        if not self.conn.execute("SELECT COUNT(*) FROM CATS"):
            self.bot.client.send(context, "当前无人上传过猫片!")
            return
        _args = {
            "qq": None,
            "id": -1
        }
        for x in args:
            a, *b = x.split(":")
            self.logger.debug(a)
            self.logger.debug(b)
            if a in _args and b:
                _args[a] = b[0]
        self.logger.info(_args)
        args = _args
        if args["qq"]:
            ids = [x[0] for x in self.conn.execute(
                "SELECT ID FROM CATS WHERE USER_ID = ? ", (int(args["qq"]),))]
        elif args["id"] != -1:
            ids = [int(args["id"])]
        else:
            ids = [x[0] for x in self.conn.execute("SELECT ID FROM CATS")]
        if not ids:
            self.bot.client.send(context, "猫片不存在")
            return

        image = self.conn.execute(
            "SELECT ID,USER_ID,UPLOAD_TIME,DATA FROM CATS WHERE ID = ?", (random.choice(ids),)).fetchone()
        if not image:
            self.bot.client.send(context, "猫片不存在")
            return
        upload_time: time.struct_time = time.localtime(image[2])
        b64_encoded = base64.encodebytes(image[3]).decode().replace("\n", "")
        self.bot.client_async.send(context,
                                   f"来自 {image[1]} 的猫片 {image[0]} (上传于 {upload_time.tm_year}年 {upload_time.tm_mon}月 {upload_time.tm_mday}日)\n[CQ:image,file=base64://{b64_encoded}]")

    async def upload_cat_image(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        import time
        import hashlib
        need_check = False
        if isinstance(evt, PrivateMessageEvent):
            if not self.config.USE_TENCENT_CLOUD:
                await self.bot.client_async.send(context, "不允许私聊上传")
                return
            else:
                need_check = True

        elif isinstance(evt, GroupMessageEvent):
            if evt.group_id in self.config.WHITE_LIST_GROUPS:
                pass
            else:
                if not self.config.USE_TENCENT_CLOUD:
                    await self.bot.client_async.send(context, "本群不被允许上传")
                    return
                else:
                    need_check = True
        else:
            await self.bot.client_async.send(context, "暂不支持")
            return
        self.bot.logger.debug(args)
        if not args:
            await self.bot.client_async.send(context, "请上传图片")
            return
        search_result = self.upload_pattern.search(args[0])
        if not search_result:
            await self.bot.client_async.send(context, "请上传图片")
            return
        url = search_result.group("url")
        if evt.user_id in self.config.WHITE_LIST_USERS:
            need_check = False
        if need_check:

            if time.time()-self.last_upload.get(evt.user_id, 0) < self.config.TRY_DELAY:
                await self.bot.client_async.send(context, f"你在 {self.config.TRY_DELAY}s 内只能进行一次尝试")
                return
            else:
                self.last_upload[evt.user_id] = time.time()

        await self.bot.client_async.send(context, "开始保存猫猫图片..")
        async with self.client.get(url) as resp:
            resp: aiohttp.ClientResponse
            image_data = await resp.read()
            if len(image_data) > self.config.IMAGE_SIZE_LIMIT:
                await self.bot.client_async.send(context, "图片过大")
                return
        if need_check:
            check_result = await self.recognize_cat_image(image_data)
            if not check_result.ok:
                await self.bot.client_async.send(context, "上传失败!\n"+check_result.message)
                return
            last_upload = self.conn.execute(
                "SELECT UPLOAD_TIME FROM CATS WHERE USER_ID=?", [evt.user_id]).fetchone()
            if last_upload and time.time()-last_upload[0] < self.config.SUCCESS_DELAY:
                await self.bot.client_async.send(context, f"你在 {self.config.SUCCESS_DELAY}s 内只能上传成功一次")
                return
        md5 = hashlib.md5()
        md5.update(image_data)
        if self.conn.execute(
                "SELECT CHECKSUM FROM CATS WHERE CHECKSUM=?", [md5.hexdigest()]).fetchone():
            await self.bot.client_async.send(context, "你之前曾上传过相同的猫片!")
            return

        ret = self.conn.execute("INSERT INTO CATS (USER_ID,UPLOAD_TIME,DATA,CHECKSUM) VALUES (?,?,?,?)", (
            evt.sender.user_id,
            int(time.time()),
            image_data,
            md5.hexdigest()
        ))
        self.conn.commit()
        await self.bot.client_async.send(context, f"{evt.sender.user_id} 的猫猫图片 {ret.lastrowid} 上传成功")

    def on_disable(self):
        self.logger.info(f"Cats: closing database..")
        self.conn.close()

    def on_enable(self):
        self.bot: CountdownBot
        self.config: CatsConfig
        self.conn = sqlite3.connect(
            self.plugin_base_dir/"cats.db", check_same_thread=False)
        self.client = aiohttp.ClientSession()
        self.upload_pattern = re.compile(
            r"\[CQ:image.+url\=(?P<url>[^\[^\]]+)\]")

        try:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS CATS(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                USER_ID INTEGER NOT NULL,
                UPLOAD_TIME INTEGER,
                DATA BLOB NOT NULL,
                CHECKSUM TEXT NOT NULL UNIQUE
            )""")
            self.conn.execute("CREATE INDEX ID_INDEX ON CATS(ID)")
            self.conn.execute("CREATE INDEX USER_ID_INDEX ON CATS(USER_ID)")
            self.conn.execute("CREATE INDEX INDEX_CHECKSUM ON CATS(CHECKSUM)")
            self.conn.commit()
        except Exception as ex:
            self.logger.error(ex)

        self.register_command_wrapped(
            command_name="吸猫",
            command_handler=self.get_cat_image,
            help_string="吸猫 | 吸猫 [qq:上传者ID(可选)] [id:图片ID(可选)]",
            chats=ChatType.all(),
            alias=["cat"],
        )
        self.register_command_wrapped(
            command_name="upload",
            command_handler=self.upload_cat_image,
            help_string="上传猫片 | upload [图片]",
            chats=ChatType.all(),
            is_async=True
        )
        self.register_command_wrapped(
            command_name="list-cats",
            command_handler=self.list_cats,
            help_string="查看上传过猫片的用户列表 | 查询某个用户上传的猫片 list-cats [QQ]",
            chats=ChatType.all(),
        )
        self.register_command_wrapped(
            command_name="delete-cat",
            command_handler=self.delete_cat_image,
            help_string="删除猫片 | delete-cat [id]",
            chats=ChatType.all(),
        )
        self.last_upload: Dict[int, float] = dict()


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
