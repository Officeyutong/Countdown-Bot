

import sys
import warnings
warnings.filterwarnings("ignore")


def render_latex(formula: str) -> bytes:
    import io
    import sympy
    buf = io.BytesIO()
    sympy.preview(formula, viewer="BytesIO", euler=False,
                  outputbuffer=buf, packages=tuple({PACKAGES}))
    return buf.getvalue()


def make_result1(expr):
    import sympy
    import sys
    # print("making result", file=sys.stderr,flush=True)
    return {
        "latex": sympy.latex(expr),
        "python_expr": str(expr),
        "image": render_latex(f"$${sympy.latex(expr)}$$")
    }


def solve(unknown, equations):
    import sympy
    return make_result1(sympy.solve(equations.split(","), unknown.split(",")))


def factor(func):
    import sympy
    return make_result1(sympy.factor(func))


def integrate(func):
    import sympy
    return make_result1(sympy.integrate(func))


def differentiate(func):
    # import sys
    # print("loading sympy", file=sys.stderr,flush=True)
    import sympy
    # print("sympy loaded", file=sys.stderr,flush=True)
    x = sympy.Symbol("x")
    return make_result1(sympy.diff(func, x))


def series(x0, func):
    import sympy
    x = sympy.symbols("x")
    return make_result1(sympy.series(func, x0=sympy.simplify(x0), n=10, x=x))


def plot(begin, end, funcs):
    import numpy as np
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
        "pi": np.pi,
        "numpy": np
    }
    import numpy
    import io
    import matplotlib.pyplot as plt
    xs = np.arange(begin, end, (end-begin)/1000)
    buf = io.BytesIO()
    figure = plt.figure(",".join(funcs))
    for func in funcs:
        plt.plot(
            xs, eval(func, None, {"x": xs, **MATH_NAMES})
        )
    figure.canvas.print_png(buf)
    return {"latex": "", "python_expr": "", "image": buf.getvalue()}


def plotpe(begin, end, funcs):
    import numpy as np
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
        "pi": np.pi,
        "numpy": np
    }
    import numpy
    import io
    import matplotlib.pyplot as plt
    ts = np.arange(begin, end, (end-begin)/1000)
    buf = io.BytesIO()
    figure = plt.figure(",".join(funcs))
    for func in funcs:
        func_x, func_y = func.split(":")
        plt.plot(
            eval(func_x, None, {"t": ts, **MATH_NAMES}),
            eval(func_y, None, {"t": ts, **MATH_NAMES})
        )
    figure.canvas.print_png(buf)
    return {"latex": "", "python_expr": "", "image": buf.getvalue()}


# print("started..", file=sys.stderr,flush=True)
output = {"latex": "", "python_expr": "", "image": b""}
{CODE}
# print(output)
with open("output.txt", "w") as f:
    f.write(str(output))
