from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.command import Command, ChatType
from common.event import *
from common.loop import TimeTuple
from typing import List


class MyEventListener(Listener):
    def __init__(self, plugin):
        self.plugin = plugin

    # def message(self, evt: MessageEvent):
    #     self.plugin.logger.info(evt.message)
    #     self.plugin.logger.info(evt)
    def group_message(self, evt: GroupMessageEvent):
        self.plugin.bot.logger.debug(evt.message)
        self.plugin.bot.logger.debug(evt.sender.user_id)
        evt.at_sender = True
        evt.reply = f"嘤嘤嘤 {evt.message}"
        print(evt)

    def private_message(self, evt: PrivateMessageEvent):
        self.plugin.bot.logger.debug(evt.message)
        self.plugin.bot.logger.debug(evt.sender.user_id)
        evt.reply = evt.message

    def fileup(self, evt: GroupFileUploadEvent):
        self.plugin.bot.logger.debug(evt)

    def admin_change(self, evt: GroupAdminChangeEvent):
        self.plugin.bot.logger.debug(evt)

    def member_decrease(self, evt: GroupMemberDecreaseEvent):
        self.plugin.bot.logger.debug(evt)

    def member_increase(self, evt: GroupMemberIncreaseEvent):
        self.plugin.bot.logger.debug(evt)

    def group_ban(self, evt: GroupBanEvent):
        self.plugin.bot.logger.debug(evt)

    def request_friend(self, evt: FriendAddRequestEvent):
        self.plugin.bot.logger.debug(evt)
        evt.approve = True

    def request_group(self, evt: GroupInviteOrAddRequestEvent):
        self.plugin.bot.logger.debug(evt)
        evt.approve = False


class MyPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def my_loop(self):
        self.bot.logger.debug("executing...")
        # import asyncio
        # await asyncio.sleep(1)
        self.bot.logger.debug("Meow~")
        # raise Exception("嘤嘤嘤")

    def on_enable(self):
        # self.bot
        self.logger.info("You are loading Me!")
        self.logger.info(self.config.TEST_URL)
        self.logger.debug(self.simple_console_command)
        self.register_command_wrapped(
            command_name="qwq",
            command_handler=self.simple_console_command,
            help_string="Meow~",
            chats=None,
            alias=None,
            is_console=True
        )
        self.register_command_wrapped(
            command_name="qwq",
            command_handler=self.simple_command,
            help_string="Meow~",
            chats={ChatType.private},
            alias=["qwq1", "Qwq2"],
            is_console=False
        )
        self.register_all_event_listeners(
            MyEventListener(self)
        )
        from datetime import datetime
        self.register_schedule_loop(
            TimeTuple(datetime.now().hour,
                      datetime.now().minute+1), self.my_loop()
        )
        import datetime
        self.register_state_handler(lambda: f"现在是: {datetime.datetime.now()}")

    def simple_command(self, plugin: 'MyPlugin', args: List[str], raw_string: str, context: dict, evt):
        print(locals())

    def simple_console_command(self, plugin: 'MyPlugin', args: List[str], raw_string: str, context: dict, evt):
        print("qwqqwq")
        print(locals())

        async def qwqqwq():
            import asyncio
            await asyncio.sleep(5)
            self.logger.info("Meow~")
        self.bot.submit_async_task(qwqqwq())


class MyPluginConfig(ConfigBase):
    TEST_URL: str = "default_value"


def get_plugin_class():
    return MyPlugin


def get_config_class():
    return MyPluginConfig


def get_plugin_meta():
    return PluginMeta(
        "qwqqwwq", 1.0, "测试一下"
    )
