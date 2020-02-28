from functools import wraps
from common.event import EventBase, Listener, EventManager, EventCallback
from common.command import CommandManager, Command, CommandHandler, ChatType
from typing import Callable, Set, Tuple, NoReturn, Type, Optional, Iterable, TypeVar, Any
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.state import StateManager, StateHandler
from common.loop import ScheduleLoopManager, TimeTuple
from abc import abstractclassmethod
from pathlib import Path
import logging


def dataclass_wrapper(func):
    @wraps(func)
    def inner():
        from common.datatypes import PluginMeta
        result: PluginMeta = func()
        return {
            "author": result.author,
            "version": result.version,
            "description": result.description
        }
    return inner


class Plugin:

    def __init__(self,
                 event_manager: EventManager,
                 command_manager: CommandManager,
                 state_manager: StateManager,
                 schedule_loop_manager: ScheduleLoopManager,
                 plugin_base_dir: Path,
                 plugin_id: str,
                 plugin_meta: PluginMeta,
                 bot: Any,
                 config: Optional[ConfigBase]
                 ):
        """
        此函数不应由用户进行调用。
        """
        self.__event_listeners: Set[Tuple[EventBase, EventCallback]] = set()
        self.event_manager = event_manager
        self.plugin_base_dir = plugin_base_dir
        self.__config = config
        self.command_manager = command_manager
        self.__plugin_id = plugin_id
        self.state_manager = state_manager
        self.__plugin_meta = plugin_meta
        self.__bot = bot
        self.schedule_loop_manager = schedule_loop_manager

    @property
    def bot(self):
        """
        返回此加载此插件的Bot实例
        """
        return self.__bot

    @property
    def plugin_meta(self) -> PluginMeta:
        """
        返回此插件的元信息
        """
        return self.__plugin_meta

    @property
    def data_dir(self) -> Path:
        """
        返回此插件的数据目录。
        """
        return self.plugin_base_dir/"data"

    @property
    def listeners(self) -> Set[Tuple[EventBase, EventCallback]]:
        """
        返回此插件的已注册事件监听器
        """
        return self.__event_listeners

    @property
    def plugin_id(self) -> str:
        """
        返回此插件的插件ID
        """
        return self.__plugin_id

    @property
    def config(self):
        """
        返回此插件的配置类实例。
        配置类由插件的plugin.py中的get_config_class所指定，如果不存在此函数，则配置类为ConfigBase。
        CountdownBot会自动将插件目录下的config.py中的常量覆盖插件配置类中的默认值。
        """
        return self.__config

    @property
    def logger(self) -> logging.Logger:
        """
        返回插件所使用的Logger
        """
        return self.bot.logger

    def register_schedule_loop(self, time: TimeTuple, coro, name: str = "", init=None):
        """
        注册循环事件。
        任务开始后，CountdownBot会在每CHECK_INTERVAL秒时进行检查，并在时间为time时执行此任务，执行完成后延迟EXECUTE_DELAY秒后继续检查。
        如果init不为None，则在任务初始化时被调用。
        init 与 coro 均为coroutine对象。
        """
        self.schedule_loop_manager.register(time, coro, name, init)

    T = TypeVar("T")

    def register_event_listener(self, event: Type[T], callback: Callable[[T], None]):
        """
        注册事件监听函数。
        @param event: 要监听的事件的类
        @param callback: 事件回调函数 (plugin,)
        """
        self.__event_listeners.add((event, callback))
        self.event_manager.register_event(event, callback)

    # def unregister_event_listsner(self, event: EventBase, callback: EventCallback) -> NoReturn:
    #     self.__event_listeners.remove((event, callback))
    #     self.event_manager.unregister_event(event, callback)

    def register_all_event_listeners(self, listener_class_instance: Listener):
        """
        注册一个Listener下的所有事件监听器。
        @param listener_class_instance: 要注册的Listsner类
        Listener类下的所有只接受一个参数，并且参数类型为EventBase子类的类函数将会被视为事件监听器。
        """
        for func in dir(listener_class_instance):
            item = getattr(listener_class_instance, func)
            if not func.startswith("__") and callable(item):
                annotations = item.__annotations__
                if len(annotations) == 1:
                    event_type = list(annotations.values())[0]
                    if issubclass(event_type, EventBase):
                        self.logger.debug(
                            f"Registering event listener {event_type} : {item}")
                        self.register_event_listener(event_type, item)

    def register_command_wrapped(self, command_name: str, command_handler: CommandHandler, help_string: str, chats: Optional[Set[ChatType]], alias: Optional[Iterable[str]] = None, is_console: bool = False, is_async=False) -> Command:
        """
        注册指令。
        @param command_name: 命令名称
        @param command_handler: 命令回调函数 (plugin:Plugin,args:List[str],context:dict,event:MessageEvent)
        @param help_string: 帮助文本
        @param chats: 此命令可用的聊天环境，Set[ChatType]，对于控制台命令请留为None
        @param alias: 别名列表。控制台命令不支持别名
        @param is_console: 是否为控制台命令
        @param is_async: 是否为异步命令,如果是,command_handler应该为协程对象
        """
        self.logger.debug(command_handler)
        self.register_command(Command(
            alias=alias,
            plugin_id=self.__plugin_id,
            command_name=command_name,
            handler=command_handler,
            plugin=self,
            help_string=help_string,
            available_chats=chats,
            is_console=is_console,
            is_async=is_async

        ))

    def register_command(self, command: Command):
        """注册命令"""
        self.command_manager.register_command(command)

    def register_state_handler(self, state_handler: StateHandler):
        """
        注册状态处理器。
        用于在status指令时调用，返回状态文本。
        """
        self.state_manager.register_state_caller(state_handler)

    def on_enable(self):
        """
        插件被启用时调用
        """
        pass

    def on_disable(self) -> NoReturn:
        """
        插件被卸载时调用
        """
        pass
        # for event, callback in self.__event_listeners:
        #     self.unregister_event_listsner(event, callback)
