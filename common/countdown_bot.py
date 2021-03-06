from cqhttp import CQHttp  # type: ignore
# from aiocqhttp import CQHttp
from pathlib import Path
from common.plugin import Plugin  # type: ignore
from common.event import EventManager, MessageEvent  # type: ignore
import common.event as event  # type: ignore
from common.command import CommandManager, Command, ChatType  # type: ignore
from common.state import StateManager  # type: ignore
from common.config_loader import ConfigBase, load_from_file  # type: ignore
from typing import List, Iterable, Callable, DefaultDict, Any, Optional, Union, Dict, Tuple
from common.datatypes import PluginMeta  # type: ignore
from common.loop import ScheduleLoopManager  # type: ignore
from common.utils import stop_thread  # type: ignore
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from .api_client.api import ClientWrapper  # type: ignore
from .api_client.async_api_client import AsyncHTTPAPIClient  # type: ignore
from .base_commands import *
import concurrent
import sys
import os
import importlib
import asyncio
import signal
import logging
import datetime
import sys
import io
import sqlite3
import html
LOGGER: logging.Logger = None
APRIL_FOOL: bool = False


class CountdownBotConfig(ConfigBase):
    API_URL = "http://127.0.0.1:5001"
    ACCESS_TOKEN = "sxoiers"
    SECRET = ""
    POST_ADDRESS = "0.0.0.0"
    POST_PORT = 5002
    CHECK_INTERVAL = 5
    EXECUTE_DELAY = 60
    COMMAND_PREFIX = ["--", "!!"]
    COMMAND_COOLDOWN = 0
    DEBUG = False
    SERVER_URL = "http://ecs.zhehao.top"
    LOGGING_LEVEL = logging.INFO
    MAX_THREAD_EXECUTORS = 10
    BLACKLIST_USERS = [

    ]  # 不处理来自这些用户的指令
    # 群内为了防止刷屏使用help指令的延迟，单位为s，对单个用户限制
    HELP_INVOKE_DELAY = 24*3600
    # 启用帮助指令调用限制的群
    ENABLE_HELP_INVOKE_DELAY_GROUPS: List[int] = [

    ]
    # 代理地址，形如http://127.0.0.1:8000
    # 设置为None表示不使用
    PROXY = None



