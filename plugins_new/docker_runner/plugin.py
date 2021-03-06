from common.plugin import Plugin
from common.countdown_bot import CountdownBot
from common.datatypes import PluginMeta
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.config_loader import ConfigBase
import docker
from typing import List, Dict
import asyncio
import tempfile
import pathlib
import aiofiles
import re
import html


class DockerRunnerConfig(ConfigBase):
    DOCKER_IMAGE = "python"
    # 输出长度限制，字节
    OUTPUT_LENGTH_LIMIT = 200
    # 执行Python代码的时间限制(ms)
    EXECUTE_TIME_LIMIT = 2000
    # 用户提供的输入数据在多长时间后到期，ms
    INPUT_EXPIRE_AFTER = 1000*60*60
    NEW_LINE_COUNT_LIMIT = 5
    LANGUAGE_SETTINGS = {
        "python": {
            "sourceFilename": "{name}.py_",
            "executeFilename": "{name}.py",
            "compile": "cp {source} {target}",
            "run": "python3.8 {target}"
        },
        "cpp": {
            "sourceFilename": "{name}.cpp",
            "executeFilename": "{name}.out",
            "compile": "g++ -fdiagnostics-color=never {source} -o {target}",
            "run": "./{target}"
        },
        "c": {
            "sourceFilename": "{name}.c",
            "executeFilename": "{name}.out",
            "compile": "gcc  -fdiagnostics-color=never {source} -o {target}",
            "run": "./{target}"
        },
        "bash": {
            "sourceFilename": "{name}.sh_",
            "executeFilename": "{name}.sh",
            "compile": "cp {source}  {target} && chmod +x {target}",
            "run": "bash {target}"
        },
        "rust": {
            "sourceFilename": "{name}.rs",
            "executeFilename": "{name}.out",
            "compile": "rustc {source} -o {target}",
            "run": "./{target}"
        },
        "haskell": {
            "sourceFilename": "{name}.hs",
            "executeFilename": "{name}.out",
            "compile": "ghc {source} -o {target}",
            "run": "./{target}"
        },
    }
    BLACKLIST_USERS: List[int] = []


