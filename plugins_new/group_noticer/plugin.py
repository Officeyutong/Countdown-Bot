from common.event import GroupMemberDecreaseEvent, GroupMemberDecreaseType, GroupMemberIncreaseEvent
from common.countdown_bot import CountdownBot
from common.config_loader import ConfigBase
from common.plugin import Plugin
from common.datatypes import PluginMeta


class GroupNoticerConfig(ConfigBase):
    # 不启用的群，int
    DISABLE_GROUPS = [

    ]

    WELCOME_MESSAGE = " {at}\n哇，你来啦，要玩的开心哦！"


class GroupNoticer(Plugin):
    def exit_listener(self, evt: GroupMemberDecreaseEvent):
        if evt.group_id not in self.config.DISABLE_GROUPS:
            stranger_info: dict = self.bot.client.get_stranger_info(
                user_id=evt.user_id, no_cache=True)
            if evt.sub_type != GroupMemberDecreaseType.kick_me:
                resp = f"""用户 {stranger_info["user_id"]}({stranger_info["nickname"]}) 已 {"退出" if evt.sub_type == GroupMemberDecreaseType.leave else "被踢出"} 本群"""
                self.bot.client.send_group_msg(
                    group_id=evt.group_id, message=resp)

    def join_listener(self, evt: GroupMemberIncreaseEvent):
        if evt.group_id not in self.config.DISABLE_GROUPS:
            self.bot.client.send_group_msg(group_id=evt.group_id,
                                           message=self.config.WELCOME_MESSAGE.format(at=f"[CQ:at,qq={evt.user_id}]"))

    def on_enable(self):
        self.bot: CountdownBot
        self.config: GroupNoticerConfig
        self.register_event_listener(GroupMemberDecreaseEvent, self.exit_listener)
        self.register_event_listener(GroupMemberIncreaseEvent, self.join_listener)


def get_plugin_class(): return GroupNoticer


def get_config_class(): return GroupNoticerConfig


def get_plugin_meta(): return PluginMeta(
    author="officeyutong",
    version=2.0,
    description="群通知器"
)
