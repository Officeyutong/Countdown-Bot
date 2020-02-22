from global_vars import VARS
from cqhttp import CQHttp
from util import print_log
from register import message_listener
from util import print_log
import importlib
import global_vars
config = global_vars.CONFIG[__name__]
last_message: dict = None
repeat_time: dict = None


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "复读机."
    }


def load():
    VARS["repeater_last_message"] = dict()
    VARS["repeater_repeat_time"] = dict()
    global last_message, repeat_time
    last_message = VARS["repeater_last_message"]
    repeat_time = VARS["repeater_repeat_time"]


@message_listener
def repeat_handler(bot: CQHttp, context, message):
    group = context["group_id"]
    global last_message, repeat_time
    if group not in last_message:
        last_message[group] = None
        repeat_time[group] = 0
    if message == last_message[group]:
        repeat_time[group] += 1
    else:
        last_message[group] = message
        repeat_time[group] = 1
    if repeat_time[group] >= config.REPEAT_TIME_LIMIT:
        print(f"Repeating {message}")
        bot.send(context, message)
        repeat_time[group] = 0
        last_message[group] = None
