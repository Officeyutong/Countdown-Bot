import global_vars
from util import print_log
from register import command, schedule_loop
from global_vars import config as global_config

config = global_vars.CONFIG[__name__]


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "基础广播功能"
    }


@command(name="broadcast", help="在当前群进行广播")
def broadcast_cmd(bot, context, args=None):
    # print_log("broadcasting..")
    group_id = context.get("group_id", -1)
    if group_id != -1:
        broadcast_at_group(group_id)


def get_countdown_list(url):
    import json
    import urllib
    decoder = json.JSONDecoder()
    result = None
    with urllib.request.urlopen(url) as f:
        result = decoder.decode(f.read().decode("utf-8"))
    return result


def broadcast_at_group(group_id: int, content=None):
    bot = global_vars.VARS["bot"]
    if content is None:
        content = get_countdown_list(config.LIST_URL)
    print_log("Broadcasting at group %d with content %s" % (group_id, content))
    for item in get_broadcast_content(content[str(group_id)]):
        try:
            bot.send_group_msg(group_id=group_id, message=item)
        except Exception as ex:
            print_log(ex)
            # raise ex


@schedule_loop(hour=config.BROADCAST_HOUR, minute=config.BROADCAST_MINUTE,  name="Broadcast")
def execute_broadcast():
    text = get_countdown_list(config.LIST_URL)
    for group in text:
        broadcast_at_group(int(group), text)


def get_broadcast_content(broadcast_list: list):
    # print_log("broadcasting..")
    result = []
    countdown_list = broadcast_list
    from datetime import datetime
    from datetime import timedelta
    today = datetime.now()
    for item in countdown_list:
        print_log(item)
        name = item["name"]
        exp_time = datetime.strptime(item["date"], "%Y-%m-%d")
        delta: timedelta = exp_time-today+timedelta(days=1)
        # days=delta.days+1
        mouths = delta.days//30
        days = delta.days % 30
        if delta.days < 0:
            continue
        text = ""
        if delta.days > 0:
            if mouths > 0:
                text = "距离 %s 还有 %d 天 (%d个月%s)." % (
                    name, delta.days, mouths, ("%d天" % days) if days != 0 else "整")
            else:
                text = "距离 %s 还有 %d 天." % (name, delta.days)
        else:
            text = "今天是 %s ." % (name)
        print_log(text)
        result.append(text)
    return result
