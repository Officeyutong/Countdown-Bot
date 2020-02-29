import global_vars
import os
from cqhttp import CQHttp
from flask import session, request, Flask
import time
import random
config = global_vars.CONFIG[__name__]
WEB_DIR = os.path.join(os.path.dirname(__file__), "web/")
bot_ins: CQHttp = global_vars.VARS["bot"]
web_app: Flask = global_vars.VARS["web_app"]


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "HelloPaint验证端(用于发送验证码)"
    }


def make_response(ok, result=None):
    from json import JSONEncoder
    return JSONEncoder().encode({"ok": ok, "result": result})


@web_app.route("/paintboard/send_code", methods=["POST"])
def paintboard_send_code():
    token, target, content = request.form["token"], request.form["target"], request.form["content"]
    if token != config.ACCESS_KEY:
        return make_response(False, {"message": "token错误"})
    bot_ins.send_private_msg(user_id=target, message=content)
    return make_response(True)
