from common.plugin import Plugin
from common.config_loader import ConfigBase
from common.datatypes import PluginMeta
from common.countdown_bot import CountdownBot
from common.loop import TimeTuple
from common.command import ChatType
from common.event import GroupMessageEvent
import aiohttp
import urllib
from typing import Dict,List
from io import StringIO


class WeatherConfig(ConfigBase):
    # 和风天气 https://www.heweather.com
    APP_KEY = ""


class WeatherPlugin(Plugin):
    async def get_data(self, local: str, type1: str, type2: str) -> dict:
        async with self.aioclient.get(f"https://free-api.heweather.net/s6/{type1}/{type2}", params={
            "location": urllib.parse.quote(local),
            "key": self.config.APP_KEY,
            "lang": "zh"
        }) as resp:
            data = await resp.json()
        return data['HeWeather6'][0]

    def generate_location(self, data: Dict[str, str]) -> str:
        return f"""查询位置: {data["location"]},{data["parent_city"]},{data["admin_area"]},{data["cnty"]}
时区: {data["tz"]}
经度: {data["lon"]}
纬度: {data["lat"]}
"""

    def generate_weather(self, weather: Dict[str, str], air: Dict[str, str]) -> str:
        return f"""当前天气: {weather["cond_txt"]}
当前温度: {weather["tmp"]}摄氏度
风向风力: {weather["wind_dir"]} {weather["wind_sc"]}级
空气质量: {air["qlty"]}
空气质量指数(AQI): {air["aqi"]}
"""

    def generate_forecast(self, index: int, data: Dict[str, str]) -> str:
        return f"""{"今明后"[index]}天({data['date']}):
白天天气: {data['cond_txt_d']}
夜间天气: {data['cond_txt_n']}
最高温度: {data['tmp_max']}摄氏度
最低温度: {data['tmp_min']}摄氏度"""

    def command_weather(self, plugin, args: List[str], raw_string: str, context, evt: GroupMessageEvent):
        async def wrapper():
            weather_now = await self.get_data(args[0], "weather", "now")
            weather_forecast = await self.get_data(args[0], "weather", "forecast")
            if not weather_now['status'] == "ok":
                self.bot.send(context, f"Error: {weather_now['status']}")
                return
            if not weather_forecast['status'] == 'ok':
                self.bot.send(context, f"Error: {weather_forecast['status']}")
                return
            air_now = await self.get_data(weather_now['basic']['parent_city'], "air", "now")
            message = StringIO()
            message.write(self.generate_location(weather_now['basic']))
            message.write(f"更新时间:{weather_now['update']['loc']}\n\n")
            message.write(self.generate_weather(weather_now['now'],
                                                air_now['air_now_city'] if air_now['status'] == "ok" else {'qlty': "未知", 'aqi': '未知'}))
            message.write("\n最近三天:\n")
            for index, data in enumerate(weather_forecast['daily_forecast']):
                message.write(self.generate_forecast(index, data))
                if index >= 2:
                    break
                message.write('\n')
            self.bot.send(context, message.getvalue())
        self.bot.submit_async_task(wrapper())

    def on_enable(self):
        self.aioclient = aiohttp.ClientSession()
        self.bot: CountdownBot
        self.config: WeatherConfig
        self.register_command_wrapped(
            command_name="weather",
            command_handler=self.command_weather,
            help_string="查询天气 | weather [地名/城市代码/IP地址/经度,纬度] (单个地名半角逗号分割小到大的行政区排列)",
            chats={ChatType.discuss, ChatType.group, ChatType.private},
            alias=["天气"]
        )


def get_plugin_class():
    return WeatherPlugin


def get_config_class():
    return WeatherConfig


def get_plugin_meta():
    return PluginMeta(
        "weather", 2.0, "天气查询"
    )
