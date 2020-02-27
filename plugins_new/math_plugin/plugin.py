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
from .data import MATH_NAMES


class MathPluginConfig(ConfigBase):
    # LaTeX使用的额外宏包
    LATEX_PACKAGES = [
        "amssymb", "color", "amsthm", "multirow", "enumerate", "amstext"
    ]
    # 画图区间长度限制
    MATPLOT_RANGE_LENGTH = 30
    # 画图函数数量限制
    FUNCTION_COUNT_LIMIT = 4
    DEFUALT_TIMEOUT = 30


class MathPlugin(Plugin):
    def on_enable(self):
        self.bot: CountdownBot
        self.config: MathPluginConfig
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
                self.seires, "级数展开超时", self.config.DEFUALT_TIMEOUT),
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

    def time_limit_wrapper(self, func,  err_msg: str, timeout):
        async def wrapper(*args, **kwargs):
            try:
                await asyncio.wait_for(asyncio.wrap_future(self.bot.thread_pool.submit(lambda: func(*args, **kwargs))), timeout=timeout)
            except asyncio.TimeoutError:
                await self.bot.client_async.send(args[3], err_msg)
            except Exception as ex:
                await self.bot.client_async.send(args[3], str(ex))
                raise ex
        return wrapper

    def encode_bytes(self, bytes_) -> str:
        return base64.encodebytes(bytes_).decode().replace("\n", "")

    def make_result(self, sympy_obj) -> str:
        rendered = self.render_latex(f"$${sympy.latex(sympy_obj)}$$")
        return f"""Python表达式:
{sympy_obj}

LaTeX:
{sympy.latex(sympy_obj)}

图像:
[CQ:image,file=base64://{self.encode_bytes(rendered)}]
"""

    def solve(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        try:
            unknown, equations, *_ = args
        except:
            self.bot.client.send(context, "请输入正确的参数格式")
            raise
        result = sympy.solve(equations.split(","), unknown.split(","))
        self.bot.client.send(context, self.make_result(result))

    def integrate(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        func = raw_string.replace("integrate ", "")
        x = sympy.symbols("x")
        result = sympy.integrate(func, x)
        self.bot.client.send(context, self.make_result(result))

    def differentiate(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        func = raw_string.replace("diff ", "")
        x = sympy.symbols("x")
        result = sympy.diff(func, x)
        self.bot.logger.info(f"Diff: {func}\n result: {result}")
        self.bot.client.send(context, self.make_result(result))

    def seires(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        x0, *secs = args
        func = " ".join(secs)
        x = sympy.symbols("x")
        result = sympy.series(func, x0=sympy.simplify(x0), n=10, x=x)
        self.bot.client.send(context, self.make_result(result))

    def plot(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        try:
            begin, end, *func_all = args
            begin = float(begin)
            end = float(end)
            funcs = " ".join(func_all).split(",")
            if len(funcs) > self.config.FUNCTION_COUNT_LIMIT:
                self.bot.client.send(context, "绘制函数过多")
                return
            import matplotlib.pyplot as plt
            xs = numpy.arange(begin, end, (end-begin)/1000)
            buf = io.BytesIO()
            figure = plt.figure(",".join(funcs))
            for func in funcs:
                plt.plot(
                    xs, eval(func, None, {"x": xs, **MATH_NAMES})
                )
            figure.canvas.print_png(buf)
            self.bot.client.send(
                context, f"[CQ:image,file=base64://{self.encode_bytes(buf.getvalue())}]")
        except Exception as ex:
            self.bot.client.send(context, str(ex))
            raise ex

    def plotpe(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        try:
            begin, end, *func_all = args
            funcs = " ".join(func_all).split(",")
            if len(funcs) > self.config.FUNCTION_COUNT_LIMIT:
                self.bot.client.send(context, "绘制函数过多")
                return
            import matplotlib.pyplot as plt
            begin = float(begin)
            end = float(end)
            ts = numpy.arange(begin, end, (end-begin)/1000)
            buf = io.BytesIO()
            figure = plt.figure(",".join(funcs))
            for func in funcs:
                func_x, func_y = func.split(":")
                plt.plot(
                    eval(func_x, None, {"t": ts, **MATH_NAMES}),
                    eval(func_y, None, {"t": ts, **MATH_NAMES})
                )
            figure.canvas.print_png(buf)
            self.bot.client.send(
                context, f"[CQ:image,file=base64://{self.encode_bytes(buf.getvalue())}]")
        except Exception as ex:
            self.bot.client.send(context, str(ex))
            raise ex

    def render_latex(self, formula: str) -> bytes:
        buf = io.BytesIO()
        self.bot.logger.info(f"Rendering... {formula}")
        sympy.preview(formula, viewer="BytesIO", euler=False,
                      outputbuffer=buf, packages=tuple(self.config.LATEX_PACKAGES))
        self.bot.logger.info(f"Render {formula} ok")
        return buf.getvalue()

    def command_render_latex(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        to_render = raw_string.replace("latex ", "", 1)
        self.bot.client.send(
            context, f"[CQ:image,file=base64://{self.encode_bytes(self.render_latex(to_render))}]")


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
