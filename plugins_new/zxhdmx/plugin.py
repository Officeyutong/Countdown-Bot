from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import MessageEvent, GroupMessageEvent
from typing import Set, Dict, List
from .game import Game
import json
import flask
HELP_STR =\
    """开始 ---- 开始本群游戏
拼点 ---- 参与拼点
接受 ---- 接受处罚
状态 ---- 查看游戏状态
帮助 ---- 查看帮助
提醒 ---- 提醒未拼点玩家参与拼点
跳过 ---- 跳过未拼点玩家
终止 ---- 强行终止当前游戏 **在并非有人咕掉游戏的情况下使用本指令可能会招致部分玩家的极度反感(比如开发者)**
选择 [题库] ---- 选择惩罚题库 
使用物品 [ID] [参数] ---- 使用物品
查看物品 ---- 查看物品列表"""


class ZxhDmxConfig(ConfigBase):
    # 启用的群号
    ENABLE_GROUPS = [
        # 123456,
    ]
    # 管理员密码
    ADMIN_PASSWORD = "qwqqwqqwq"
    # 开始所需最少玩家数
    MIN_REQUIRED_PLAYERS = 2


def get_plugin_class():
    return ZxhDmxPlugin


def get_config_class():
    return ZxhDmxConfig


def get_plugin_meta():
    return PluginMeta(
        "officeyutong", 2.0, "真心话大冒险"
    )


def get_md5(text: str) -> str:
    import hashlib
    ins = hashlib.md5()
    ins.update(text.encode("utf-8"))
    return ins.hexdigest()


class ZxhDmxPlugin(Plugin):

    def load_data(self):
        with open(self.plugin_base_dir/"data.json", "r") as file:
            return json.loads(file.read())

    def save_data(self, obj):
        with open(self.plugin_base_dir/"data.json", "w") as file:
            return file.write(json.dumps(obj))

    def web_get_data(self):
        dat = flask.request.form
        if dat.get("password", None).lower() != get_md5(get_md5(self.config.ADMIN_PASSWORD)+"qwqqwqqwq"):
            return json.dumps({
                "code": -1, "message": "密码错误"
            })
        return json.dumps({
            "code": 0, "data": self.load_data()
        })

    def web_set_data(self):
        dat = flask.request.form
        if dat.get("password", None).lower() != get_md5(get_md5(self.config.ADMIN_PASSWORD)+"qwqqwqqwq"):
            return json.dumps({
                "code": -1, "message": "密码错误"
            })
        self.save_data(json.loads(dat["data"]))
        return json.dumps({
            "code": 0, "message": "操作成功"
        })

    def web_edit(self):
        self.bot.logger.info("Loading webpage..")
        self.bot.logger.info(str(self.plugin_base_dir/"web"))
        return flask.send_from_directory(str(self.plugin_base_dir/"web"), "edit.html")

    def command_zxh(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        if evt.group_id not in self.config.ENABLE_GROUPS:
            self.bot.client.send(context, "本群未启用本功能！")
            return
        user_id = evt.sender.user_id
        group = evt.group_id
        if group not in self.games:
            self.games[group] = Game(self.bot, group, self)
        game: Game = self.games[group]
        if user_id not in game.players:
            game.join(user_id)
        else:
            game.exit(user_id)

    def message_listener(self, evt: GroupMessageEvent):
        player = evt.sender.user_id
        group = evt.group_id
        if group not in self.games:
            self.games[group] = Game(self.bot, group, self)
        game = self.games[group]
        if player in game.players and evt.message.split(" ")[0] in self.commands:
            command, *args = evt.message.split(" ")
            if not hasattr(self, f"zxh_command_{command}"):
                self.bot.client.send(evt.context, f"未知指令 {command}")
                return
            func = getattr(self, f"zxh_command_{command}")
            if 3+len(args) != len(func.__code__.co_varnames):
                self.bot.client.send(evt.context, "参数不足或过多")
                return
            func(evt, game, *args)

    def on_enable(self):
        self.bot: CountdownBot
        self.config: ZxhDmxConfig
        self.games: Dict[int, Game] = {}
        self.commands: Set[str] = set()
        for name in dir(self):
            if name.startswith("zxh_command_"):
                self.commands.add(name.replace("zxh_command_", "", 1))
        self.bot.logger.info(f"Loaded zxh commands: {self.commands}")
        self.register_command_wrapped(
            command_name="zxh",
            command_handler=self.command_zxh,
            help_string="加入/退出真心话大冒险",
            chats={ChatType.group},
            alias=["dmx"]
        )
        self.register_event_listener(GroupMessageEvent, self.message_listener)
        self.bot.server_app.route(
            "/zxh/get_data", methods=["POST"])(self.web_get_data)
        self.bot.server_app.route(
            "/zxh/set_data", methods=["POST"])(self.web_set_data)
        self.bot.server_app.route("/zxh/edit/")(self.web_edit)

    def get_problem_set_list(self) -> dict:
        result = {}
        for k, v in self.load_data()["problem_set"].items():
            result[k] = v["name"]
        return result

    def get_items(self) -> dict:
        result = {}
        for k, v in self.load_data()["items"].items():
            result[k] = v["name"]
        return result

    def zxh_command_帮助(self, event: GroupMessageEvent, game: Game):
        self.bot.client.send(event.context, HELP_STR)

    def zxh_command_状态(self, event: GroupMessageEvent, game: Game):
        self.bot.client.send(event.context, game.get_status())

    def zxh_command_开始(self, event: GroupMessageEvent, game: Game):
        game.start()

    def zxh_command_拼点(self, event: GroupMessageEvent, game: Game):
        game.play(event.sender.user_id)

    def zxh_command_选择(self, event: GroupMessageEvent, game: Game, problem_set):
        game.select(event.sender.user_id, problem_set)

    def zxh_command_查看物品(self, event: GroupMessageEvent, game: Game):
        self.bot.client.send(
            event.context, game.get_items((event.sender.user_id)))

    def zxh_command_使用物品(self, event: GroupMessageEvent, game: Game, item_id, arg):
        game.use_item(event.sender.user_id, item_id, arg)

    def zxh_command_接受(self, event: GroupMessageEvent, game: Game):
        game.accept(event.sender.user_id)
