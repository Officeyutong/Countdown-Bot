from register import command, message_listener
from cqhttp import CQHttp
from enum import Enum
from global_vars import VARS
from collections import namedtuple
import sys
import global_vars
import random
import os
import json
import flask
config = global_vars.CONFIG[__name__]
app: flask.Flask = global_vars.VARS["web_app"]
commands = None
games = None


class GameStage(Enum):
    WAITING_TO_START = 1
    DISTRIBUTE_POINTS = 2
    SELECT_PUNISH = 3
    PUNISH = 4


STAGES = {
    GameStage.WAITING_TO_START: "准备开始游戏",
    GameStage.DISTRIBUTE_POINTS: "拼点进行中",
    GameStage.SELECT_PUNISH: "选择惩罚中",
    GameStage.PUNISH: "惩罚进行中"
}
WEB_DIR = os.path.join(os.path.dirname(__file__), "web/")
HELP_STR =\
    """开始 ---- 开始本群游戏
拼点 ---- 参与拼点
接受 ---- 接受处罚
状态 ---- 查看游戏状态
帮助 ---- 查看帮助
提醒 ---- 提醒未拼点玩家参与拼点
跳过 ---- 跳过未拼点玩家
终止 ---- 强行终止当前游戏
选择 [题库] ---- 选择惩罚题库 
使用物品 [ID] ---- 使用物品
查看物品 ---- 查看物品列表"""
DATA_PATH = os.path.join(os.path.dirname(__file__))


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "真心话大冒险支持"
    }


def load():
    global games, commands
    print("Loading...")
    VARS["zxh_games"] = {}
    VARS["commands"] = set()
    commands = VARS["commands"]
    games = VARS["zxh_games"]
    for name in dir(sys.modules[__name__]):
        if name.startswith("zxh_command_"):
            commands.add(name[name.rindex("_")+1:])


def encode_json(obj):
    return json.JSONEncoder().encode(obj)


@app.route("/zxh/get_data", methods=["POST"])
def web_get_data():
    dat = flask.request.form
    if dat.get("password", None).lower() != get_md5(get_md5(config.ADMIN_PASSWORD)+"qwqqwqqwq"):
        return encode_json({
            "code": -1, "message": "密码错误"
        })
    return encode_json({
        "code": 0, "data": load_data()
    })


@app.route("/zxh/set_data", methods=["POST"])
def web_set_data():
    dat = flask.request.form
    if dat.get("password", None).lower() != get_md5(get_md5(config.ADMIN_PASSWORD)+"qwqqwqqwq"):
        return encode_json({
            "code": -1, "message": "密码错误"
        })
    save_data(json.JSONDecoder().decode(dat["data"]))
    return encode_json({
        "code": 0, "message": "操作成功"
    })
    # flask.make_response()


@app.route("/zxh/edit", methods=["GET"])
def web_edit_page():
    return flask.send_from_directory(WEB_DIR, "edit.html")


def get_md5(text: str) -> str:
    import hashlib
    ins = hashlib.md5()
    ins.update(text.encode("utf-8"))
    return ins.hexdigest()


