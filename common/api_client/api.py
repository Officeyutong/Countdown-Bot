from typing import Any, Callable, Union, Literal
from concurrent.futures import Future
from .datatypes import *


class ClientWrapper:
    def __init__(self, invoker: [[str, dict], Future]):
        self.invoker = invoker

    def send_private_msg(self, user_id: int, message: Union[str, dict], auto_escape: bool = False) -> int:
        local_vars = locals()
        del local_vars["self"]
        return self.invoker("send_private_msg", local_vars)

    def send_group_msg(self, group_id: int, message: Union[str, dict], auto_escape: bool = False) -> int:
        local_vars = locals()
        del local_vars["self"]
        return self.invoker("send_group_msg", local_vars)

    def send_discuss_msg(self, discuss_id: int, message: Union[str, dict], auto_escape: bool = False) -> int:
        local_vars = locals()
        del local_vars["self"]
        return self.invoker("send_discuss_msg", local_vars)

    def send_msg(self, message: Union[str, dict], message_type: str = "", discuss_id: int = -1, user_id: int = -1, group_id: int = -1, auto_escape: bool = False) -> int:
        local_vars = locals()
        del local_vars["self"]
        return self.invoker("send_msg", local_vars)

    def delete_msg(self, message_id: int):
        local_vars = locals()
        del local_vars["self"]
        return self.invoker("delete_msg", local_vars)

    def send_like(self, user_id: int, times: int = -1):
        local_vars = locals()
        # del local_vars["self"]
        del local_vars["self"]
        return self.invoker("send_like", local_vars)

    def send(self, context: dict, message: Union[str, dict], auto_escape: bool = False):
        message_type = context["message_type"]
        mapping = {
            "private": ("user_id"),
            "discuss": ("discuss_id"),
            "group": ("group_id")
        }
        print(context)
        return self.send_msg(message=message,
                             auto_escape=auto_escape,
                             message_type=message_type,
                             **{mapping[message_type]: context[mapping[message_type]]}
                             )

    def get_stranger_info(self, user_id: int, no_cache: bool = False):
        local_vars = locals()
        # del local_vars["self"]
        del local_vars["self"]
        return self.invoker("get_stranger_info", local_vars)

    def get_group_info(self, group_id: int, no_cache: bool = False):
        local_vars = locals()
        # del local_vars["self"]
        del local_vars["self"]
        return self.invoker("get_group_info", local_vars)

    def get_group_member_list(self, group_id: int):
        local_vars = locals()
        # del local_vars["self"]
        del local_vars["self"]
        return self.invoker("get_group_member_list", local_vars)

    def __getattribute__(self, name: str) -> Any:
        if hasattr(self, name):
            return getattr(self, name)
        else:
            def wrapper(self,  **kwargs) -> Any:
                return self.invoker(name,  kwargs)
            return wrapper