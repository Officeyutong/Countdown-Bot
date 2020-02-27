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

class DockerRunnerConfig(ConfigBase):
    DOCKER_IMAGE = "python"
    # 输出长度限制，字节
    OUTPUT_LENGTH_LIMIT = 200
    # 执行Python代码的时间限制(ms)
    EXECUTE_TIME_LIMIT = 2000
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
        }
    }


class DockerRunnerPlugin(Plugin):
    async def run_code(self, code: str, language_cfg: dict, context: dict, stdin: bytes = b"") -> str:
        pattern = re.compile(r'&#(.*?);')
        for item in pattern.findall(code):
            code = code.replace("&#{};".format(
                item), bytes([int(item)]).decode("utf-8"))
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
            await self.bot.client_async.send(context, f"代码'{code}'执行超时", auto_escape=False)
            # timed_out = True
        # if not timed_out:
        output = container.logs().decode()
        if len(output) > self.config.OUTPUT_LENGTH_LIMIT:
            output = output[:self.config.OUTPUT_LENGTH_LIMIT] + \
                "[超出长度限制部分已截断]"
            # self.bot.logger.debug(container.logs().decode())
        self.bot.logger.debug("done.")
        await self.bot.client_async.send(context, "无输出" if not output else output)
        container.remove(force=True)
        import shutil
        shutil.rmtree(temp_dir)

    async def command_execx(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        if not args:
            await self.bot.client_async.send(context, f'execx [语言ID] 代码\n支持的语言ID: {" ".join(self.config.LANGUAGE_SETTINGS.keys())}')
            return
        if args[0] not in self.config.LANGUAGE_SETTINGS:
            await self.bot.client_async.send(context, "未知语言ID")
            return
        code = " ".join(raw_string.split(" ")[1:])
        self.logger.info(f"Running: {code}")
        await self.run_code(code, self.config.LANGUAGE_SETTINGS[args[0]], context)

    async def command_exec(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        code = raw_string.strip()[5:]
        code = f"""CALLER_UID={context['user_id']}\nCALLER_NICKNAME={str(context['sender']['nickname']).encode()}.decode()\nCALLER_CARD={str(context['sender']['card']).encode()}.decode()\n"""+code
        self.logger.debug(f"Code: {code}")
        await self.run_code(code, self.config.LANGUAGE_SETTINGS["python"], context, "qwqqwq".encode())

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
