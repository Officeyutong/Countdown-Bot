from register import command
from cqhttp import CQHttp
from typing import List, Dict, Union

from pyecharts.charts import Map
from pyecharts.options import InitOpts, VisualMapOpts, TitleOpts
from pyecharts.render import make_snapshot
# from snapshot_selenium import snapshot
# from selenium import webdriver
from snapshot_phantomjs import snapshot
from threading import Thread
import global_vars
config = global_vars.CONFIG[__name__]


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "丁香园2019nCov疫情播报"
    }


def make_province_image(data: Dict[str, Union[Dict, int, str]], update_time) -> bytes:
    snapshot.PHANTOMJS_EXEC = config.PHANTOMJS_PATH
    current_map = Map(InitOpts(
        "450px", "400px",
        bg_color="white"
    ))
    max_val = max((x["confirmedCount"] for x in data["cities"]))
    current_map.add(
        series_name="确诊分布",
        data_pair=[
            (city["cityName"]+"市", city["confirmedCount"]) for city in data["cities"]
        ]+[
            (city["cityName"], city["confirmedCount"]) for city in data["cities"]
        ],
        maptype=data["provinceShortName"],
    )
    current_map.set_global_opts(
        visualmap_opts=VisualMapOpts(max_=max_val, is_piecewise=False),
        title_opts=TitleOpts(title=f"{data['provinceName']}确诊病例分布图",
                             subtitle=f"截止{update_time},本省已有 {data['confirmedCount']} 人确诊, {data['curedCount']} 人治愈, {data['deadCount']} 人死亡")
    )
    import tempfile
    import base64
    import os
    target_file = tempfile.mktemp(".png")
    make_snapshot(snapshot, current_map.render(),
                  target_file, is_remove_html=True, pixel_ratio=1)
    print(target_file)
    with open(target_file, "rb") as f:
        image_data = f.read()
    os.remove(target_file)
    return image_data


@command(name="covid19", help="查询COVID-19（原2019-nCov）疫情 | covid19 (省名)")
def dxy_query(bot: CQHttp, context=None, args: List[str] = None):
    import bs4
    import requests
    import re
    import json
    import time
    import datetime
    with requests.get("https://3g.dxy.cn/newh5/view/pneumonia") as urlf:
        soup = bs4.BeautifulSoup(urlf.content.decode("utf-8"), "lxml")
    script = soup.select_one("#getAreaStat")
    expr = re.compile(r"(\[.*\])")

    data: List[Dict[str, dict]] = json.JSONDecoder().decode(
        expr.search(script.string).groups()[0])
    statistics = json.JSONDecoder().decode(re.compile(
        r"= (\{.*\})\}catch").search(soup.select_one("#getStatisticsService").string).groups()[0])

    # broadcast = soup.select_one(".count___3GCdh)
    # total_confirmed = sum((item["confirmedCount"] for item in data))
    # total_suspected = sum((item["suspectedCount"] for item in data))
    # total_cured = sum((item["curedCount"] for item in data))
    # total_dead = sum((item["deadCount"] for item in data))
    update_time: time.struct_time = time.localtime(
        statistics["modifyTime"]//1000)
    broadcast = f"{statistics['confirmedCount']} 确认 | {statistics['suspectedCount']} 疑似 | {statistics['curedCount']} 治愈 | {statistics['deadCount']} 死亡\n更新于{time.strftime('%Y.%m.%d %H:%M:%S', update_time)}"
    from io import StringIO
    buf = StringIO()
    buf.write("数据来源: 丁香医生\n")
    # buf.write(str(soup.select_one(".title___2d1_B").cmd.text)+"\n")
    buf.write(broadcast)
    buf.write("\n\n")

    def generate_line(obj):
        return f"{obj['provinceName'] if 'provinceName' in obj else obj['cityName']} 已确认 {obj['confirmedCount']} 疑似 {obj['suspectedCount']} 治愈 {obj['curedCount']} 死亡 {obj['deadCount']}"

    def handle_province(obj):
        buf.write(generate_line(obj))
        buf.write("\n\n")
        for city in obj["cities"]:
            buf.write(generate_line(city)+"\n")
        bot.send(context, buf.getvalue())

        def generate_image():
            import base64
            image_data = make_province_image(
                obj, time.strftime('%Y.%m.%d %H:%M:%S', update_time))
            print("Image generated.")
            # print(image_data[:100])
            # bot.send(context, f"[CQ:image,file=base64://{base64_data}]")
            bot.send(context, "[CQ:image,file=base64://{}]".format(
                base64.encodebytes(image_data).decode(
                    "utf-8").replace("\n", "")
            ))
        Thread(target=generate_image).start()

    def handle_global():
        for item in data:
            buf.write(generate_line(item)+"\n")
        bot.send(context, buf.getvalue())

    while args and args[-1].strip() == "":
        args.pop()
    print(args)
    if len(args) == 1:
        handle_global()
    else:
        for item in data:
            if args[1] in item["provinceName"]:
                handle_province(item)
                return
        bot.send(context, "请输入正确的省份名称")


@command(name="covnews", help="查询COVID-19（原2019-nCov）最近5条实时播报")
def ncov_news(bot: CQHttp, context=None, args: List[str] = None):
    import bs4
    import requests
    import re
    import json
    import time
    import datetime
    with requests.get("https://3g.dxy.cn/newh5/view/pneumonia") as urlf:
        soup = bs4.BeautifulSoup(urlf.content.decode("utf-8"), "lxml")
    script = soup.select_one("#getTimelineService")
    expr = re.compile(r"(\[.*\])")

    data: List[Dict[str, dict]] = json.JSONDecoder().decode(
        expr.search(script.string).groups()[0])
    statistics = json.JSONDecoder().decode(re.compile(
        r"= (\{.*\})\}catch").search(soup.select_one("#getStatisticsService").string).groups()[0])
    update_time: time.struct_time = time.localtime(
        statistics["modifyTime"]//1000)
    # print(broadcast.text)
    from io import StringIO
    buf = StringIO()
    buf.write(
        f"数据来源: 丁香医生\n更新于{time.strftime('%Y.%m.%d %H:%M:%S', update_time)}")
    # buf.write(str(soup.select_one(".mapTitle___2QtRg").text)+"\n")
    buf.write("\n\n")
    for item in data[:5]:
        buf.write(f"""{item["title"]} - {item["infoSource"]} - {item["pubDateStr"]}
        {item["sourceUrl"]}
        {item["summary"]}

        """)
    bot.send(context, buf.getvalue())
