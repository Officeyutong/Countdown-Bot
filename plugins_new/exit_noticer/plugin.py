from common.event import GroupMemberDecreaseEvent, GroupMemberDecreaseType
from common.countdown_bot import CountdownBot
from common.config_loader import ConfigBase
from common.plugin import Plugin
from common.datatypes import PluginMeta


class GroupExitNoticerConfig(ConfigBase):
    # 不启用的群，int
    DISABLE_GROUPS = [

    ]


class GroupExitNoticer(Plugin):
    def listener(self, evt: GroupMemberDecreaseEvent):
        if evt.group_id not in self.config.DISABLE_GROUPS:
            stranger_info: dict = self.bot.client.get_stranger_info(
                user_id=evt.user_id, no_cache=True)
            if evt.sub_type != GroupMemberDecreaseType.kick_me:
                resp = f"""用户 {stranger_info["user_id"]}({stranger_info["nickname"]}) 已 {"退出" if evt.sub_type==GroupMemberDecreaseType.leave else "被踢出"} 本群"""
                self.bot.client.send_group_msg(
                    group_id=evt.group_id, message=resp)

    def on_enable(self):
        self.bot: CountdownBot
        self.config: GroupExitNoticerConfig
        self.register_event_listener(GroupMemberDecreaseEvent, self.listener)


def get_plugin_class(): return GroupExitNoticer


def get_config_class(): return GroupExitNoticerConfig


def get_plugin_meta(): return PluginMeta(
    author="officeyutong",
    version=1.0,
    description="退群通知器"
)
