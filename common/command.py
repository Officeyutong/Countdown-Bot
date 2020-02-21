from typing import Dict, Set, Callable, List, Iterable, Optional, Any
# (插件,参数列表,原始字符串,上下文)
CommandHandler = Callable[[Any, List[str], str, dict], None]


class Command:
    def __init__(self,
                 plugin_id: str,
                 command_name: str,
                 handler: CommandHandler,
                 plugin,
                 help_string: str = "",
                 alias: Optional[Iterable[str]] = None,
                 is_console=False,
                 ):
        self.plugin_id = plugin_id
        self.command_name = command_name
        self.handler = handler
        self.alias = list(alias or [])
        self.help_string = help_string
        self.plugin = plugin
        self.is_console = is_console

    def invoke(self, args: List[str], raw_string: str, context: str):
        self.handler(self.plugin, args, raw_string, context)

    def __hash__(self):
        return hash(self.command_name)


class CommandManager:
    def __init__(self):
        self.commands: Dict[str, Dict[str, Command]] = {}
        self.name_bindings: Dict[str, Command] = {}
        self.console_commands: Dict[str, Command] = {}

    def register_command(self, command: Command):
        if command.is_console:
            if command.command_name in self.console_commands:
                raise NameError(f"控制台命令 {command.command_name} 已被注册")
            self.console_commands[command.command_name] = command
            return
        if command.plugin_id not in self.commands:
            self.commands[command.plugin_id] = {}
        if command.command_name in self.name_bindings:
            raise NameError(f"命令 {command.command_name} 已经被注册")
        for item in command.alias:
            if item in self.name_bindings:
                raise NameError(f"别名 {item} 已被注册")
        self.commands[command.plugin_id][command.command_name] = command
        self.name_bindings[command.command_name] = command
        for item in command.alias:
            self.name_bindings[item] = command
