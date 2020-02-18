import numpy as np
from cqhttp import CQHttp
from util import print_log
from register import command
from global_vars import registered_commands as commands
import re
import util
import sympy
import threading
import time
import base64
from io import BytesIO
import global_vars
from typing import List
config = global_vars.CONFIG[__name__]

MATH_NAMES = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "floor": np.floor,
    "around": np.around,
    "log": np.log,
    "log10": np.log10,
    "log2": np.log2,
    "sinh": np.sinh,
    "cosh": np.cosh,
    "tanh": np.tanh,
    "arcsin": np.arcsin,
    "arccos": np.arccos,
    "arctan": np.arctan,
    "arcsinh": np.arcsinh,
    "arccosh": np.arccosh,
    "arctanh": np.arctanh,
    "abs": np.abs,
    "sqrt": np.sqrt,
    "log1p": np.log1p,
    "sign": np.sign,
    "ceil": np.ceil,
    "modf": np.modf,
    "pi": np.pi
}


def plugin():
    return {
        "author": "officeyutong",
        "version": 2.0,
        "description": "sympy功能封装"
    }


@command(name="solve", help="解方程组 | solve 未知数1,未知数2... 方程1,方程2... (未知数和方程中不得含有空格)")
def solve(bot: CQHttp, context: dict, args: List[str] = None):
    def process():
        try:
            unknown, equations, *_ = args[1:]
        except Exception as ex:
            bot.send(context, "请输入正确的参数格式")
            raise ex
            # return

        def solve():
            print_log("Starting...")
            try:
                # res = sympy.integrate(func, x)
                result = sympy.solve(equations.split(","), unknown.split(","))
                buffer: BytesIO = renderLatex(
                    "$${}$$".format(sympy.latex(result)))
                bot.send(context, "Python表达式:\n{}\n\nLatex:\n{}\n\n图像:\n[CQ:image,file=base64://{}]".format(
                    result, sympy.latex(result), base64.encodebytes(buffer.getvalue()).decode(
                        "utf-8").replace("\n", "")))
            except Exception as ex:
                bot.send(context, ("{}".format(ex))[:300])
                raise ex
            print_log("Done...")
        thd2 = threading.Thread(target=solve)
        thd2.start()
        begin = time.time()
        while time.time()-begin < 10:
            time.sleep(0.1)
        if thd2.is_alive():
            bot.send(context, f"解方程{unknown},{equations}运行超时.")
            util.stop_thread(thd2)

    thread = threading.Thread(target=process)
    thread.start()


@command(name="integrate", help="对f(x)进行不定积分")
def integrate(bot: CQHttp, context=None, args=None):

    def process():
        func = "".join(map(lambda x: x+" ", args[1:]))
        x = sympy.symbols("x")
        print_log("Integrate for "+func)

        def integrate():
            print_log("Starting...")
            try:
                res = sympy.integrate(func, x)
                buffer: BytesIO = renderLatex(
                    "$${}$$".format(sympy.latex(res)))
                bot.send(context, "Python表达式:\n{}\n\nLatex:\n{}\n\n图像:\n[CQ:image,file=base64://{}]".format(
                    res, sympy.latex(res), base64.encodebytes(buffer.getvalue()).decode(
                        "utf-8").replace("\n", "")))
            except Exception as ex:
                bot.send(context, ("{}".format(ex))[:300])
                raise ex
            print_log("Done...")
        thd2 = threading.Thread(target=integrate)
        thd2.start()
        begin = time.time()
        while time.time()-begin < 5:
            time.sleep(0.1)
        if thd2.is_alive():
            bot.send(context, "积分{}运行超时.".format(func))
            util.stop_thread(thd2)

    thread = threading.Thread(target=process)
    thread.start()


@command(name="latex", help="渲染Latex公式")
def renderlatex(bot: CQHttp, context=None, args=None) -> None:
    from io import BytesIO
    import base64
    formula = "".join(map(lambda x: x+" ", args[1:]))
    try:
        buffer: BytesIO = renderLatex(formula)
        bot.send(context, "[CQ:image,file=base64://{}]".format(
            base64.encodebytes(buffer.getvalue()).decode(
                "utf-8").replace("\n", "")
        ))
    except Exception as ex:
        bot.send(context, "渲染Latex时发生错误:\n{}".format(ex))


@command(name="diff", help="求导")
def differentiate(bot: CQHttp, context: dict, args: List[str]) -> None:

    def process():
        func = "".join(map(lambda x: x+" ", args[1:]))
        x = sympy.symbols("x")
        print_log("diff for "+func)

        def diff():
            print_log("Starting...")
            try:
                res = sympy.diff(func, x)
                buffer: BytesIO = renderLatex(
                    "$${}$$".format(sympy.latex(res)))
                bot.send(context, "Python表达式:\n{}\n\nLatex:\n{}\n\n图像:\n[CQ:image,file=base64://{}]".format(
                    res, sympy.latex(res), base64.encodebytes(buffer.getvalue()).decode(
                        "utf-8").replace("\n", "")))
            except Exception as ex:
                bot.send(context, ("{}".format(ex))[:300])
                raise ex
            print_log("Done...")
        thd2 = threading.Thread(target=diff)
        thd2.start()
        begin = time.time()
        while time.time()-begin < 5:
            time.sleep(0.1)
        if thd2.is_alive():
            bot.send(context, "求导{}运行超时.".format(func))
            util.stop_thread(thd2)

    thread = threading.Thread(target=process)
    thread.start()


