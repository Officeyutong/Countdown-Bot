from register import command
from global_vars import CONFIG
import threading
from dns import resolver
from util import print_log
from io import StringIO


def plugin():
    return {
        "author": "Antares",
        "version": 1.0,
        "description": "DNS查询"
    }


def A_query(domain: str) -> list:
    result = []
    try:
        items = resolver.query(domain, 'A')
        for i in items.response.answer:
            for j in i.items:
                result.append(j.address)
    except Exception as err:
        print_log(err)
        return []
    return result


def MX_query(domain: str) -> list:
    result = []
    try:
        MX_items = resolver.query(domain, 'MX')
        for i in MX_items:
            result.append(
                f"MX preference = {i.preference}, main exchanger = {i.exchange}")
    except Exception as err:
        print_log(err)
        return []
    return result


def BASE_query(domain: str, query_mode: str) -> list:
    result = []
    try:
        items = resolver.query(domain, query_mode)
        for i in items.response.answer:
            for j in i.items:
                result.append(j.to_text())
    except Exception as err:
        print_log(err)
        return []
    return result


def ALL_query(domain: str, query_mode: str) -> list:
    if query_mode == 'A':
        return A_query(domain)
    elif query_mode == 'MX':
        return MX_query(domain)
    else:
        return BASE_query(domain, query_mode)


@command(name="dns", help="DNS查询")
def dns_query(bot, context, args):
    while args[-1] == "":
        del args[-1]

    if len(args) == 1:
        bot.send(context, "请输入正确的域名")
        return

    def handle():
        mode_list = ["A", "MX", "NS", "CNAME"]
        if args[1] == "help":
            bot.send(context, f"dns 域名 查询类型(可省)\n{mode_list}")
            return

        if len(args) > 2:
            if not args[2] in mode_list:
                bot.send(context, f"请输入正确的查询模式:{mode_list}")
                return
            buf = StringIO()
            buf.write(f"查询域名:{args[1]}\n")
            buf.write(f"查询模式:{args[2]}\n")
            buf.write("查询结果:\n")
            result = ALL_query(args[1], args[2])
            for item in result:
                buf.write(f"{item}\n")
            bot.send(context, buf.getvalue())
        else:
            buf = StringIO()
            buf.write(f"查询域名:{args[1]}\n查询结果:\n")
            for opt in mode_list:
                buf.write(f"{opt}:\n")
                result = ALL_query(args[1], opt)
                for item in result:
                    buf.write(f"{item}\n")
                buf.write("\n")
            bot.send(context, buf.getvalue())
    threading.Thread(target=handle).start()
