from selenium import webdriver
from PIL import Image
from io import BytesIO
from register import command
import tempfile
import os
import global_vars
import threading
import urllib
import base64
import time
config = global_vars.CONFIG[__name__]


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "中国天气网爬虫"
    }


def take_screenshot(url)->bytes:
    func = """    function getElementPageLeft(element){
            var actualLeft=element.offsetLeft;
            var parent=element.offsetParent;
            while(parent!=null){
                actualLeft+=parent.offsetLeft+(parent.offsetWidth-parent.clientWidth)/2;
                parent=parent.offsetParent;
            }
            return actualLeft;
        }

        function getElementPageTop(element){
            var actualTop=element.offsetTop;
            var parent=element.offsetParent;
            while(parent!=null){
                actualTop+=parent.offsetTop+(parent.offsetHeight-parent.clientHeight)/2;
                parent=parent.offsetParent;
            }
            return actualTop;
        }"""
    driver = webdriver.PhantomJS(config.PHANTOMJS_PATH)
    driver.get(url)
    driver.set_window_size(1920, 3080)
    buf = BytesIO(driver.get_screenshot_as_png())
    image = Image.open(buf)
    elem = driver.find_element_by_class_name("left")
    left, top = driver.execute_script(
        func+"""\nelem=document.getElementsByClassName('left')[0];
    return [getElementPageLeft(elem),getElementPageTop(elem)]
        """)
    right = left+elem.size["width"]
    weatherChart = driver.find_element_by_id("weatherChart")
    bottom = driver.execute_script(
        func+"return getElementPageTop(document.getElementById('weatherChart'))")+weatherChart.size["height"]
    # 截取今天的天气
    today = image.crop((left, top, right, bottom))
    driver.find_element_by_css_selector(
        "ul#someDayNav li:nth-child(2)").find_element_by_tag_name("a").click()
    # 截取七天的天气
    buf = BytesIO(driver.get_screenshot_as_png())
    image = Image.open(buf)
    seven_day = driver.find_element_by_id("7d")
    bottom = driver.execute_script(
        func+"return getElementPageTop(document.getElementById('7d'))")+seven_day.size["height"]
    seven_day = image.crop((left, top, right, bottom))
    result = Image.new(
        "RGBA", (max(today.width, seven_day.width), today.height+seven_day.height))
    result.paste(today, (0, 0))
    result.paste(seven_day, (0, today.height))
    # result.save("z:/4.png")
    output = BytesIO()
    result.save(output, format="png")
    driver.quit()
    return output.getvalue()


@command(name="weather", help="查询天气")
def get_weather(bot, context, args):
    city = args[1]
    if city.strip() == "":
        bot.send(context, "请输入正确的城市名！")
        return
    begin = time.time()

    def handle():
        with urllib.request.urlopen("http://toy1.weather.com.cn/search?cityname="+urllib.parse.quote(city)) as url:
            # text = url.read().decode()
            data = eval(url.read().decode())
        # print(data)
        if len(data) == 0:
            bot.send(context, "未知城市: "+city)
            return
        image = take_screenshot(
            "http://www.weather.com.cn/weather1d/{}.shtml".format(data[0]["ref"].split("~")[0]))
        end = time.time()
        to_send = '[CQ:image,file=base64://{}]\n查询耗时 {}s.'.format(
            base64.encodebytes(image).decode("utf-8").replace("\n", ""), (end-begin))
        # print(to_send)
        bot.send(context, to_send)
    threading.Thread(target=handle).start()