class DockerRunnerPlugin(Plugin):
    async def run_code(self, code: str, language_cfg: dict, context: dict, stdin: bytes = b"") -> str:
        # pattern = re.compile(r'&#(.*?);')
        # for item in pattern.findall(code):
        #     code = code.replace("&#{};".format(
        #         item), bytes([int(item)]).decode("utf-8"))
        code = html.unescape(code).strip()
        self.bot.logger.info(f"Running...")
        client = docker.from_env()
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        src_file = language_cfg["sourceFilename"].format(name="app")
        exe_file = language_cfg["executeFilename"].format(name="app")
        async with aiofiles.open(temp_dir/src_file, "w") as f:
            await f.write(code)
        async with aiofiles.open(temp_dir/"f_stdin", "wb") as f:
            await f.write(stdin)
        command = language_cfg["compile"].format(source=src_file, target=exe_file) \
            + " && "+language_cfg["run"].format(target=exe_file) + " < f_stdin"
        container = client.containers.run(
            image=self.config.DOCKER_IMAGE,
            command=f"sh -c '{command}'",
            stdin_open=True,
            detach=True,
            tty=True,
            network_mode="none",
            working_dir="/temp",
            volumes={str(temp_dir): {"bind": "/temp", "mode": "rw"}},
            mem_limit="50m",
            memswap_limit="50m",
            oom_kill_disable=True,
            nano_cpus=int(0.4*1/1e-9)
        )
        try:
            await asyncio.wait_for(asyncio.wrap_future(
                self.bot.submit_multithread_task(container.wait)
            ), timeout=self.config.EXECUTE_TIME_LIMIT/1000)
        except asyncio.TimeoutError:
            try:
                container.kill()
                container.stop()
            except Exception as ex:
                self.bot.logger.exception(ex)
            await self.bot.client_async.send(context, f"执行超时", auto_escape=False)
            # timed_out = True
        # if not timed_out:
        output: str = container.logs().decode()
        if len(output) > self.config.OUTPUT_LENGTH_LIMIT:
            output = output[:self.config.OUTPUT_LENGTH_LIMIT] + \
                "[超出长度限制部分已截断]"
        if output.count("\n") > self.config.NEW_LINE_COUNT_LIMIT:
            output = "\n".join(output.split(
                "\n")[:self.config.NEW_LINE_COUNT_LIMIT]+["[消息行数过多]"])
        # self.bot.logger.debug(container.logs().decode())
        self.bot.logger.debug("done.")
        regexpr = re.compile(r"\[CQ:(record|image),.*file=file:(.*).*\]")
        if regexpr.search(output):
            escape = True
        else:
            escape = False
        await self.bot.client_async.send(context, "无输出" if not output else output, auto_escape=escape)
        container.remove(force=True)
        import shutil
        shutil.rmtree(temp_dir)

    async def command_execx(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        if evt.user_id in self.config.BLACKLIST_USERS:
            await self.bot.client_async.send(context, "你无权使用该指令")
            return
        if not args:
            await self.bot.client_async.send(context, f'execx [语言ID] 代码\n支持的语言ID: {" ".join(self.config.LANGUAGE_SETTINGS.keys())}')
            return
        if args[0] not in self.config.LANGUAGE_SETTINGS:
            await self.bot.client_async.send(context, "未知语言ID")
            return
        stdin_data = self.user_input.get((evt.group_id, evt.user_id), b"")
        code = raw_string.replace("execx", "", 1).replace(args[0], "", 1)
        self.logger.info(f"Running: \n{code}")
        await self.run_code(code, self.config.LANGUAGE_SETTINGS[args[0]], context, stdin_data)

    async def command_exec(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        if evt.user_id in self.config.BLACKLIST_USERS:
            await self.bot.client_async.send(context, "你无权使用该指令")
            return
        stdin_data = self.user_input.get((evt.group_id, evt.user_id), b"")
        code = raw_string.strip()[5:]
        code = f"""CALLER_UID={context['user_id']}\nCALLER_NICKNAME={str(context['sender']['nickname']).encode()}.decode()\nCALLER_CARD={str(context['sender']['card']).encode()}.decode()\n"""+code
        self.logger.debug(f"Code: {code}")
        await self.run_code(code, self.config.LANGUAGE_SETTINGS["python"], context, stdin_data)

    async def command_input(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        if evt.user_id in self.config.BLACKLIST_USERS:
            await self.bot.client_async.send(context, "你无权使用该指令")
            return
        if not args:
            await self.bot.client_async.send(context, "请提供输入数据")
        user_id = (evt.group_id, evt.user_id)
        data = raw_string.replace("input ", "", 1).encode("utf-8")
        self.user_input[user_id] = data

        async def remover():
            await asyncio.sleep(self.config.INPUT_EXPIRE_AFTER/1000)
            if user_id in self.user_input:
                del self.user_input[user_id]
        self.bot.submit_async_task(remover())
        await self.bot.client_async.send(context, f"您的输入数据已经保存,此输入数据将会在下次使用input指令或 {self.config.INPUT_EXPIRE_AFTER}ms 后失效.")

    def on_enable(self):
        self.bot: CountdownBot
        self.config: DockerRunnerConfig
        self.register_command_wrapped(
            command_name="exec",
            command_handler=self.command_exec,
            help_string="在Docker中执行Python3代码",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="execx",
            command_handler=self.command_execx,
            help_string="在Docker中执行代码 | 输入 execx 查看帮助",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="input",
            command_handler=self.command_input,
            help_string="指定下一次执行代码时的标准输入 | input [输入数据]",
            chats={ChatType.group},
            is_async=True
        )
        self.user_input: Dict[str, bytes] = dict()


def get_plugin_class():
    return DockerRunnerPlugin


def get_config_class():
    return DockerRunnerConfig


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="在Docker中执行代码"
    )
