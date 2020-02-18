from register import command
from global_vars import CONFIG
import threading
import urllib
config = CONFIG[__name__]

def plugin():
    return {
        "author": "Antares",
        "version": 1.0,
        "description": "天气查询"
    }

def get_now_weather(local, key):
    url = "https://free-api.heweather.net/s6/weather/now?location=%s&key=%s" % (str(urllib.parse.quote(local)), key)
    import json
    data = None
    with urllib.request.urlopen(url) as f:
        data = json.JSONDecoder().decode(f.read().decode("utf-8"))
    return data['HeWeather6'][0]

def get_air(local, key):
    url = "https://free-api.heweather.net/s6/air/now?location=%s&key=%s" % (str(urllib.parse.quote(local)), key)
    import json
    data = None
    with urllib.request.urlopen(url) as f:
        data = json.JSONDecoder().decode(f.read().decode("utf-8"))
    return data['HeWeather6'][0]

def get_forecast_weather(local, key):
    url = "https://free-api.heweather.net/s6/weather/forecast?location=%s&key=%s" % (str(urllib.parse.quote(local)), key)
    import json
    data = None
    with urllib.request.urlopen(url) as f:
        data = json.JSONDecoder().decode(f.read().decode("utf-8"))
    return data['HeWeather6'][0]

@command(name="天气", help="查询天气")
def weather(bot, context, args):

    while args[-1] == "":
        del args[-1]
        
    def handle():
        now_weather = get_now_weather(args[1], config.KEY)
        forecast_weather = get_forecast_weather(args[1], config.KEY)

        if not now_weather['status'] == "ok":
            bot.send(context,"Now Weather Error: %s"% now_weather['status'])
            return

        if not forecast_weather['status'] == "ok":
            bot.send(context,"Forecast Weather Error: %s"% forecast_weather['status'])
            return

        now_air = get_air(now_weather['basic'][
            'parent_city' if 'parent_city' in now_weather['basic'] else 'location'], config.KEY)

        if not now_air['status'] == "ok":
            now_air['air_now_city'] = {'qlty':"未知",'aqi':'未知'}
        
        location_data = "查询位置:%s,%s,%s,%s\n时区:%s\n更新时间:%s\n" % (
            now_weather['basic']['location'], now_weather['basic'][
                'parent_city' if 'parent_city' in now_weather['basic'] else 'location'],
            now_weather['basic'][
                'admin_area' if 'admin_area' in now_weather['basic'] else 'location'],
            now_weather['basic']['cnty'], now_weather['basic']['tz'], now_weather['update']['loc'])
        
        now_data = "当前天气:%s\n当前温度:%s摄氏度\n风向风力:%s %s级\n空气质量:%s\n空气质量指数(AQI):%s\n" % (
            now_weather['now']['cond_txt'], now_weather['now']['tmp'],
            now_weather['now']['wind_dir'], now_weather['now']['wind_sc'],
            now_air['air_now_city']['qlty'], now_air['air_now_city']['aqi'])

        more_days = []
        for item in forecast_weather['daily_forecast']:
            more_days.append("天(%s):\n白天天气:%s\n夜间天气:%s\n最高温度:%s摄氏度\n最低温度:%s摄氏度" %(
                item['date'],item['cond_txt_d'],item['cond_txt_n'],item['tmp_max'],item['tmp_min']
            ))

        message="%s\n%s\n最近三天:\n今%s\n明%s\n后%s" % (
            location_data, now_data, more_days[0], more_days[1], more_days[2])
        bot.send(context,message)
        
    threading.Thread(target=handle).start()
