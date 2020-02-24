from cqhttp import CQHttp
from util import print_log
from register import command, schedule_loop, console_command
from global_vars import registered_commands as commands
from global_vars import config as global_config
from global_vars import CONFIG
import re
import util
import global_vars


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "倒计时Bot的基本功能."
    }


@command(name="help", help="查看帮助")
def help(bot: CQHttp, context=None, args=None):
    bot.send(context, "\n".join(
        map(lambda x: x[0]+" --- "+x[1][0], sorted(commands.items(), key=lambda x: x[0]))))


@command(name="status", help="查看Bot运行状态")
def show_status(bot: CQHttp, context, args):
    to_send =\
        """倒计时广播时间: {broadcast_hour:0>2d}:{broadcast_minute:0>2d}
Hitokoto广播时间: {hitokoto_hour:0>2d}:{hitokoto_minute:0>2d}
指令前缀: {command_prefix}
输入 [指令前缀]help 查看帮助""".format(
            broadcast_hour=CONFIG["plugins.broadcast.broadcast"].BROADCAST_HOUR, broadcast_minute=CONFIG["plugins.broadcast.broadcast"].BROADCAST_MINUTE,
            hitokoto_hour=CONFIG["plugins.hitokoto.hitokoto"].HITOKOTO_HOUR, hitokoto_minute=CONFIG["plugins.hitokoto.hitokoto"].HITOKOTO_MINUTE,
            command_prefix="".join(
                map(lambda x: x+" ", global_config.COMMAND_PREFIX)),
        )
    bot.send(context, to_send)


@command(name="plugins", help="查看插件列表")
def plugins(bot: CQHttp, context, args):
    def make_msg(obj):
        name, detail = obj
        msg = """%s\n""" % name
        if "description" in detail:
            msg += detail["description"]+"\n"
        if "author" in detail:
            msg += "作者:"+detail["author"]+"\n"
        if "version" in detail:
            msg += "版本:{}\n".format(detail["version"])
        return msg+"\n"
    bot.send(context, "".join(
        map(lambda obj: make_msg(obj), global_vars.loaded_plugins.items())))


# @console_command(name="reload", help="重新加载配置文件")
# def reload_config(args):
#     import importlib
#     global global_config
#     global_config = importlib.reload(global_config)
#     for item in dir(global_config):
#         if item.startswith("__"):
#             continue
#         print("%s = %s" % (item, getattr(global_config, item)))


# @console_command(name="broadcast", help="在所有此Bot所在的群里广播消息")
# def broadcast_message(args):
#     from io import StringIO
#     buf = StringIO()
#     for text in args[1:]:
#         buf.write(text)
#         buf.write(" ")
#     bot: CQHttp = global_vars.VARS["bot"]
#     message = buf.getvalue().strip()
#     print("Message = ", f"'{message}'")
#     for group in bot.get_group_list():
#         group_id = group["group_id"]
#         print("Sending..", group_id)
#         bot.send_message(message_type="group",
#                          group_id=group_id, message=message)


# @command(name="about", help="关于")
# def about(bot: CQHttp, context=None, args=None):
#     bot.send(context, "https://gitee.com/yutong_java/Countdown-Bot")
#     bot.send(context, "by MikuNotFoundException")


# @command(name="阿克", help="阿克")
# def ak(bot: CQHttp, context=None, args=None):
#     bot.send(context, "您阿克了！")


# @command(name="爆零", help="qwq")
# def zero(bot: CQHttp, context=None, args=None):
#     bot.send(context, "您不会爆零的qwq")


# @command(name="凉了", help="凉了?")
# def im_cold(bot: CQHttp, context=None, args=None):
#     bot.send(context, "qwq您不会凉的~")
