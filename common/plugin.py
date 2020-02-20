from functools import wraps
from .event import EventBase, Listener, EventManager, EventCallback
from .command import CommandManager, Command, CommandHandler
from typing import Callable, Set, Tuple, NoReturn, Type, Optional, Iterable
from .datatypes import PluginMeta
from .config_loader import ConfigBase
from .state import StateManager, StateHandler
from abc import abstractclassmethod
from pathlib import Path


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
                 plugin_base_dir: Path,
                 plugin_id: str,
                 plugin_meta: PluginMeta,
                 bot: '.countdown_bot.CountdownBot',  # type: .countdown_bot.CountdownBot
                 config: Optional[ConfigBase]
                 ):
        self.__event_listeners: Set[Tuple[EventBase, EventCallback]] = set()
        self.event_manager = event_manager
        self.plugin_base_dir = plugin_base_dir
        self.__config = config
        self.command_manager = command_manager
        self.__plugin_id = plugin_id
        self.state_manager = state_manager
        self.__plugin_meta = plugin_meta
        self.__bot = bot # type: .countdown_bot.CountdownBot

    @property
    def bot(self) -> ".countdown_bot.CountdownBot": # type: .countdown_bot.CountdownBot
        return self.__bot

    @property
    def plugin_meta(self) -> PluginMeta:
        return self.__plugin_meta

    @property
    def data_dir(self) -> Path:
        return self.plugin_base_dir/"data"

    @property
    def listeners(self) -> Set[Tuple[EventBase, EventCallback]]:
        return self.__event_listeners

    @property
    def plugin_id(self) -> str:
        return self.__plugin_id
    @property
    def config(self):
        return self.__config

    def register_event_listener(self, event: EventBase, callback: EventCallback) -> NoReturn:
        self.__event_listeners.add((event, callback))
        self.event_manager.register_event(event, callback)

    # def unregister_event_listsner(self, event: EventBase, callback: EventCallback) -> NoReturn:
    #     self.__event_listeners.remove((event, callback))
    #     self.event_manager.unregister_event(event, callback)

    def register_all_event_listeners(self, listener_class_instance: Listener) -> NoReturn:
        for func in dir(listener_class_instance):
            item = getattr(listener_class_instance, func)
            if not func.startswith("__") and callable(item):
                annotations = item.__annotations__
                if len(annotations) == 1:
                    event_type = list(annotations.values())[0]
                    if issubclass(event_type, EventBase):
                        self.register_event_listener(event_type, item)

    def wrap_command(self, command_name: str, command_handler: CommandHandler, help_string: str, alias: Optional[Iterable[str]] = None) -> Command:
        return (Command(
            self.__plugin_id, command_name, command_handler, self, help_string, alias
        ))

    def register_command(self, command: Command) -> NoReturn:
        self.command_manager.register_command(command)

    def register_state_handler(self, state_handler: StateHandler) -> NoReturn:
        self.state_manager.register_state_caller(state_handler)

    def on_load(self) -> NoReturn:
        pass

    def on_disable(self) -> NoReturn:
        pass
        # for event, callback in self.__event_listeners:
        #     self.unregister_event_listsner(event, callback)
