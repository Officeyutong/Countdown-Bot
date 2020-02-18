from global_vars import registered_commands as commands
from register import command
from util import print_log
from threading import Thread
from cqhttp import CQHttp
import ctypes
import inspect
import os
import re
import tempfile
import time
import docker
import util
import global_vars
from typing import List
config = global_vars.CONFIG[__name__]


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "简单随机数生成器"
    }


@command(name="rand", help="生成随机数.rand 随机上限 数量(可省略)")
def simple_rand(bot: CQHttp, context: dict = None, args: List[str] = None) -> None:
    while args and args[-1].strip() == "":
        del args[-1]
    try:
        upper, *other = (int(x) for x in args[1:])
    except Exception as ex:
        bot.send(context, "请输入合法参数")
        raise ex
        # return
    # print(other, upper)
    if not other:
        count = 1
    else:
        count = other[0]
    if count > config.MAX_NUMBER_COUNT:
        bot.send(context, "您输入的数值过大")
        return
    # print(upper, count)
    from io import StringIO
    from random import randint
    buf = StringIO()
    buf.write("随机数结果:\n")
    for x in range(count):
        buf.write(f"{randint(1,upper)}\n")
    # print(buf.getvalue())
    # print(buf.getvalue())

    bot.send(context, buf.getvalue())
