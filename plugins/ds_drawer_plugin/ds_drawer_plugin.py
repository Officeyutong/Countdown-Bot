from register import command
from global_vars import CONFIG
from . import ds_drawer
import base64
config = CONFIG[__name__]


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.1,
        "description": "SAM绘制器"
    }


@command(name="sam", help="绘制SAM")
def sam(bot, context, args):

    if len(args) < 2:
        bot.send(context, "请输入字符串")
        return
    string = "".join(args[1:])
    if len(string) > config.MAX_STRING_LENGTH:
        bot.send(context, "字符串过长")
        return
    imgpath = ds_drawer.generate_graph(string, "png")
    result = ""
    with open(imgpath, "rb") as file:
        result = base64.encodebytes(file.read()).decode().replace("\n", "")
    bot.send(context, "[CQ:image,file=base64://{}]".format(result))
