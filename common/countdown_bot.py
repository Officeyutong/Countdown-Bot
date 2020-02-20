from cqhttp import CQHttp
from pathlib import Path
from .plugin import Plugin
from .event import EventManager
from .command import CommandManager
from .state import StateManager
from .config_loader import ConfigBase, load_from_file
from typing import List
from .datatypes import PluginMeta
import sys
import os
import importlib


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


class CountdownBot(CQHttp):
    def __init__(self, app_root: Path):
        self.app_root = app_root
        self.__config = load_from_file(
            self.app_root/"config.py", CountdownBotConfig)
        super().__init__(self.config.API_URL,
                         self.config.ACCESS_TOKEN, self.config.SECRET)
        self.plugins: List[Plugin] = []
        self.event_manager = EventManager()
        self.state_manager = StateManager()
        self.command_manager = CommandManager()

    @property
    def config(self) -> CountdownBotConfig:
        return self.__config

    def init(self):
        # 加载插件
        sys.path.append(str(os.path.abspath(self.app_root/"plugins")))
        print("加载插件中")
        for plugin_dir in os.listdir(self.app_root/"plugins"):
            plugin_id = plugin_dir
            current_plugin = self.app_root/"plugins"/plugin_dir
            if not os.path.isdir(current_plugin):
                # print(f"{current_plugin} 不是目录,已忽略")
                continue
            if not os.path.exists(current_plugin/"plugin.py"):
                # print(f"{current_plugin} 不存在plugin.py,已忽略")
                continue
            plugin_module = importlib.import_module(f"{plugin_id}.plugin")
            if not hasattr(plugin_module, "get_plugin_class"):
                # print(f"{plugin_id} 不存在get_plugin_class")
                continue
            print(f"加载插件 {plugin_id}")
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
                plugin_base_dir=current_plugin,
                plugin_id=plugin_id,
                plugin_meta=plugin_meta,
                config=plugin_config,
                bot=self
            )
            print(f"启用插件 {plugin_id} 中")
            plugin.on_load()
            self.plugins.append(plugin)
            print(f"插件 {plugin_id} 加载完成")
        commands_count = sum((
            len(x) for x in self.command_manager.commands.values()
        ))
        listeners_count = sum((
            len(x) for x in self.event_manager.events.values()
        ))

        print(
            f"共加载 {commands_count} 个命令, {len(self.plugins)} 个插件, {listeners_count} 个监听器, {self.state_manager.state_callers} 个状态管理器")

    def start(self):
        pass
