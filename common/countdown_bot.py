from cqhttp import CQHttp
from pathlib import Path
from .plugin import Plugin
from .event import EventManager, MessageEvent
from .command import CommandManager, Command
from .state import StateManager
from .config_loader import ConfigBase, load_from_file
from typing import List
from .datatypes import PluginMeta
from .loop import ScheduleLoopManager
from .utils import stop_thread
from threading import Thread
import sys
import os
import importlib
import asyncio
import signal
import logging
import datetime
import sys


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


class CountdownBot(CQHttp):
    def __init__(self, app_root: Path, **flask_args):
        self.app_root = app_root
        self.__config = load_from_file(
            self.app_root/"config.py", CountdownBotConfig)
        super().__init__(self.config.API_URL,
                         self.config.ACCESS_TOKEN, self.config.SECRET)
        self.plugins: List[Plugin] = []
        self.event_manager = EventManager()
        self.state_manager = StateManager()
        self.command_manager = CommandManager()
        self.loop_manager = ScheduleLoopManager(
            self.config.CHECK_INTERVAL, self.config.EXECUTE_DELAY, self)
        self.flask_args = flask_args
        self.__logger = logging.Logger(
            "CountdownBot"
        )

    @property
    def logger(self) -> logging.Logger:
        return self.__logger

    @property
    def config(self) -> CountdownBotConfig:
        return self.__config

    def __load_plugins(self):
        # 加载插件
        sys.path.append(str(os.path.abspath(self.app_root/"plugins")))
        self.logger.info("Loading plugins..")
        for plugin_dir in os.listdir(self.app_root/"plugins"):
            plugin_id = plugin_dir
            current_plugin = self.app_root/"plugins"/plugin_dir
            if not os.path.isdir(current_plugin):
                self.logger.debug(f"Ignored {current_plugin}: not a directory")
                continue
            if not os.path.exists(current_plugin/"plugin.py"):
                # print(f"{current_plugin} 不存在plugin.py,已忽略")
                self.logger.debug(
                    f"Ignored {current_plugin}: doesn't has a 'plugin.py'")

                continue
            plugin_module = importlib.import_module(f"{plugin_id}.plugin")
            if not hasattr(plugin_module, "get_plugin_class"):
                # print(f"{plugin_id} 不存在get_plugin_class")
                self.logger.debug(
                    f"Ignored {current_plugin}: doesn't has 'get_plugin_class()'")
                continue
            self.logger.info(f"Loaded plugin: {plugin_id}")
            plugin_class = plugin_module.get_plugin_class()
            plugin_config_class = plugin_module.get_config_class() if hasattr(
                plugin_module, "get_config_class") else None
            plugin_meta: PluginMeta = plugin_module.get_plugin_meta() if hasattr(
                plugin_module, "get_plugin_meta") else PluginMeta("unknown", 1.0, "")
            plugin_config = ConfigBase()
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

    def init(self):
        self.__init_logger()
        self.logger.info("Starting Countdown-Bot 2")
        self.__load_plugins()

        commands_count = sum((
            len(x) for x in self.command_manager.commands.values()
        ))
        listeners_count = sum((
            len(x) for x in self.event_manager.events.values()
        ))

        self.logger.info(
            f"{commands_count} group commands, {len(self.command_manager.console_commands)} console commands, {len(self.plugins)} plugins, {listeners_count} listeners, {len(self.state_manager.state_callers)} states")
        self.on_message()(self.message_handler)
        self.loop = asyncio.get_event_loop()
        self.input_thread = Thread(target=self.input_handler)
        self.command_manager.register_command(
            Command(
                "<base>", "stop", self.__console_stop_command, None, "关闭Bot", is_console=True
            )
        )
        self.command_manager.register_command(
            Command(
                "<base>", "help", self.__console_help_command, None, "查看帮助", is_console=True
            )
        )
        self.command_manager.register_command(
            Command(
                "<base>", "post", self.__console_post_message_event, None, "模拟消息事件 | post <消息内容>", is_console=True
            )
        )

    def __coroutine_exception_handler(self, future: asyncio.Future):
        exc = future.exception()
        if exc:
            raise exc

    def start(self):
        self.loop_thread = Thread(
            target=lambda: self.loop.run_forever())
        self.logger.info("Starting schedule loops..")
        # self.loop.set_exception_handler()
        # self.loop.set_debug(True)
        self.loop.set_exception_handler(
            self.__loop_exception_handler
        )
        self.loop_thread.start()
        for item in self.loop_manager.tasks:
            asyncio.run_coroutine_threadsafe(item, self.loop).add_done_callback(
                self.__coroutine_exception_handler)
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
            except (KeyboardInterrupt, EOFError):
                self.stop()
            except Exception as ex:
                import traceback
                traceback.print_exc(ex)
            splited = string.split(" ")
            command_name, args = splited[0], splited[1:]
            if command_name not in self.command_manager.console_commands:
                self.logger.info(f"Unknown command: {command_name}")
                continue
            self.command_manager.console_commands[command_name].invoke(
                args, string, None
            )

    def message_handler(self, context: dict):
        self.logger.debug(context)

    def stop(self):
        self.logger.info("Shutting down..")
        self.loop.call_soon_threadsafe(self.loop.stop)
        stop_thread(self.input_thread)
        os.kill(os.getpid(), 1)

    def submit_async_task(self, coro):
        self.logger.info(f"Submitted async task {coro}")
        asyncio.run_coroutine_threadsafe(
            coro, self.loop
        ).add_done_callback(self.__coroutine_exception_handler)

    def __console_stop_command(self, plugin, args: List[str], raw_string: str, context):
        self.stop()

    def __console_help_command(self, plugin, args: List[str], raw_string: str, context):
        for k, v in sorted(self.command_manager.console_commands.items(), key=lambda x: x[0]):
            self.logger.info(f"{k} --- {v.help_string}")

    def __console_post_message_event(self, plugin, args: List[str], raw_string, context):
        self.event_manager.process_event(
            MessageEvent(args[0], {})
        )
