from abc import abstractmethod
from typing import List, Callable, Mapping, Set, TypeVar, Optional, Type, Any, Dict
from dataclasses import dataclass
from enum import Enum


class EventBase:
    def __init__(self):
        self.cancelled = False

    def __repr__(self):
        return str(self.__dict__)


class MessageEvent(EventBase):
    def __init__(self, context: dict):
        super().__init__()
        self.context = context
        self.post_type = context["post_type"]
        self.message_id: int = context.get("message_id", None)
        self.user_id: int = context.get("user_id", None)
        self.message: Optional[str] = context.get("message", None)
        self.raw_message: str = context.get("raw_message", None)
        self.font: int = context.get("font", None)


class PrivateMessageSubtype(Enum):
    friend = "friend"
    group = "group"
    discuss = "discuss"
    other = "other"


class GroupMessageSubtype(Enum):
    normal = "normal"
    anonymous = "anonymous"
    notice = "notice"


class GroupMemberRole(Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class NoticeType(Enum):
    group_upload = "group_upload"
    group_admin = "group_admin"
    group_increase = "group_increase"
    group_decrease = "group_decrease"
    group_ban = "group_ban"
    friend_add = "friend_add"
    friend = "friend"


class GroupAdminChangeType(Enum):
    set = "set"
    unset = "unset"


class GroupMemberDecreaseType(Enum):
    leave = "leave"
    kick = "kick"
    kick_me = "kick_me"


class GroupMemberIncreaseType(Enum):
    approve = "approve"
    invite = "invite"


class GroupBanType(Enum):
    ban = "ban"
    lift_ban = "lift_ban"


class RequestType(Enum):
    friend = "friend"
    group = "group"


class GroupJoinType(Enum):
    add = "add"
    invite = "invite"


@dataclass
class SimpleMessageSender:
    user_id: int
    nickname: str
    sex: str
    age: int

    def __init__(self, val: dict):
        self.user_id = val.get("user_id", None)
        self.nickname = val.get("nickname", None)
        self.sex = val.get("sex", None)
        self.age = val.get("age", None)


@dataclass
class GroupAnonymousSender:
    id: int
    name: str
    flag: str

    def __init__(self, val: dict):
        self.id = val.get("id", None)
        self.name = val.get("name", None)
        self.flag = val.get("flag", None)


@dataclass
class GroupMessageSender:
    user_id: int
    nickname: str
    card: str
    sex: str
    age: int
    area: str
    level: str
    role: Optional[GroupMemberRole]
    title: str

    def __init__(self, val: dict):
        self.user_id = val.get("user_id", None)
        self.nickname = val.get("nickname", None)
        self.card = val.get("card", None)
        self.sex = val.get("sex", None)
        self.age = val.get("age", None)
        self.area = val.get("area", None)
        self.level = val.get("level", None)
        self.role = GroupMemberRole(
            val["role"]) if val.get("role", None) else None
        self.title = val.get("title", None)


class PrivateMessageEvent(MessageEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.sub_type: Optional[PrivateMessageSubtype] = PrivateMessageSubtype(
            context["sub_type"]) if context.get("sub_type", None) else None

        self.sender: Optional[SimpleMessageSender] = SimpleMessageSender(
            context["sender"]) if context.get("sender", None) else None
        self.anonymous: Optional[GroupAnonymousSender] = GroupAnonymousSender(
            context["anonymous"]) if context.get("anonymous", None) else None
        self.reply = None
        self.auto_escape = None


class GroupMessageEvent(MessageEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.sub_type: Optional[GroupMessageSubtype] = GroupMessageSubtype(
            context["sub_type"]) if context.get("sub_type", None) else None
        self.group_id: int = context.get("group_id", None)
        self.sender: Optional[SimpleMessageSender] = SimpleMessageSender(
            context["sender"]) if context.get("sender", None) else None
        self.reply: Optional[str] = None
        self.auto_escape: Optional[bool] = None
        self.at_sender: Optional[bool] = None
        self.delete: Optional[bool] = None
        self.kick: Optional[bool] = None
        self.ban: Optional[bool] = None
        self.ban_duration: Optional[int] = None


class DiscussMessageEvent(MessageEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.sub_type = "discuss"
        self.discuss_id: Optional[int] = context.get("discuss_id", None)
        self.sender: Optional[SimpleMessageSender] = SimpleMessageSender(
            context["sender"]) if context.get("sender", None) else None
        self.reply: Optional[str] = None
        self.auto_escape: Optional[bool] = None
        self.at_sender: Optional[bool] = None


class NoticeEvent(EventBase):
    def __init__(self, context: dict):
        super().__init__()
        self.notice_type = NoticeType(context["notice_type"])


@dataclass
class GroupFile:
    id: str
    name: str
    size: str  # bytes
    busid: str

    def __init__(self, val: dict):
        self.id = val["id"]
        self.name = val["name"]
        self.size = val["size"]
        self.busid = val["busid"]


class GroupFileUploadEvent(NoticeEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.group_id: int = context["group_id"]
        self.user_id: int = context["user_id"]
        self.file = GroupFile(context["file"])


class GroupAdminChangeEvent(NoticeEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.sub_type = GroupAdminChangeType(context["sub_type"])
        self.group_id: int = context["group_id"]
        self.user_id: int = context["user_id"]


class GroupMemberDecreaseEvent(NoticeEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.sub_type = GroupMemberDecreaseType(context["sub_type"])
        self.group_id: int = context["group_id"]
        self.user_id: int = context["user_id"]
        self.operator_id: int = context["operator_id"]


class GroupMemberIncreaseEvent(NoticeEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.sub_type = GroupMemberIncreaseType(context["sub_type"])
        self.group_id: int = context["group_id"]
        self.user_id: int = context["user_id"]
        self.operator_id: int = context["operator_id"]


class GroupBanEvent(NoticeEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.sub_type = GroupBanType(context["sub_type"])
        self.group_id: int = context["group_id"]
        self.user_id: int = context["user_id"]
        self.operator_id: int = context["operator_id"]
        self.duration: int = context["duration"]


class FriendAddEvent(NoticeEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.user_id: int = context["user_id"]


class RequestEvent(EventBase):
    def __init__(self, context: dict):
        super().__init__()
        self.request_type = RequestType(context["request_type"])


class FriendAddRequestEvent(RequestEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.user_id: int = context["user_id"]
        self.comment: str = context["comment"]
        self.flag: str = context["flag"]
        self.approve: Optional[bool] = None
        self.remark: Optional[str] = None


class GroupInviteOrAddRequestEvent(RequestEvent):
    def __init__(self, context: dict):
        super().__init__(context)
        self.user_id: int = context["user_id"]
        self.comment: str = context["comment"]
        self.flag: str = context["flag"]
        self.group_id: int = context["group_id"]
        self.sub_type = GroupJoinType(context["sub_type"])
        self.approve: Optional[bool] = None
        self.reason: Optional[str] = None


    # def set_reply()
EventCallback = Callable[[EventBase], None]


class Listener:
    pass


class EventManager:

    def __init__(self, bot):
        self.events: Dict[Any, Set[EventCallback]] = {}
        self.bot = bot

    def process_event(self, event: EventBase):
        self.bot.logger.debug(f"Processing event type = {type(event)}")
        for event_type, listeners in self.events.items():
            if issubclass(type(event), event_type):
                self.bot.logger.debug(
                    f"Processing event {event.__class__} for listener type: {event_type}")
                for func in listeners:
                    func(event)
                    if event.cancelled:
                        self.bot.logger.debug(f"Event {event} cancelled")
                        break

    def register_event(self, event, callback: EventCallback):
        if callback in self.events.get(event, []):
            raise ValueError(f"事件 {event} 的处理函数 {callback} 已经注册")
        self.bot.logger.debug(
            f"Registering event {event} with callback {callback}")
        if event not in self.events:
            self.events[event] = {callback}
        else:
            self.events[event].add(callback)

    def unregister_event(self, event, callback):
        if event not in self.events or callback not in self.events[event]:
            raise NameError(f"未注册的对于事件 {event} 的监听器: {callback}")
        self.events[event].remove(callback)