@command(name="series", help="级数展开 series 展开点 函数")
def series(bot: CQHttp, context: dict, args: List[str]) -> None:

    def process():
        x0 = args[1]
        func = "".join(map(lambda x: x+" ", args[2:]))
        x = sympy.symbols("x")
        print_log("series for "+func)

        def series():
            print_log("Starting...")
            try:
                res = sympy.series(func, x0=sympy.simplify(x0), n=10, x=x)
                buffer: BytesIO = renderLatex(
                    "$${}$$".format(sympy.latex(res)))
                print("sending...")
                bot.send(context, "Python表达式:\n{}\n\nLatex:\n{}\n\n图像:\n[CQ:image,file=base64://{}]".format(
                    res, sympy.latex(res), base64.encodebytes(buffer.getvalue()).decode(
                        "utf-8").replace("\n", "")))
            except Exception as ex:
                bot.send(context, ("{}".format(ex))[:300])
                raise ex
            print_log("Done...")
        thd2 = threading.Thread(target=series)
        thd2.start()
        begin = time.time()
        while time.time()-begin < 5:
            time.sleep(0.1)
        if thd2.is_alive():
            bot.send(context, "级数{}运行超时.".format(func))
            util.stop_thread(thd2)

    thread = threading.Thread(target=process)
    thread.start()


@command(name="plot", help="绘制函数图像 plot 起始点 终点 函数")
def plot(bot: CQHttp, context: dict, args: List[str]) -> None:

    def process():

        def plot():

            print_log("Starting...")
            try:
                begin, end = float(args[1]), float(args[2])
                functions = (
                    "".join(map(lambda x: x+" ", args[3:]))).split(",")
                if len(functions) > config.FUNCTION_COUNT_LIMIT:
                    bot.send(context, "绘制函数过多")
                    return
                print_log(f"drawing {functions}, {begin}, {end}")
                import numpy
                if end-begin > config.MATPLOT_RANGE_LENGTH:
                    bot.send(context, "绘制区间过长")
                    return

                import matplotlib.pyplot as plt
                from io import BytesIO

                x = numpy.arange(begin, end, (end-begin)/1000)
                print(begin, end)
                buf = BytesIO()
                plt.cla()
                fig = plt.figure(",".join(functions))
                for func in functions:
                    plt.plot(x, eval(func, None, {
                        "x": x,
                        **MATH_NAMES
                    }))
                fig.canvas.print_png(buf)
                bot.send(context, "[CQ:image,file=base64://{}]".format(
                    base64.encodebytes(buf.getvalue()).decode(
                         "utf-8").replace("\n", "")))
            except Exception as ex:
                bot.send(context, ("{}".format(ex))[:300])
                raise ex
            print_log("Done...")
        thd2 = threading.Thread(target=plot)
        thd2.start()
        begin_time = time.time()
        while time.time()-begin_time < 10:
            time.sleep(0.1)
        if thd2.is_alive():
            bot.send(context, "绘图{}运行超时.".format(func))
            print("超时..")
            util.stop_thread(thd2)

    thread = threading.Thread(target=process)
    thread.start()


@command(name="plotpe", help="绘制参数方程图像 参数起始 参数终止 x方程1:y方程1[,x方程2:y方程2[,...]]")
def plotpe(bot: CQHttp, context: dict, args: List[str]) -> None:

    def process():

        def plot():

            print_log("Starting...")
            try:
                begin, end = float(args[1]), float(args[2])
                functions = (
                    "".join(map(lambda x: x+" ", args[3:]))).split(",")
                if len(functions) > config.FUNCTION_COUNT_LIMIT:
                    bot.send(context, "绘制函数过多")
                    return
                print_log(f"drawing {functions}, {begin}, {end}")
                import numpy
                if end-begin > config.MATPLOT_RANGE_LENGTH:
                    bot.send(context, "绘制区间过长")
                    return

                import matplotlib.pyplot as plt
                from io import BytesIO

                ts = np.arange(begin, end, (end-begin)/1000)
                print(begin, end)
                buf = BytesIO()
                plt.cla()
                fig = plt.figure(",".join(functions))
                for func in functions:
                    func_x, func_y = func.split(":")

                    plt.plot(eval(func_x, None, {
                        "t": ts,
                        **MATH_NAMES
                    }), eval(func_y, None, {
                        "t": ts,
                        **MATH_NAMES
                    }))
                fig.canvas.print_png(buf)
                import tempfile
                tmpf = tempfile.mktemp(".png")
                with open(tmpf, "wb") as f:
                    f.write(buf.getvalue())
                print(tmpf)

                bot.send(context, "[CQ:image,file=base64://{}]".format(
                    base64.encodebytes(buf.getvalue()).decode(
                         "utf-8").replace("\n", "")))
            except Exception as ex:
                bot.send(context, ("{}".format(ex))[:300])
                raise ex
            print_log("Done...")
        thd2 = threading.Thread(target=plot)
        thd2.start()
        begin_time = time.time()
        while time.time()-begin_time < 10:
            time.sleep(0.1)
        if thd2.is_alive():
            bot.send(context, "绘图{}运行超时.".format(func))
            print("超时..")
            util.stop_thread(thd2)

    thread = threading.Thread(target=process)
    thread.start()


def renderLatex(formula: str) -> BytesIO:
    from sympy import preview
    print_log("Rendering {}".format(formula))
    buffer = BytesIO()
    preview(formula, viewer="BytesIO", euler=False,
            outputbuffer=buffer, packages=tuple(config.LATEX_PACKAGES))
    return buffer
