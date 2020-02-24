from cqhttp import CQHttp
from util import print_log
from register import command
from global_vars import registered_commands as commands
from global_vars import config
import re
import util
# import json
# import urllib
import requests
from typing import List
client = requests.session()


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "OIerDB查询支持."
    }


@command(name="oier", help="执行oierdb查询(http://bytew.net/OIer)")
def oier_query(bot: CQHttp, context: dict = None, args: List[str] = None):
    print_log("querying "+str(args))
    while args and not args[-1].strip():
        args.pop()
    if len(args) < 2:
        bot.send(context, "请输入姓名qwq")
        return
    import threading

    def query():
        from util import print_log
        from io import StringIO
        buf = StringIO()
        # print_log("querying "+args[1])
        buf.write("查询到以下数据:\n")
        # bot.send(context,"查询到以下数据:")
        from random import shuffle
        count = 0
        # items = fetch(args[1])
        with client.get("http://bytew.net/OIer/search.php", params={"method": "normal", "q": args[1]}) as urlf:
            items = urlf.json()["result"]
        shuffle(items)
        for item in items:
            print_log("item:{}".format(item))
            buf.write("姓名:%s\n生理性别:%s\n" % (item["name"],
                                            {-1: "女", 1: "男"}.get(int(item["sex"]), "未知")))
            # text+="获得奖项:\n"
            awards = list(enumerate(eval(item["awards"])))
            for _, award in awards:
                # print_log(award)
                # print_log(type(award))
                for k, v in award.items():
                    if type(v) == str:
                        award[k] = award[k].strip()
                format_str = "在<{province}>{school}<{grade}>时参加<{contest}>以{score}分(全国排名{rank})的成绩获得<{type}>\n"
                buf.write(format_str.format(grade=award["grade"],
                                            province=award["province"],
                                            rank=award["rank"],
                                            score=award["score"],
                                            school=award["school"],
                                            type=award["award_type"],
                                            contest=award["identity"]
                                            ))
            count += 1
            if count >= 5:
                buf.write("\n余下记录太长，请去原网站查看.")
                break
            # text += '\n'
            buf.write("\n")
        bot.send(context, buf.getvalue().strip())
    thread: threading.Thread = threading.Thread(target=query)
    # query()
    thread.start()


# def fetch(name: str):
#     decoder = json.JSONDecoder()
#     with urllib.request.urlopen("?method=normal&q="+urllib.parse.quote(name)) as page:
#         result = decoder.decode(page.read().decode("utf-8"))
#     return result["result"]
