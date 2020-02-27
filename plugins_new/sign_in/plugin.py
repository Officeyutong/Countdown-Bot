from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import GroupMessageEvent
from typing import List, Dict
from .datatypes import SignInData

import sqlite3
import time


class SignInConfig(ConfigBase):
    # 不启用签到的群
    BLACK_LIST_GROUPS = {"88888888"}


class SignInPlugin(Plugin):
    def get_last_sign_in_data(self, group_id: int, user_id: int) -> SignInData:
        if self.conn.execute(
                "SELECT COUNT(*) FROM SIGNINS WHERE GROUP_ID = ? AND USER_ID = ?", 
                (group_id, user_id,)).fetchone()[0]:
            # 存在上一条记录
            last_time: int = self.conn.execute(
                "SELECT MAX(TIME) FROM SIGNINS WHERE GROUP_ID = ? AND USER_ID = ?", 
                (group_id, user_id,)).fetchone()[0] # 得到上次签到时间
            result = self.conn.execute(
                "SELECT * FROM SIGNINS WHERE GROUP_ID = ? AND USER_ID = ? AND TIME = ?", (
                    group_id,
                    user_id,
                    last_time,
                )).fetchone() #上次签到数据
            return SignInData(result[0], result[1], result[2], result[3], result[4], result[5])
        else:
            return SignInData(group_id, user_id, 0, 0, 0, 0)

    def clac_sign_in_times(self, group_id: int, user_id: int) -> (int, int):
        now = time.localtime(int(time.time()))
        this_month = int(time.mktime(time.strptime(
            f"{now.tm_year}-{now.tm_mon}", "%Y-%m"))) # 获得当前月开始的时间戳
        all_times = self.conn.execute(
            "SELECT COUNT(*) FROM SIGNINS WHERE GROUP_ID = ? AND USER_ID = ?", 
            (group_id, user_id,)).fetchone()[0] # 签到总数
        month_times = self.conn.execute(
            "SELECT COUNT(*) FROM SIGNINS WHERE GROUP_ID = ? AND USER_ID = ? AND TIME >= ? ",
            (group_id, user_id, this_month,)).fetchone()[0] #本月签到数
        return all_times, month_times

    def save_data(self, sign_in_data: SignInData) -> None:
        self.conn.execute(
            "INSERT INTO SIGNINS (GROUP_ID,USER_ID,TIME,DURATION,SCORE,SCORE_CHANGES) VALUES (?,?,?,?,?,?)", (
                sign_in_data.group_id,
                sign_in_data.user_id,
                sign_in_data.time,
                sign_in_data.duration,
                sign_in_data.score,
                sign_in_data.score_changes,
            )) # 写入签到记录
        
        if self.conn.execute("SELECT COUNT(*) FROM USERS WHERE GROUP_ID = ? AND USER_ID = ?",
                             (sign_in_data.group_id, sign_in_data.user_id,)).fetchone()[0]:
            # 检查用户信息存在
            self.conn.execute("UPDATE USERS SET SCORE = ? WHERE GROUP_ID = ? AND USER_ID = ?", (
                sign_in_data.score,
                sign_in_data.group_id,
                sign_in_data.user_id,
            )) #更新用户信息
        else:
            self.conn.execute("INSERT INTO USERS (GROUP_ID,USER_ID,SCORE) VALUES (?,?,?)", (
                sign_in_data.group_id,
                sign_in_data.user_id,
                sign_in_data.score,
            )) # 新建用户信息
        self.conn.commit()

    def command_sign_in(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        group_id = int(context['group_id'])

        if str(group_id) in self.config.BLACK_LIST_GROUPS:
            self.bot.client_async.send(context, "签到功能在本群停用")
            return

        user_id = int(context['sender']['user_id'])

        last_sign_in_data = self.get_last_sign_in_data(group_id, user_id) #上次签到的数据
        last_time = time.localtime(last_sign_in_data.time) #上次签到的时间
        current_time = time.localtime(int(time.time())) #当前时间
        all_times, month_times = self.clac_sign_in_times(group_id, user_id) #总签到次数，当月签到次数

        if last_time.tm_year == current_time.tm_year and last_time.tm_yday == current_time.tm_yday:
            # 年份和天数都相等，当天已经签到
            self.bot.client_async.send(context, f"""[CQ:at,qq={user_id}]今天已经签过到啦！
连续签到：{last_sign_in_data.duration}天
当前积分：{last_sign_in_data.score}
本月签到次数：{month_times}
累计群签到次数：{all_times}""")
            return

        sign_in_data = SignInData

        sign_in_data.time = int(time.mktime(current_time)) # 签到时间
        sign_in_data.user_id = user_id
        sign_in_data.group_id = group_id

        if last_time.tm_year == current_time.tm_year:
            # 上次签到和本次签到年份相等
            if last_time.tm_yday + 1 == current_time.tm_yday:
                #上次签到日期和本次差1，连续签到
                sign_in_data.duration = last_sign_in_data.duration+1
            else:
                sign_in_data.duration = 1
        elif last_time.tm_year + 1 == current_time.tm_year:
            # 上次签到和本次签到年份差1
            if (last_time.tm_mon == 12 and last_time.tm_mday == 31
                    and current_time.tm_mon == 1 and current_time.tm_mday == 1):
                # 12.31日和1.1日
                sign_in_data.duration += 1
            else:
                sign_in_data.duration = 1
        else:
            sign_in_data.duration = 1

        duration_add = sign_in_data.duration-1
        if duration_add > 10:
            duration_add = 10
        if sign_in_data.duration > 30:
            duration_add = 15
        # 连续签到加成计算：
        # 2-10天：天数-1
        # 10-30天：10
        # 大于30天：15

        sign_in_data.score_changes = 10 + duration_add #基础积分：10
        sign_in_data.score = last_sign_in_data.score + sign_in_data.score_changes
        
        self.save_data(sign_in_data)

        self.bot.client_async.send(context,
                                   f"""给[CQ:at,qq={sign_in_data.user_id}]签到成功了！
连续签到：{sign_in_data.duration}天
积分增加：{sign_in_data.score_changes}
连续签到加成：{duration_add}
当前积分：{sign_in_data.score}
本月签到次数：{month_times+1}
累计群签到次数：{all_times+1}""")

    def on_disable(self):
        self.logger.info(f"SignIn: closing database..")
        self.conn.close()

    def on_enable(self):
        self.bot: CountdownBot
        self.config: SignInConfig
        self.conn = sqlite3.connect(
            self.plugin_base_dir/"sign_in.db", check_same_thread=False)
        try:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS SIGNINS(
                GROUP_ID      INTEGER NOT NULL,
                USER_ID       INTEGER NOT NULL,
                TIME          INTEGER NOT NULL,
                DURATION      INTEGER NOT NULL,
                SCORE         INTEGER NOT NULL,
                SCORE_CHANGES INTEGER NOT NULL
            )""")
            # 群号，QQ号，签到时间，连续签到次数，当前积分，和上次比较积分变化
            self.conn.execute("""CREATE TABLE IF NOT EXISTS USERS(
                GROUP_ID INTEGER NOT NULL,
                USER_ID  INTEGER NOT NULL,
                SCORE    INTEGER NOT NULL
            )""")
            # 群号，QQ号，当前积分 可以拿来做排名
            self.conn.execute(
                "CREATE INDEX GROUP_ID_INDEX ON SIGNINS(GROUP_ID)")
            self.conn.execute(
                "CREATE INDEX USER_ID_INDEX  ON SIGNINS(USER_ID)")
            self.conn.execute("CREATE INDEX TIME_INDEX     ON SIGNINS(TIME)")
            self.conn.execute("CREATE INDEX GROUP_ID_INDEX ON USERS(GROUP_ID)")
            self.conn.execute("CREATE INDEX USER_ID_INDEX  ON USERS(USER_ID)")
            self.conn.commit()
            self.conn.close()
        except Exception as ex:
            self.logger.error(ex)
        self.register_command_wrapped(
            command_name="签到",
            command_handler=self.command_sign_in,
            help_string="签到",
            chats={ChatType.group},
            alias=["sign-in", "check-in"],
        )


def get_plugin_class():
    return SignInPlugin


def get_config_class():
    return SignInConfig


def get_plugin_meta():
    return PluginMeta(
        "Antares", 2.0, "群签到"
    )