class Game:
    # 群号
    group: str = ""
    # 参与的玩家，
    players = None
    # 当前进行的阶段
    stage: GameStage = None
    bot: CQHttp = None
    # 游戏结束后加入的用户列表
    join_at_next = None
    # 游戏结束后退出的用户列表
    exit_at_next = None
    # 尚未拼点玩家
    non_played: set = None
    # 已经拼点的玩家的点数
    points: dict = None
    # 是否是最大点数受罚
    max_punish = False
    # 被处罚到成为最小点数的玩家
    adjoint_punish: set = None
    # 某个玩家被限定所能选择的题库
    limits: dict = None
    # 玩家持有的物品
    # dict:set
    player_items: dict = None
    # 选择惩罚的人
    selector = -1
    # 还没完成惩罚的人
    punish_list: set = None
    # 剩余x轮后要执行的函数
    countdowns: list = None
    # 下一局要受惩罚的玩家集合
    next_punish: set = None

    def __init__(self, bot, group):
        self.group = group
        self.players = set()
        self.stage = GameStage.WAITING_TO_START
        self.bot = bot
        self.join_at_next = []
        self.exit_at_next = []
        self.non_played = set()
        self.points = {}
        self.adjoint_punish = set()
        self.limits = dict()
        self.player_items = dict()
        self.countdowns = []
        self.next_punish = set()
        # self.punishes = set()
        # self.send_message("群 {} 的游戏创建成功qwq".format(self.group))

    def send_message(self, message):
        """向这个游戏对应的群发送消息"""
        self.bot.send_group_msg(group_id=self.group, message=message)

    def get_profile(self, player) -> str:
        """获取玩家个人信息，以 "群名片 (QQ昵称)" 的形式返回"""
        profile = self.bot.get_group_member_info(
            group_id=self.group, user_id=player)
        return "{}({})".format(profile["card"], profile["nickname"])

    def get_status_player_score(self) -> str:
        """获取玩家分数状态文本"""
        msg = ""
        msg += "玩家点数:\n"
        for k, v in sorted(self.points.items(), key=lambda x: x[1]):
            msg += "{}: {}\n".format(self.get_profile(k), v)
        return msg

    def get_status_punish(self) -> str:
        msg = "尚未接受处罚的玩家:\n"
        for player in self.punish_list:
            msg += self.get_profile(player)
        return msg

    def get_status_distribute(self) -> str:
        """获取在拼点时候的状态文本"""
        msg = ""
        msg += self.get_status_player_score()
        msg += "尚未拼点玩家:\n"
        for player in self.non_played:
            msg += "{}\n".format(self.get_profile(player))
        return msg

    def get_status(self) -> str:
        """获取总体状态文本"""
        msg = "当前阶段: {}\n当前共有 {} 人参加:\n\n".format(
            STAGES[self.stage], len(self.players))
        for player_id in self.players:
            msg += self.get_profile(player_id)+"\n"
        if self.stage == GameStage.DISTRIBUTE_POINTS:
            msg += self.get_status_distribute()
        if self.stage == GameStage.PUNISH:
            msg += self.get_status_punish()
        return msg

    def notify_non_played(self) -> None:
        if self.stage != GameStage.DISTRIBUTE_POINTS:
            return
        if self.non_played:
            msg = ""
            for x in self.non_played:
                msg += "[CQ:at,qq={}]\n".format(x)
            msg += "\n请立刻参与拼点qwq"
            self.send_message(msg)

    def skip_non_played(self) -> None:
        if self.stage != GameStage.DISTRIBUTE_POINTS:
            return
        if self.non_played:
            self.non_played.clear()
            self._handle_play_end()

    def force_stop(self) -> None:
        # 强行终止游戏
        self._game_end()

    def join(self, player_id: int):
        """玩家加入游戏"""
        if player_id not in self.players:
            if self.stage == GameStage.WAITING_TO_START:
                self.players.add(player_id)
                self.send_message("[CQ:at,qq={}] 成功加入游戏qwq.\n输入 \"帮助\" 查看帮助\n当前状态:\n".format(
                    player_id)+self.get_status())
            else:
                self.join_at_next.append(player_id)
                self.send_message("[CQ:at,qq={}] 你将会在下次游戏开始时自动加入游戏哦qwq".format(
                    player_id))
        else:
            self.send_message("[CQ:at,qq={}] 你已经加入游戏了qwq".format(player_id))

    def exit(self, player_id: int):
        """玩家退出游戏"""
        if player_id in self.players:
            if self.stage == GameStage.WAITING_TO_START:
                self.players.remove(player_id)
                # del self.limits[player_id]
                if player_id in self.player_items:
                    del self.player_items[player_id]
                if player_id in self.limits:
                    del self.limits[player_id]
                if player_id in self.adjoint_punish:
                    self.adjoint_punish.remove(player_id)
                self.send_message("[CQ:at,qq={}] 成功退出游戏qwq，当前状态:\n".format(
                    player_id)+self.get_status())
            else:
                self.exit_at_next.append(player_id)
                self.send_message("[CQ:at,qq={}] 你将会在游戏结束时自动退出游戏哦qwq".format(
                    player_id))
        else:
            self.send_message(
                "[CQ:at,qq={}] 你不在当前游戏内呢qwq".format(player_id))

    def start(self):
        """开始游戏，从等候开始到拼点"""
        if self.stage != GameStage.WAITING_TO_START:
            self.send_message("游戏已经开始!")
            return
        if len(self.players) < config.MIN_REQUIRED_PLAYERS:
            self.send_message("至少需要 {} 个玩家才能开始游戏！".format(
                config.MIN_REQUIRED_PLAYERS))
            return
        for x in self.players:
            self.non_played.add(x)
        self.stage = GameStage.DISTRIBUTE_POINTS
        self.send_message("拼点开始啦！\n使用指令 \"拼点\" 参与qwq")

    def _handle_play_end(self) -> None:
        msg = "拼点结束！\n"+self.get_status_player_score()

        def key_func(x): return x[1]
        minval = min(self.points.items(), key=key_func)
        maxval = max(self.points.items(), key=key_func)
        msg += "\n点数最小: \n{} {}\n\n点数最大: \n{} {}\n\n".format(self.get_profile(
            minval[0]), minval[1], self.get_profile(maxval[0]), maxval[1])
        self.punish_list = self.adjoint_punish.copy()

        if minval[0] in self.adjoint_punish:
            self.adjoint_punish.remove(minval[0])
            self.send_message("{} 已成为最小点数，下局起不再连带受罚。".format(
                self.get_profile(minval[0])))
        if self.next_punish:
            # self.punish_list += self.next_punish
            self.punish_list = self.punish_list.union(self.next_punish)
            self.next_punish.clear()
        else:
            if self.max_punish:
                self.punish_list.add(maxval[0])
            else:
                self.punish_list.add(minval[0])
        print(self.punish_list)
        self.selector = minval[0]
        msg += "下面将会由点数最小的人([CQ:at,qq={}])选择惩罚方式:\n".format(minval[0])
        for k, v in get_problem_set_list().items():
            msg += "{}({})\n".format(v, k)
        msg += "使用指令 \"选择 [题库ID]\" 来选择处罚方式."
        self.stage = GameStage.SELECT_PUNISH
        self.send_message(msg)

    def play(self, player_id: int):
        """玩家参与拼点"""
        if self.stage != GameStage.DISTRIBUTE_POINTS:
            self.send_message(
                "[CQ:at,qq={}] 游戏尚未开始或已经拼点结束了呢".format(player_id))
            return
        if player_id not in self.non_played:
            self.send_message("[CQ:at,qq={}] 你已经完成了拼点了呢qwq".format(player_id))
            return
        val = random.randint(1, 100)
        while val == min(self.points.values(), default=101) or val == max(self.points.values(), default=-1):
            val = random.randint(1, 100)
        self.points[player_id] = val
        self.non_played.remove(player_id)
        self.send_message(
            "[CQ:at,qq={}] 你的点数为 {} ，看起来很不错呢qwq\n{}".format(player_id, val, self.get_status_distribute()))
        if not self.non_played:
            self._handle_play_end()

    def select(self, player_id: int, problem_set):
        if self.stage != GameStage.SELECT_PUNISH:
            self.send_message("现在不在惩罚选择阶段")
            return
        if player_id != self.selector:
            self.send_message("你无权选择处罚方式")
            return
        if player_id in self.limits and problem_set not in self.limits[player_id]:
            self.send_message("你被禁止选择本处罚方式")
            return
        SET = get_problem_set_list()
        ITEMS = load_data()["items"]
        if problem_set not in SET:
            self.send_message("请输入正确的题库ID")
            return
        msg = "处罚方式已经选定为: {}({})\n".format(SET[problem_set], problem_set)
        msg += "下面有请以下玩家接受处罚:\n"
        for player in self.punish_list:
            msg += "{} [CQ:at,qq={}]\n".format(
                self.get_profile(player), player)
        selected_item = random.choice(
            load_data()["problem_set"][problem_set]["rules"])
        print(selected_item)
        msg += "处罚内容为:\n"
        if selected_item["type"] == "simple":
            msg += selected_item["content"]+"\n"
            msg += "完成处罚的玩家请使用指令 \"接受\" 确认。\n或者使用 \"使用物品 [物品ID]\" 使用物品."
            self.send_message(msg)
            self.stage = GameStage.PUNISH
        elif selected_item["type"] == "item":
            msg += "所有受罚玩家获得物品: "+ITEMS[selected_item["content"]]["name"]
            list(map(lambda x: self._give_item(
                x, selected_item["content"]), self.punish_list))
            self.send_message(msg)
            self._game_end()
        elif selected_item["type"] == "punish":
            punish = load_data()["punish"][selected_item["content"]]
            msg += punish["name"]
            self.send_message(msg)
            self._handle_special_punish(
                player_id, selected_item["content"], punish)
            self._game_end()

    def _handle_special_punish(self, player_id: int, punish_id: str, punish: dict):
        if punish["type"] == "max_punish":
            self.max_punish = True
            self.countdowns.append(
                [punish["rounds"]+1, lambda: setattr(self, "max_punish", False)])
            # self.send_message("接下来 {} 局内，点数最大者")
        elif punish["type"] == "punish_until_min":
            self.adjoint_punish.add(player_id)
        elif punish["type"] == "problem_set_limit":
            self.limits[player_id] = punish["val"].split("|")
            self.countdowns.append(
                [punish["rounds"]+1, lambda: self.limits.pop(player_id, None)])
        elif punish["type"] == "next_punish":
            self.next_punish = self.punish_list.copy()
    # def _handle_

    def _give_item(self, player_id: int, item_id: str):
        if player_id not in self.player_items:
            self.player_items[player_id] = [item_id]
        else:
            self.player_items[player_id].append(item_id)
        self.send_message("[CQ:at,qq={}] 你已获得物品: {}".format(
            player_id, get_items()[item_id]))

    def _game_end(self):
        self.send_message("本轮游戏结束.")
        self.points.clear()
        self.punish_list.clear()
        self.selector = -1
        # 倒计时函数
        for item in self.countdowns:
            item[0] -= 1
            if item[0] == 0:
                item[1]()
        self.countdowns = list(filter(lambda x: x[0] != 0, self.countdowns))
        self.stage = GameStage.WAITING_TO_START
        for x in self.join_at_next:
            self.join(x)
        for x in self.exit_at_next:
            self.exit(x)
        self.join_at_next.clear()
        self.exit_at_next.clear()

    def get_items(self, player_id: int) -> str:
        msg = "[CQ:at,qq={}] 你的物品有:\n".format(player_id)
        ITEMS = get_items()
        for x in self.player_items.get(player_id, []):
            msg += "{}({})\n".format(ITEMS[x], x)
        return msg

    def use_item(self, player_id: int, item_id: str, arg):
        if self.stage != GameStage.PUNISH:
            self.send_message("[CQ:at,qq={}] 当前不在处罚阶段.".format(player_id))
            return
        if item_id not in self.player_items.get(player_id, []):
            self.send_message("[CQ:at,qq={}] 你没有这个物品.".format(player_id))
            return
        if item_id == "transfer_punish":
            arg = int(arg)
            if arg not in self.players:
                self.send_message("[CQ:at,qq={}] 指定玩家未参与.".format(player_id))
                return
            self.player_items[player_id].remove(item_id)
            self.punish_list.remove(player_id)
            self.punish_list.add(arg)
            self.send_message("[CQ:at,qq={}] 通过道具将惩罚转移给了 [CQ:at,qq={}]\n{}".format(
                player_id, arg, self.get_status_punish()))

    def accept(self, player_id: int):
        if self.stage != GameStage.PUNISH:
            self.send_message("[CQ:at,qq={}] 当前不在处罚阶段.".format(player_id))
            return
        if player_id not in self.punish_list:
            self.send_message("[CQ:at,qq={}] 你不在惩罚列表之中.".format(player_id))
            return
        self.punish_list.remove(player_id)
        self.send_message("玩家 {} 已接受惩罚.\n{}".format(
            self.get_profile(player_id), self.get_status_punish()))
        if not self.punish_list:
            self._game_end()
            return
        # self.send_message(self.get_status_punish())


