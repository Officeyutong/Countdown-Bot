from register import command
from global_vars import CONFIG
import base64
import tempfile
import os
from aip import AipSpeech
import threading
config = CONFIG[__name__]


def plugin():
    return {
        "author": "Antares",
        "version": 1.0,
        "description": "文字朗读"
    }


@command(name="read", help="文字转语音")
def read(bot, context, args):
    string = " ".join(args[1:])
    if len(string) > config.MAX_STRING_LENGTH:
        bot.send(context, "字符串过长")
        return

    def handle():
        client = AipSpeech(config.APP_ID, config.API_KEY, config.SECRET_KEY)
        voice = client.synthesis(string, 'zh', 1, {
            'vol': config.VOLUME,
            'per': 4,
            'spd': config.SPEED
        })
        
        if not isinstance(voice, dict):
            result = str(base64.encodebytes(voice).decode().replace("\n", ""))
            bot.send(context, "[CQ:record,file=base64://{}]".format(result))
        else:
            bot.send(context, "转换语音失败，请检查是否含有非法字符")
    
    threading.Thread(target=handle).start()
