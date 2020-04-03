from enum import Enum
from common.countdown_bot import CountdownBot
from typing import List, Dict, Set, Union, Callable
from threading import Lock
import random


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


class Game:
    # 群号
    group: str = ""
    # 参与的玩家，
    players = None
    # 当前进行的阶段
    stage: GameStage = None
    bot: CountdownBot = None
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
    # 上一条拼点消息的ID，用以撤回 -1表示不存在
    last_play_message_id: int = -1

    def __init__(self, bot, group, plugin):
        self.group: int = group
        self.players: Set[int] = set()
        self.stage: GameStage = GameStage.WAITING_TO_START
        self.bot: CountdownBot = bot
        self.join_at_next: List[int] = []
        self.exit_at_next: List[int] = []
        self.non_played: List[int] = set()
        self.points: Dict[int, int] = {}
        self.adjoint_punish: Set[int] = set()
        self.limits: Dict[int, List[str]] = dict()
        self.player_items: Dict[int, List[str]] = dict()
        self.countdowns: List[List[Union[int, Callable[[], None]]]] = []
        self.next_punish: Set[int] = set()
        # 接下来每一局这些玩家要自动加上给定的点数
        self.add_points: Dict[int, int] = dict()
        self.player_list_lock = Lock()
        self.base_lock = Lock()
        self.plugin = plugin
        self.last_play_message_id = -1
        # self.punishes = set()
        # self.send_message("群 {} 的游戏创建成功qwq".format(self.group))

    def send_message(self, message):
        """向这个游戏对应的群发送消息"""
        return self.bot.send_group_msg(group_id=self.group, message=message)

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
            msg += self.get_profile(player)+"\n"
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
            if len(self.points) < 1:
                self.send_message("必须至少有一个玩家进行拼点才可跳过!")
                return
            self.non_played.clear()
            self._handle_play_end()

    def force_stop(self) -> None:
        # 强行终止游戏
        self._game_end()

    def join(self, player_id: int):
        """玩家加入游戏"""
        if player_id not in self.players:
            self.player_list_lock.acquire()
            if self.stage == GameStage.WAITING_TO_START:
                self.players.add(player_id)
                self.bot.logger.info(f"{player_id} joined,{self.players}")
                self.send_message("[CQ:at,qq={}] 成功加入游戏qwq.\n输入 \"帮助\" 查看帮助\n当前状态:\n".format(
                    player_id)+self.get_status())
            else:
                self.bot.logger.info(
                    f"{player_id} scheduled to join next,{self.join_at_next},{self.players}")
                self.join_at_next.append(player_id)
                self.send_message("[CQ:at,qq={}] 你将会在下次游戏开始时自动加入游戏哦qwq".format(
                    player_id))
            self.player_list_lock.release()
        else:
            self.send_message("[CQ:at,qq={}] 你已经加入游戏了qwq".format(player_id))

    def exit(self, player_id: int):
        """玩家退出游戏"""
        if player_id in self.players:
            self.player_list_lock.acquire()
            if self.stage == GameStage.WAITING_TO_START:
                self.players.remove(player_id)
                # del self.limits[player_id]
                if player_id in self.player_items:
                    del self.player_items[player_id]
                if player_id in self.limits:
                    del self.limits[player_id]
                if player_id in self.adjoint_punish:
                    self.adjoint_punish.remove(player_id)
                if player_id in self.add_points:
                    self.add_points.pop(player_id)
                if player_id in self.next_punish:
                    self.next_punish.remove(player_id)
                self.bot.logger.info(f"{player_id} exited,{self.players}")
                self.send_message("[CQ:at,qq={}] 成功退出游戏qwq，当前状态:\n".format(
                    player_id)+self.get_status())

            else:
                self.exit_at_next.append(player_id)
                self.bot.logger.info(
                    f"{player_id} scheduled to join next,{self.exit_at_next},{self.players}")
                self.send_message("[CQ:at,qq={}] 你将会在游戏结束时自动退出游戏哦qwq".format(
                    player_id))
            self.player_list_lock.release()
        else:
            self.send_message(
                "[CQ:at,qq={}] 你不在当前游戏内呢qwq".format(player_id))

    def start(self):
        """开始游戏，从等候开始到拼点"""
        if self.stage != GameStage.WAITING_TO_START:
            self.send_message("游戏已经开始!")
            return
        if len(self.players) < self.plugin.config.MIN_REQUIRED_PLAYERS:
            self.send_message("至少需要 {} 个玩家才能开始游戏！".format(
                self.plugin.config.MIN_REQUIRED_PLAYERS))
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
            self.bot.logger.info(f"Next punish: {self.next_punish}")
            # self.punish_list += self.next_punish
            self.punish_list = self.punish_list.union(self.next_punish)
            self.next_punish.clear()
        else:
            if self.max_punish:
                self.punish_list.add(maxval[0])
            else:
                self.punish_list.add(minval[0])
        self.bot.logger.info(f"Punish list :f{self.punish_list}")
        self.selector = minval[0]
        msg += "下面将会由点数最小的人([CQ:at,qq={}])选择惩罚方式:\n".format(minval[0])
        for k, v in self.plugin.get_problem_set_list().items():
            msg += "{}({})\n".format(v, k)
        msg += "使用指令 \"选择 [题库ID]\" 来选择处罚方式."
        self.stage = GameStage.SELECT_PUNISH
        self.send_message(msg)
        self.last_play_message_id = -1

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
        if player_id in self.add_points:
            raw_points = val
            val = min(100, val+self.add_points[player_id])
            val = max(1, val)
            self.send_message(
                f"[CQ:at,qq={player_id}],原始点数: {raw_points},惩罚点数{val}")
        if val > 70:
            joke_message = "看起来很不错呢qwq"
        elif val < 30:
            joke_message = "看起来有点凉呢qwq"
        else:
            joke_message = "qwq"
        self.points[player_id] = val
        self.non_played.remove(player_id)
        result = self.send_message(
            f"[CQ:at,qq={player_id}] 你的点数为 {val} ,{joke_message}\n{self.get_status_distribute()}")
        if self.last_play_message_id != -1:
            try:
                self.bot.client.delete_msg(self.last_play_message_id)
            except:
                import traceback
                traceback.print_exc()
        self.last_play_message_id = result["message_id"]
        self.bot.logger.debug(
            f"Last play message ID: {self.last_play_message_id}")
        if not self.non_played:
            self._handle_play_end()

    def select(self, player_id: int, problem_set, reselect: bool):
        if self.stage != GameStage.SELECT_PUNISH and not reselect:
            self.send_message("现在不在惩罚选择阶段")
            return
        if player_id != self.selector:
            self.send_message("你无权选择处罚方式")
            return
        if player_id in self.limits and problem_set not in self.limits[player_id]:
            self.send_message("你被禁止选择本处罚方式")
            return

        SET = self.plugin.get_problem_set_list()
        ITEMS = self.plugin.load_data()["items"]
        if problem_set not in SET:
            self.send_message("请输入正确的题库ID")
            return
        msg = "处罚方式已经选定为: {}({})\n".format(SET[problem_set], problem_set)

        if reselect:
            self.next_punish = self.punish_list.copy()
            msg += "处罚方式已重新选定，代价为所有受惩罚玩家下一局受罚\n"
            # self.stage=GameStage.p
        msg += "下面有请以下玩家接受处罚:\n"
        for player in self.punish_list:
            msg += "{} [CQ:at,qq={}]\n".format(
                self.get_profile(player), player)
        selected_item = random.choice(
            self.plugin.load_data()["problem_set"][problem_set]["rules"])
        self.bot.logger.info(selected_item)
        msg += "处罚内容为:\n"
        if selected_item["type"] == "simple":
            msg += selected_item["content"]+"\n"
            msg += "完成处罚的玩家请使用指令 \"接受\" 确认.\n或者使用 \"使用物品 [物品ID]\" 使用物品.\n或者使用 \"更换题目 [题库]\"重新选取惩罚."
            self.send_message(msg)
            self.stage = GameStage.PUNISH
        elif selected_item["type"] == "item":
            msg += "所有受罚玩家获得物品: "+ITEMS[selected_item["content"]]["name"]
            list(map(lambda x: self._give_item(
                x, selected_item["content"]), self.punish_list))
            self.send_message(msg)
            self._game_end()
        elif selected_item["type"] == "punish":
            punish = self.plugin.load_data(
            )["punish"][selected_item["content"]]
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
                [
                    int(punish["rounds"])+1,
                    lambda: self.limits.pop(player_id, None),
                    f"[CQ:at,qq={player_id}] 的题库限制 {punish['val']} 已经解除"
                ])
        elif punish["type"] == "next_punish":
            self.next_punish = self.punish_list.copy()
        elif punish["type"] == "add_points":
            self.countdowns.append(
                [
                    int(punish["rounds"])+1,
                    lambda: self.add_points.pop(
                        player_id) if player_id in self.add_points else None,
                    f"[CQ:at,qq={player_id}] 的每局增加 {punish['val']} 点数已经解除"
                ])
            self.add_points[player_id] = int(punish["val"])
    # def _handle_

    def _give_item(self, player_id: int, item_id: str):
        if player_id not in self.player_items:
            self.player_items[player_id] = [item_id]
        else:
            self.player_items[player_id].append(item_id)
        self.send_message("[CQ:at,qq={}] 你已获得物品: {}".format(
            player_id, self.plugin.get_items()[item_id]))

    def _game_end(self):
        self.send_message("本轮游戏结束.")
        if self.points:
            self.points.clear()
        # self.player_list_lock.acquire()
        if self.punish_list:
            self.punish_list.clear()
        # self.player_list_lock.release()
        self.selector = -1
        # 倒计时函数
        for item in self.countdowns:
            item[0] -= 1
            if item[0] == 0:
                item[1]()
                if len(item) == 3:
                    self.send_message(item[2])
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
        ITEMS = self.plugin.get_items()
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
            if player_id not in self.punish_list:
                self.send_message("[CQ:at,qq={}] 你没有被惩罚.".format(player_id))
                return
            self.player_items[player_id].remove(item_id)
            self.punish_list.remove(player_id)
            self.punish_list.add(arg)
            self.send_message("[CQ:at,qq={}] 通过道具将惩罚转移给了 [CQ:at,qq={}]\n{}".format(
                player_id, arg, self.get_status_punish()))
        elif item_id == "adjoint_punish":
            arg = int(arg)
            if arg not in self.players:
                self.send_message(
                    "[CQ:at,qq={}] 指定玩家未参与.".format(player_id))
                return
            if player_id not in self.punish_list:
                self.send_message("[CQ:at,qq={}] 你没有被惩罚.".format(player_id))
                return
            if player_id == arg:
                self.send_message("[CQ:at,qq={}] ???".format(player_id))
                return
            self.player_items[player_id].remove(item_id)
            self.punish_list.add(arg)
            self.send_message(
                f"[CQ:at,qq={player_id}] 邀请 [CQ:at,qq={arg}] 和自己一起受罚\n{self.get_status_punish()}")

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