@command(name="zxh", help="加入/退出真心话大冒险")
def zxh(bot: CQHttp, context, args):
    if context["group_id"] not in config.ENABLE_GROUPS:
        bot.send(context, "本群未启用本功能！")
        return
    user_id = context["sender"]["user_id"]
    group = context["group_id"]
    if group not in games:
        games[group] = Game(bot, group)
    game: Game = games[group]
    if user_id not in game.players:
        # players[group].add(user_id)
        game.join(user_id)
    else:
        game.exit(user_id)

    # print(context)


@message_listener
def zxh_command(bot: CQHttp, context, message):
    player = context["sender"]["user_id"]
    group = context["group_id"]
    if group not in games:
        games[group] = Game(bot, group)
    game: Game = games[group]
    if player in game.players and message.split(" ")[0] in commands:
        args = message.split(" ")
        while args[-1].strip() == "":
            del args[-1]
        command = args[0]
        this = sys.modules[__name__]
        if not hasattr(this, "zxh_command_%s" % command):
            bot.send(context, "未知指令 {}".format(command))
            return
        func = getattr(this, "zxh_command_%s" % command)
        if 3+len(args[1:]) != len(func.__code__.co_varnames):
            bot.send(context, "参数个数不足或过多")
            return
        func(bot, context, games[context["group_id"]], *args[1:])


