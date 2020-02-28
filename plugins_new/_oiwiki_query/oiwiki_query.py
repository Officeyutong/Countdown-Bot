from cqhttp import CQHttp
from util import print_log
from register import command
from global_vars import registered_commands as commands
import re
import util
import global_vars
config = global_vars.CONFIG[__name__]


def plugin():
    return {
        "author": "0xis",
        "version": 1.0,
        "description": "OI Wiki查询支持."
    }


@command(name="wiki", help="求助 OI Wiki(https://oi-wiki.org/)")
def oiwiki_query(bot: CQHttp, context=None, args=None):
    # from wikipages import wikipages
    import urllib
    import json
    wikipages = None
    decoder = json.JSONDecoder()
    with urllib.request.urlopen(config.OIWIKI_LIST_URL) as page:
        wikipages = decoder.decode(page.read().decode("utf-8"))
    query_text = args[1]
    if query_text in wikipages:
        bot.send(context, "OI Wiki 列表中有名为「%s」的页面：%s" %
                 (query_text, wikipages[query_text]))
    else:
        bot.send(context, "OI Wiki 列表中无结果，请访问：https://oi-wiki.org/ 查看更多内容")
