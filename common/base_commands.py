from typing import List
from common.command import ChatType, Command
from common.event import MessageEvent


def console_stop_command(plugin, args: List[str], raw_string: str, context, evt):
    plugin.bot.stop()


def console_help_command(plugin, args: List[str], raw_string: str, context, evt):
    for k, v in sorted(plugin.bot.command_manager.console_commands.items(), key=lambda x: x[0]):
        plugin.bot.logger.info(f"{k} --- {v.help_string}")


def help_command(plugin, args: List[str], raw_string: str, context, evt):
    from io import StringIO
    buf = StringIO()
    command_list: List[Command] = []
    chat_type = ChatType(context["message_type"])
    if not args:
        for value in plugin.bot.command_manager.commands.values():
            for item in value.values():
                if chat_type in item.available_chats:
                    command_list.append(item)
    else:
        if args[0] in plugin.bot.command_manager.commands:
            for item in plugin.bot.command_manager.commands[args[0]].values():
                if chat_type in item.available_chats:
                    command_list.append(item)
        else:
            plugin.bot.client.send(context, "此插件未注册指令")
    command_list.sort(key=lambda x: x.command_name)
    for cmd in command_list:
        buf.write(
            f"{cmd.command_name}{'['+','.join(cmd.alias)+']' if cmd.alias else ''} --- {cmd.help_string}\n")
    plugin.bot.send(context, buf.getvalue())


def status_command(plugin, args: List[str], raw_string: str, context, evt):
    plugin.bot.send(context, plugin.bot.state_manager.generate_message())


def about_command(plugin, args: List[str], raw_string: str, context, evt):
    plugin.bot.send(context, """Countdown-Bot 2 by MikuNotFoundException
https://gitee.com/yutong_java/Countdown-Bot""")


def plugins_command(plugin, args: List[str], raw_string: str, context, evt):
    from io import StringIO
    buf = StringIO()
    for plugin in plugin.bot.plugins:
        meta = plugin.plugin_meta
        buf.write(
            f"{plugin.plugin_id} {meta.version}\n作者: {meta.author}\n描述: {meta.description}\n\n")
    plugin.bot.send(context, buf.getvalue())