def load_data():
    with open(os.path.join(DATA_PATH, "data.json"), "r") as file:
        return json.JSONDecoder().decode(file.read())


def save_data(obj):
    with open(os.path.join(DATA_PATH, "data.json"), "w") as file:
        return file.write(json.JSONEncoder().encode(obj))


def get_problem_set_list() -> dict:
    result = {}
    for k, v in load_data()["problem_set"].items():
        result[k] = v["name"]
    return result


def get_items() -> dict:
    result = {}
    for k, v in load_data()["items"].items():
        result[k] = v["name"]
    return result


def zxh_command_帮助(bot, context, game: Game):
    bot.send(context, HELP_STR)


def zxh_command_状态(bot, context, game: Game):
    bot.send(context, game.get_status())


def zxh_command_开始(bot, context, game: Game):
    game.start()


def zxh_command_拼点(bot, context, game: Game):
    game.play(context["sender"]["user_id"])


def zxh_command_选择(bot, context, game: Game, problem_set):
    game.select(context["sender"]["user_id"], problem_set)


def zxh_command_查看物品(bot, context, game: Game):
    bot.send(context, game.get_items((context["sender"]["user_id"])))


def zxh_command_使用物品(bot, context, game: Game, item_id, arg):
    game.use_item(context["sender"]["user_id"], item_id, arg)


def zxh_command_接受(bot, context, game: Game):
    game.accept(context["sender"]["user_id"])


def zxh_command_提醒(bot, context, game: Game):
    game.notify_non_played()


def zxh_command_跳过(bot, context, game: Game):
    game.skip_non_played()


def zxh_command_终止(bot, context, game: Game):
    game.force_stop()
