from register import command
from global_vars import CONFIG
import threading
import urllib.parse,urllib.request,urllib.error
import json
import base64
from util import print_log

config = CONFIG[__name__]

def plugin():
    return {
        "author":"Antares",
        "version":1.0,
        "description":"网易云点歌"
    }
 
def login():
    if config.LOGIN_MODE == "phone":
        url = config.API_URL + f"/login/cellphone?phone={config.PHONE}&password={config.PASSWORD}" 
    elif config.LOGIN_MODE == "email":
        url = config.API_URL + f"/login?email={config.EMAIL}&password={config.PASSWORD}"
    else:
        return
    
    with urllib.request.urlopen(url) as f:
        data = json.JSONDecoder().decode(f.read().decode("utf8"))
    
    if data['code'] == 200:
        print_log("登陆成功!")
    else:
        print_log("登陆失败！请检查账号密码！")


def search_music(key:str) -> dict:
    url = config.API_URL + f"/search?keywords={urllib.parse.quote(key)}&limit={config.SEARCH_LIMIT}"
    with urllib.request.urlopen(url) as f:
        data = json.JSONDecoder().decode(f.read().decode("utf8"))
    if 'result' in data:
        return data['result']
    else:
        return {'songCount':0}

def check_music(music_id:int) -> bool:
    url = config.API_URL + f"/check/music?id={music_id}"
    try:
        with urllib.request.urlopen(url) as f:
            data = json.JSONDecoder().decode(f.read().decode("utf8"))
    except urllib.error.HTTPError as err:
        print_log(err)
        return False
    return data['success']

def get_music_url(music_id:int) -> str:
    url = config.API_URL + f"/song/url?id={music_id}&br=320000"
    with urllib.request.urlopen(url) as f:
        data = json.JSONDecoder().decode(f.read().decode("utf8"))
    return data['data'][0]['url']

@command(name="music",help="网易云音乐点歌")
def music(bot,context,args):
    while args[-1] == "":
        del args[-1]

    def handle():
        raw = False
        link = False
        if args [-1] == "raw":
            raw = True
            del args[-1]
        elif args[-1] == "link":
            link = True
            del args[-1]

        music_id = -1
        if args[1] == "id":
            try:
                music_id = int(args[2])
            except ValueError as err:
                print_log(err)
                bot.send(context,"请输入正确的id")
                return
        login()

        if music_id != -1:
            if not check_music(music_id):
                bot.send(context,"id对应的音乐不存在或无版权")
                return
            else:
                if raw :
                    bot.send(context,f"[CQ:music,type=163,id={music_id}]")
                else:
                    url = get_music_url(music_id)
                    if link:
                        bot.send(context, url)
                    else:
                        bot.send(context,f"[CQ:record,file={url}]")
                return
        
        key = " ".join(args[1:])
        data = search_music(key)

        if data['songCount'] == 0:
            bot.send(context,"您搜索的歌曲不存在")
            return
        
        for item in data['songs']:
            music_id = item['id']
            if check_music(music_id):
                if raw:
                    bot.send(context,f"[CQ:music,type=163,id={music_id}]")
                else:
                    url = get_music_url(music_id)
                    if link:
                        bot.send(context,url)
                    else:
                        bot.send(context,f"[CQ:record,file={url}]")
                return
        
        bot.send(context,"您搜索的歌曲不存在或无版权")
        
    threading.Thread(target=handle).start()
           
                