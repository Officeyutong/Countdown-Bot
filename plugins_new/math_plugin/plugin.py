from common.plugin import Plugin
from common.countdown_bot import CountdownBot
from common.datatypes import PluginMeta
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.config_loader import ConfigBase
from typing import List
import sympy
import io
import asyncio
import base64
import numpy
import re
from .data import MATH_NAMES
from dataclasses import dataclass
import aiofiles
import docker
import tempfile
import ast
import pathlib
@dataclass
class ExecuteResult:
    python_expr: str
    latex: str
    image: bytes


class MathPluginConfig(ConfigBase):
    # LaTeX使用的额外宏包
    LATEX_PACKAGES = [
        "amssymb", "color", "amsthm", "multirow", "enumerate", "amstext"
    ]
    # 画图区间长度限制
    MATPLOT_RANGE_LENGTH = 30
    # 画图函数数量限制
    FUNCTION_COUNT_LIMIT = 4
    DEFUALT_TIMEOUT = 30*1000  # ms
    DOCKER_IMAGE = "python"  # 运行所使用的docker镜像名


class MathPlugin(Plugin):
    async def execute_in_docker(self, code: str, context: dict) -> str:
        self.bot.logger.info(f"Running...")
        client = docker.from_env()
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        self.logger.debug(temp_dir)
        src_file = "run.py"
        async with aiofiles.open(temp_dir/src_file, "w") as f:
            await f.write(self.template.replace("{CODE}", code))
        command = f"python3.8 -O {src_file}"
        container = client.containers.run(
            image=self.config.DOCKER_IMAGE,
            command=f"sh -c '{command} 2> err.txt'",
            stdin_open=True,
            detach=True,
            tty=True,
            network_mode="none",
            working_dir="/temp",
            volumes={str(temp_dir): {"bind": "/temp", "mode": "rw"}},
            mem_limit="128m",
            memswap_limit="128m",
            oom_kill_disable=True,
            nano_cpus=int(0.4*1/1e-9)
        )
        try:
            await asyncio.wait_for(asyncio.wrap_future(
                self.bot.submit_multithread_task(container.wait)
            ), timeout=self.config.DEFUALT_TIMEOUT/1000)
            try:
                async with aiofiles.open(temp_dir/"output.txt", "r") as f:
                    docker_output = await f.read()
            except FileNotFoundError as err:
                await self.bot.client_async.send(context, str(err))
                self.logger.exception(err)
            async with aiofiles.open(temp_dir/"err.txt", "r") as f:
                stderr = await f.read()
            if stderr.strip():
                await self.bot.client_async.send(context, stderr[:1000])
                self.logger.error(stderr)
            output: dict = ast.literal_eval(docker_output)
            if not docker_output:
                raise Exception("Program exited abnormally.")
            self.bot.logger.info(type(output))
            self.bot.logger.debug(output)
            container.remove()
            return ExecuteResult(
                python_expr=output["python_expr"],
                latex=output["latex"],
                image=output["image"]
            )
        except asyncio.TimeoutError as ex0:
            try:
                container.kill()
                container.stop()
            except Exception as ex:
                self.bot.logger.exception(ex)
            raise ex0
        finally:
            pass
            import shutil
            shutil.rmtree(temp_dir)

    def process_string(self, string: str):
        pattern = re.compile(r'&#(.*?);')
        for item in pattern.findall(string):
            string = string.replace("&#{};".format(
                item), bytes([int(item)]).decode("utf-8"))
        return string

    def on_enable(self):
        self.bot: CountdownBot
        self.config: MathPluginConfig
        with open(self.plugin_base_dir/"template.py", "r") as f:
            self.template = f.read().replace(
                "{PACKAGES}", str(self.config.LATEX_PACKAGES))
        self.register_command_wrapped(
            command_name="solve",
            command_handler=self.time_limit_wrapper(
                self.solve, "解方程运行超时", self.config.DEFUALT_TIMEOUT),
            help_string="解方程组 | solve [未知数1],[未知数2].... [方程1],[方程2]... (不得有多余空格)",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="integrate",
            command_handler=self.time_limit_wrapper(
                self.integrate, "积分运行超时", self.config.DEFUALT_TIMEOUT),
            help_string="不定积分 | integrate [函数] (不得有多余空格)",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="diff",
            command_handler=self.time_limit_wrapper(
                self.differentiate, "求导运行超时", self.config.DEFUALT_TIMEOUT),
            help_string="求导 | diff [函数] (不得有多余空格)",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="latex",
            command_handler=self.time_limit_wrapper(
                self.command_render_latex, "LaTeX渲染超时", self.config.DEFUALT_TIMEOUT),
            help_string="渲染LaTeX | LaTeX [文本]",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="series",
            command_handler=self.time_limit_wrapper(
                self.series, "级数展开超时", self.config.DEFUALT_TIMEOUT),
            help_string="级数展开 | seires [展开点] [函数] (不得有多余空格)",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="plot",
            command_handler=self.time_limit_wrapper(
                self.plot, "绘图超时", self.config.DEFUALT_TIMEOUT),
            help_string="绘制函数图像 | plot [起始点] [终点] [函数1],[函数2].. (不得有多余空格)",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="plotpe",
            command_handler=self.time_limit_wrapper(
                self.plotpe, "绘图超时", self.config.DEFUALT_TIMEOUT),
            help_string="绘制参数方程 | plotpe [参数开始] [参数终止] [x方程1]:[y方程1],[x方程2]:[y方程2].. (不得有多余空格)",
            chats={ChatType.group},
            is_async=True
        )
        self.register_command_wrapped(
            command_name="factor",
            command_handler=self.time_limit_wrapper(
                self.factor, "因式分解运行超时", self.config.DEFUALT_TIMEOUT),
            help_string="分解因式 | factor 多项式 (多项式中不得含有空格)",
            chats={ChatType.group},
            is_async=True
        )

    def time_limit_wrapper(self, func,  err_msg: str, timeout):
        async def wrapper(*args, **kwargs):
            try:
                await asyncio.wait_for(
                    func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                await self.bot.client_async.send(args[3], err_msg)
            except Exception as ex:
                await self.bot.client_async.send(args[3], str(ex))
                raise ex
        return wrapper

    def encode_bytes(self, bytes_) -> str:
        return base64.encodebytes(bytes_).decode().replace("\n", "")

    def make_result(self, result: dict) -> str:
        return f"""Python表达式:
{result.python_expr}

LaTeX:
{result.latex}

图像:
[CQ:image,file=base64://{self.encode_bytes(result.image)}]
"""

    async def solve(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        try:
            unknown, equations, *_ = (self.process_string(x) for x in args)
        except:
            self.bot.client.send(context, "请输入正确的参数格式")
            raise
        TEMPLATE = f"""output=solve("{unknown}","{equations}")"""
        result = await self.execute_in_docker(TEMPLATE, context)
        await self.bot.client_async.send(context, self.make_result(result))

    async def factor(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        TEMPLATE = f"""output=factor("{self.process_string(args[0])}")"""
        result = await self.execute_in_docker(TEMPLATE, context)
        await self.bot.client_async.send(context, self.make_result(result))

    async def integrate(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        TEMPLATE = f"""output=integrate("{self.process_string(args[0])}")"""
        result = await self.execute_in_docker(TEMPLATE, context)
        await self.bot.client_async.send(context, self.make_result(result))

    async def differentiate(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        TEMPLATE = f"""output=differentiate("{self.process_string(args[0])}")"""
        result = await self.execute_in_docker(TEMPLATE, context)
        await self.bot.client_async.send(context, self.make_result(result))

    async def series(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        TEMPLATE = f"""output=series("{self.process_string(args[0])}","{self.process_string(args[1])}")"""
        result = await self.execute_in_docker(TEMPLATE, context)
        await self.bot.client_async.send(context, self.make_result(result))

    async def plot(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        try:
            begin, end, *func_all = (self.process_string(x) for x in args)
            begin = float(begin)
            end = float(end)
            funcs = " ".join(func_all).split(",")
            if len(funcs) > self.config.FUNCTION_COUNT_LIMIT:
                await self.bot.client_async.send(context, "绘制函数过多")
                return
            TEMPLATE = f"""output=plot({begin},{end},{funcs})"""
            result = await self.execute_in_docker(TEMPLATE, context)
            await self.bot.client_async.send(
                context, f"[CQ:image,file=base64://{self.encode_bytes(result.image)}]")
        except Exception as ex:
            await self.bot.client_async.send(context, str(ex))
            raise ex

    async def plotpe(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        try:
            begin, end, *func_all = (self.process_string(x) for x in args)
            funcs = " ".join(func_all).split(",")
            if len(funcs) > self.config.FUNCTION_COUNT_LIMIT:
                await self.bot.client_async.send(context, "绘制函数过多")
                return
            import matplotlib.pyplot as plt
            begin = float(begin)
            end = float(end)
            TEMPLATE = f"""output=plotpe({begin},{end},{funcs})"""
            result = await self.execute_in_docker(TEMPLATE, context)
            await self.bot.client_async.send(
                context, f"[CQ:image,file=base64://{self.encode_bytes(result.image)}]")
        except Exception as ex:
            await self.bot.client_async.send(context, str(ex))
            raise ex

    async def command_render_latex(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):

        to_render = raw_string.replace("latex ", "", 1)
        TEMPLATE = "output={'latex':'','python_expr':'','image':render_latex('''{to_render}''')}".replace("to_render",to_render)
        result = await self.execute_in_docker(TEMPLATE, context)
        await self.bot.client_async.send(
            context, f"[CQ:image,file=base64://{self.encode_bytes(result.image)}]")


def get_plugin_class():
    return MathPlugin


def get_config_class():
    return MathPluginConfig


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="sympy相关功能封装"
    )