class CountdownBot(CQHttp):
    def __init__(self, app_root: Path, **flask_args):
        """
        初始化CountdownBot
        @param app_root: 程序main.py所在的目录
        @param flask_args: 传递给Flask的额外参数 
        """
        self.app_root = app_root
        self.__config = load_from_file(
            self.app_root/"config.py", CountdownBotConfig)
        super().__init__(api_root=self.config.API_URL,
                         access_token=self.config.ACCESS_TOKEN, secret=self.config.SECRET)
        self.plugins: List[Plugin] = []
        self.event_manager = EventManager(self)
        self.state_manager = StateManager()
        self.command_manager = CommandManager(self)
        self.loop_manager = ScheduleLoopManager(
            self.config.CHECK_INTERVAL, self.config.EXECUTE_DELAY, self)
        self.flask_args = flask_args
        self.__logger = logging.Logger(
            "CountdownBot", level=self.config.LOGGING_LEVEL
        )
        self.last_command_execute: DefaultDict[str, float] = DefaultDict(
            default_factory=lambda: 0)  # 冷却标识符->执行时间
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.MAX_THREAD_EXECUTORS
        )
        self.loop = asyncio.get_event_loop()
        self.api_client = AsyncHTTPAPIClient(
            self.loop,
            self.config.API_URL,
            self.config.ACCESS_TOKEN,
            self.config.SECRET
        )
        self.client = ClientWrapper(self.api_client.invoke)
        self.client_async = ClientWrapper(lambda x, y: asyncio.wrap_future(
            self.api_client.invoke_async(x, y), loop=self.loop))
        global LOGGER, APRIL_FOOL
        LOGGER = self.logger
        now = datetime.datetime.now()
        APRIL_FOOL = (now.day == 1 and now.month == 4)
        self.april_fool = APRIL_FOOL
        self.last_helpcommand_invoke: Dict[int, float] = {  # QQ=>调用时间

        }

    @property
    def logger(self) -> logging.Logger:
        """获取此Bot的Logger"""
        return self.__logger

    @property
    def config(self) -> CountdownBotConfig:
        """Bot的全局配置"""
        return self.__config

    def handle_command(self, evt: MessageEvent, context: dict, cooldown_identifier: str, current_chat_type: ChatType) -> bool:
        """
        将一个消息事件视为命令进行处理。
        此函数会在收到消息时被自动调用
        @param evt: 代表此次处理的事件对象
        @param context: evt.context
        @param cooldown_identifier: 触发此事件的对象在统计命令冷却时的标识符
        @param current_chat_type: 触发此事件的对象所处的聊天环境

        @return: 这个事件是否为一次命令调用
        """
        if evt.user_id in self.config.BLACKLIST_USERS:
            # 忽略黑名单用户的消息
            return False
        done = False
        for prefix in self.config.COMMAND_PREFIX:
            if evt.raw_message.startswith(prefix):
                done = True
                splited = evt.message[len(prefix):].split()
                command_name = splited[0]
                self.logger.info(f"Executing command: {evt.raw_message} ")

                if command_name not in self.command_manager.name_bindings:
                    self.send(context, f"未知指令: \"{command_name}\"")
                    break
                command = self.command_manager.name_bindings[command_name]
                if current_chat_type not in command.available_chats:
                    self.send(context, f"指令 {command_name} 不可在此对话类型下使用")
                    self.logger.info(
                        f"Ignored {evt} as it doesn't support ChatType: {current_chat_type}")
                    break
                import time
                if time.time()-self.last_command_execute.get(cooldown_identifier, 0) < self.config.COMMAND_COOLDOWN/1000:
                    self.send(context, f"指令在冷却中,请稍后尝试执行.")
                    break
                self.last_command_execute.update(
                    {cooldown_identifier: time.time()})
                self.logger.debug(f"invoking {command_name}")
                self.command_manager.name_bindings[command_name].invoke(
                    args=splited[1:],
                    raw_string=html.unescape(evt.raw_message[len(prefix):]),
                    context=context,
                    event=evt,
                    bot=self
                )
                break
        return done

    def __group_message_handler(self, context: dict) -> dict:
        evt = event.GroupMessageEvent(context)
        self.logger.info(f"Handling group message {context}")
        if not self.handle_command(
            evt=evt, context=context, cooldown_identifier=f"group:{evt.group_id}", current_chat_type=ChatType.group
        ):
            self.event_manager.process_event(evt)
            result = {}
            for key in ["reply", "auto_escape", "at_sender", "delete", "kick", "ban", "ban_duration"]:
                if getattr(evt, key) is not None:
                    result[key] = getattr(evt, key)
            return result

    def __private_message_handler(self, context: dict) -> Optional[dict]:
        evt = event.PrivateMessageEvent(context)
        self.logger.info(f"Handling private message {context}")
        if not self.handle_command(
            evt=evt, context=context, cooldown_identifier=f"private:{evt.user_id}", current_chat_type=ChatType.private
        ):
            self.event_manager.process_event(evt)
            result = {}
            for key in ["reply", "auto_escape"]:
                if getattr(evt, key) is not None:
                    result[key] = getattr(evt, key)
            return result
        return None

    def __discuss_message_handler(self, context: dict) -> Optional[dict]:
        evt = event.DiscussMessageEvent(context)
        self.logger.info(f"Handling discuss message {context}")
        # self.logger.info(f"Processing message event - discuss_id: {evt.discuss_id} user_id: {evt.user_id}")
        if not self.handle_command(
            evt=evt, context=context, cooldown_identifier=f"discuss:{evt.discuss_id}", current_chat_type=ChatType.discuss
        ):
            self.event_manager.process_event(evt)
            result = {}
            for key in ["reply", "auto_escape", "at_sender"]:
                if getattr(evt, key) is not None:
                    result[key] = getattr(evt, key)
            return result
        return None

    def __init_events(self):
        self.on_message("private")(self.__private_message_handler)
        self.on_message("group")(self.__group_message_handler)
        self.on_message("discuss")(self.__discuss_message_handler)
        self.on_notice("group_upload")(self.__make_event_handler(
            event.GroupFileUploadEvent, []))
        self.on_notice("group_admin")(self.__make_event_handler(
            event.GroupAdminChangeEvent, []))
        self.on_notice("group_decrease")(self.__make_event_handler(
            event.GroupMemberDecreaseEvent, []))
        self.on_notice("group_increase")(self.__make_event_handler(
            event.GroupMemberIncreaseEvent, []))
        self.on_notice("group_ban")(self.__make_event_handler(
            event.GroupBanEvent, []))
        self.on_notice("friend_add")(self.__make_event_handler(
            event.FriendAddEvent, []))
        self.on_request("friend")(self.__make_event_handler(
            event.FriendAddRequestEvent, ["approve", "remark"]))
        self.on_request("group")(self.__make_event_handler(
            event.GroupInviteOrAddRequestEvent, ["approve", "reason"]))

    def __load_plugins(self):
        plugin_base_dir = self.app_root/"plugins_new"
        # 加载插件
        sys.path.append(str(os.path.abspath(plugin_base_dir)))
        self.logger.info("Loading plugins..")
        for plugin_dir in os.listdir(plugin_base_dir):
            plugin_id = plugin_dir
            current_plugin = plugin_base_dir/plugin_dir
            if not os.path.isdir(current_plugin):
                self.logger.debug(f"Ignored {current_plugin}: not a directory")
                continue
            if not os.path.exists(current_plugin/"plugin.py"):
                # print(f"{current_plugin} 不存在plugin.py,已忽略")
                self.logger.debug(
                    f"Ignored {current_plugin}: not provide  'plugin.py'")
                continue
            plugin_module = importlib.import_module(f"{plugin_id}.plugin")
            if not hasattr(plugin_module, "get_plugin_class"):
                # print(f"{plugin_id} 不存在get_plugin_class")
                self.logger.debug(
                    f"Ignored {current_plugin}: not provide 'get_plugin_class()'")
                continue
            self.logger.info(f"Loaded plugin: {plugin_id}")
            plugin_class = plugin_module.get_plugin_class()
            if not plugin_class or not issubclass(plugin_class, Plugin):
                self.logger.info(
                    f"Ignored {current_plugin}: not providing a valid Plugin class")
                continue
            plugin_config_class = plugin_module.get_config_class() if hasattr(
                plugin_module, "get_config_class") else ConfigBase
            plugin_meta: PluginMeta = plugin_module.get_plugin_meta() if hasattr(
                plugin_module, "get_plugin_meta") else PluginMeta("unknown", 1.0, "")
            plugin_config = plugin_config_class()
            if plugin_config_class:
                if os.path.exists(current_plugin/"config.py"):
                    plugin_config = load_from_file(
                        current_plugin/"config.py", plugin_config_class)
            plugin: Plugin = plugin_class(
                event_manager=self.event_manager,
                command_manager=self.command_manager,
                state_manager=self.state_manager,
                schedule_loop_manager=self.loop_manager,
                plugin_base_dir=current_plugin,
                plugin_id=plugin_id,
                plugin_meta=plugin_meta,
                config=plugin_config,
                bot=self
            )
            self.logger.info(f"Enabling {plugin_id} ")
            plugin.on_enable()
            self.plugins.append(plugin)
            self.logger.info(f"Loaded {plugin_id} successfully")
        self.base_plugin_wrapper = Plugin(
            self.event_manager,
            self.command_manager,
            self.state_manager,
            self.schedule_loop_manager,
            self.app_root,
            "<base>",
            PluginMeta("officeyutong", 2.0, "Bot内置功能"),
            self
        )

    def __init_logger(self):
        log_path = self.app_root/"logs" / (datetime.datetime.strftime(
            datetime.datetime.now(), "%Y-%m-%d"))
        if not os.path.exists(log_path) or not os.path.isdir(log_path):
            os.makedirs(log_path)
        # Logger
        formatter = logging.Formatter(
            '[%(name)s][%(levelname)s][%(asctime)s]: %(message)s')
        log_file = log_path / \
            (datetime.datetime.strftime(
                datetime.datetime.now(), "%Y-%m-%d %H-%M-%S")+".log")
        # if not os.path.exists(log_file):
        # os.tou
        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )
        stdout_handler = logging.StreamHandler(sys.__stdout__)
        file_handler.setFormatter(formatter)
        stdout_handler.setFormatter(formatter)
        # 输出到日志
        self.logger.addHandler(
            file_handler
        )
        self.logger.addHandler(
            stdout_handler
        )
        # self.logger.addFilter()
        sys.stdout

    def init(self):
        """
        初始化CountdownBot，此函数会进行以下操作:
        - 初始化Logger
        - 加载插件并调用on_enable函数
        - 注册内置命令,初始化内部事件监听器(用以处理基础事件)
        - 初始化协程池
        - 连接数据库
        """
        # self.db_conn = sqlite3.connect("data.db", check_same_thread=False)
        self.__init_logger()
        self.logger.info("Starting Countdown-Bot 2")
        self.logger.info(f"Base dir: {self.app_root}")
        self.__load_plugins()
        self.__init_events()
        commands_count = sum((
            len(x) for x in self.command_manager.commands.values()
        ))
        listeners_count = sum((
            len(x) for x in self.event_manager.events.values()
        ))

        self.logger.info(
            f"{commands_count} group commands, {len(self.command_manager.console_commands)} console commands, {len(self.plugins)} plugins, {listeners_count} listeners, {len(self.state_manager.state_callers)} states")
        # self.on_message()(self.message_handler)

        self.loop_thread = Thread(
            target=lambda: self.loop.run_forever())
        self.input_thread = Thread(target=self.input_handler)

        self.command_manager.register_command(Command(
            plugin_id="<base>",
            command_name="stop",
            handler=console_stop_command,
            plugin=self.base_plugin_wrapper,
            help_string="关闭Bot",
            available_chats=None,
            alias=None,
            is_console=True
        ))
        self.command_manager.register_command(Command(
            plugin_id="<base>",
            command_name="help",
            handler=console_help_command,
            plugin=self.base_plugin_wrapper,
            help_string="查看帮助",
            available_chats=None,
            alias=None,
            is_console=True
        ))
        self.command_manager.register_command(Command(
            plugin_id="<base>",
            command_name="help",
            handler=help_command,
            plugin=self.base_plugin_wrapper,
            help_string="查看帮助 | help [插件ID(可选)]",
            available_chats={ChatType.discuss,
                             ChatType.private, ChatType.group},
            alias=["帮助"],
            is_console=False
        ))
        self.command_manager.register_command(Command(
            plugin_id="<base>",
            command_name="status",
            handler=status_command,
            plugin=self.base_plugin_wrapper,
            help_string="查看Bot运行状态",
            available_chats={ChatType.discuss,
                             ChatType.private, ChatType.group},
            alias=["状态"],
            is_console=False
        ))
        self.command_manager.register_command(Command(
            plugin_id="<base>",
            command_name="plugins",
            handler=plugins_command,
            plugin=self.base_plugin_wrapper,
            help_string="查看插件列表",
            available_chats={ChatType.discuss,
                             ChatType.private, ChatType.group},
            alias=["插件"],
            is_console=False
        ))
        self.command_manager.register_command(Command(
            plugin_id="<base>",
            command_name="about",
            handler=about_command,
            plugin=self.base_plugin_wrapper,
            help_string="关于",
            available_chats={ChatType.discuss,
                             ChatType.private, ChatType.group},
            alias=["关于"],
            is_console=False
        ))

    def __future_exception_handler(self, future: Union[asyncio.Future, concurrent.futures.Future]):
        exc = future.exception()
        if exc:
            import traceback
            # traceback.print_exc()

            # self.logger.error(traceback.format_exception(value=exc))

            raise exc
            # self.logger.info(traceback.format_exc())

    def start(self):
        """
        启动CountdownBot
        - 启动协程池
        - 启动Schedule Loops
        - 启动控制台输入线程
        - 运行Flask
        """

        self.logger.info("Starting schedule loops..")
        # self.loop.set_exception_handler()
        # self.loop.set_debug(True)
        # self.loop.set_exception_handler(
        #     self.__loop_exception_handler
        # )
        self.loop_thread.start()
        for item in self.loop_manager.tasks:
            asyncio.run_coroutine_threadsafe(item, self.loop).add_done_callback(
                self.__future_exception_handler)
        self.input_thread.start()
        self.run(
            host=self.config.POST_ADDRESS,
            port=self.config.POST_PORT,
            **self.flask_args
        )

    def input_handler(self):
        while True:
            try:
                string = input(">").strip()
                splited = string.split(" ")
                command_name, args = splited[0], splited[1:]
                if command_name not in self.command_manager.console_commands:
                    self.logger.info(f"Unknown command: {command_name}")
                    continue
                self.command_manager.console_commands[command_name].invoke(
                    args=args,
                    raw_string=string,
                    context=None,
                    event=None
                )
            except (KeyboardInterrupt, EOFError):
                self.stop()
            except Exception as ex:
                import traceback
                traceback.print_exc(ex)

    def stop(self):
        """
        停止CountdownBot
        """
        self.logger.info("Shutting down..")

        for plugin in self.plugins:
            self.logger.info(f"Disabling {plugin.plugin_id}")
            plugin.on_disable()
        # self.db_conn.close()
        self.loop.call_soon_threadsafe(self.loop.stop)
        stop_thread(self.input_thread)
        os.kill(os.getpid(), 1)

    def submit_async_task(self, coro):
        """
        提交异步任务至协程池
        @param coro: coroutine对象
        @return: Future对象,异常会被自动处理
        """
        self.logger.info(f"Submitted async task {coro}")
        future = asyncio.run_coroutine_threadsafe(
            coro, self.loop
        )
        future.add_done_callback(self.__future_exception_handler)
        return future

    def submit_multithread_task(self, fn: Callable[[], Any], handle_exception=True, /, *args, **kwargs):
        """
        提交同步任务至线程池
        @param fn: Callable对象
        @param args,kwargs: 调用fn时传递的参数
        @return: Future对象,异常会被自动处理
        """
        self.logger.info(f"Submitted multithread task {fn}")
        future = self.thread_pool.submit(
            fn, *args, **kwargs
        )
        self.logger.debug(f"handle exception: {handle_exception}")
        if handle_exception:
            future.add_done_callback(self.__future_exception_handler)
        return future

    def __fill_dict(self, dic: dict, evt, val):
        if getattr(evt, val) is not None:
            dic[val] = getattr(evt, val)

    def __make_event_handler(self, event_class, reply_keys: Iterable[str]) -> Callable[[dict], dict]:
        def wrapper(context: dict) -> dict:
            evt = event_class(context)
            self.logger.debug(f"Base event received...{context['post_type']}")
            self.event_manager.process_event(evt)
            result: Dict[str, Any] = {}
            for key in reply_keys:
                self.__fill_dict(result, evt, key)
            return result
        return wrapper
