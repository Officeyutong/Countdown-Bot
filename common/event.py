from abc import abstractmethod
from typing import List, Callable, Mapping, Set, TypeVar


class EventBase:
    def __init__(self):
        self.cancelled = False


class MessageEvent(EventBase):
    def __init__(self, message: str, context: dict):
        super().__init__()
        self.message = message
        self.context = context


EventCallback = Callable[[EventBase], None]


class Listener:
    pass


class EventManager:

    def __init__(self):
        self.events: Mapping[EventBase, Set[EventCallback]] = {}

    def process_event(self, event: EventBase):
        for func in self.events.get(event.__class__, []):
            func(event)
            if event.cancelled:
                break

    def register_event(self, event, callback: EventCallback):
        if callback in self.events.get(event, []):
            raise ValueError(f"事件 {event} 的处理函数 {callback} 已经注册")
        if event not in self.events:
            self.events[event] = {callback}
        else:
            self.events[event].add(callback)

    def unregister_event(self, event, callback):
        if event not in self.events or callback not in self.events[event]:
            raise NameError(f"未注册的对于事件 {event} 的监听器: {callback}")
        self.events[event].remove(callback)
