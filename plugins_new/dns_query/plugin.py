from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import GroupMessageEvent
from typing import Dict, List
from io import StringIO
from dns import resolver


class DNSPlugin(Plugin):
    def A_query(self, domain: str) -> List[str]:
        result: List[str] = []
        try:
            items = resolver.query(domain, 'A')
            for i in items.response.answer:
                for j in i.items:
                    result.append(j.address)
        except Exception:
            return []
        return result

    def MX_query(self, domain: str) -> List[str]:
        result: List[str] = []
        try:
            MX_items = resolver.query(domain, 'MX')
            for i in MX_items:
                result.append(
                    f"MX preference = {i.preference}, main exchanger = {i.exchange}")
        except Exception:
            return []
        return result

    def BASE_query(self, domain: str, query_mode: str) -> List[str]:
        result: List[str] = []
        try:
            items = resolver.query(domain, query_mode)
            for i in items.response.answer:
                for j in i.items:
                    result.append(j.to_text())
        except Exception:
            return []
        return result

    def query(self, domain: str, query_mode: str) -> List[str]:
        if query_mode == 'A':
            return A_query(domain)
        elif query_mode == 'MX':
            return MX_query(domain)
        else:
            return BASE_query(domain, query_mode)

    def command_dns(self, plugin, args: List[str], raw_string: str, context, evt: GroupMessageEvent):
        def wrapper():
            if not len(args):
                self.bot.client_async.send(context, "请输入正确的域名")
                return

            mode_list = set("A", "MX", "NS", "CNAME")

            if len(args) > 1:
                if not args[1] in mode_list:
                    self.bot.client_async.send(
                        context, f"请输入正确的查询模式:{mode_list}")
                    return
                buf = StringIO()
                buf.write(f"查询域名:{args[0]}\n")
                buf.write(f"查询模式:{args[1]}\n")
                buf.write("查询结果:\n")
                result = query(args[0], args[1])
                for item in result:
                    buf.write(f"{item}\n")
                self.bot.client_async.send(context, buf.getvalue())
            else:
                buf = StringIO()
                buf.write(f"查询域名:{args[0]}\n查询结果:\n")
                for opt in mode_list:
                    buf.write(f"{opt}:\n")
                    result = query(args[0], opt)
                    for item in result:
                        buf.write(f"{item}\n")
                    buf.write("\n")
                self.bot.client_async.send(context, buf.getvalue())
        self.bot.submit_multithread_task(wrapper)

    def on_enable(self):
        self.bot: CountdownBot
        self.register_command_wrapped(
            command_name="dns",
            command_handler=self.command_dns,
            help_string="DNS查询 | dns [host] [A/MX/NS/CNAME](可选)",
            chats=ChatType.all(),
        )


def get_plugin_class():
    return DNSPlugin


def get_plugin_meta():
    return PluginMeta(
        "Antares", 2.0, "DNS查询"
    )
