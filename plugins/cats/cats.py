from register import command, console_command
from cqhttp import CQHttp
from util import print_log
import global_vars
import re
import oss2
import requests
import json
import threading
import random
import tempfile
import shutil
import base64
import urllib
from io import BytesIO
config = global_vars.CONFIG[__name__]


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "吸猫插件"
    }


def load():
    auth = oss2.Auth(config.ACCESS_KEY_ID, config.ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, config.ENDPOINT, config.BUCKET_NAME)
    global_vars.VARS["bucket"] = bucket


@console_command(name="sync-cats", help="同步猫猫图库")
def sync_cats(args):
    data = {}
    bucket = global_vars.VARS["bucket"]
    for file in oss2.ObjectIterator(bucket):
        if "/" not in file.key and not file.key.endswith(".jpg"):
            continue
        user, file_name, *_ = file.key.split("/")
        if user not in data:
            data[user] = {"image_list": []}
        data[user]["image_list"].append(file_name)
    print_log("Result: {}".format(data))
    save_data(data)


@command(name="吸猫", help="吸猫")
def suck_cats(bot: CQHttp, context, args):
    data = load_data()
    bucket: oss2.Bucket = global_vars.VARS["bucket"]
    if len(data) == 0:
        bot.send(context, "目前无人上传过猫猫图片.")
        return
    selected_user = None
    selected_file = None
    while args[-1] == "":
        del args[-1]
    if len(args) > 1:
        selected_user = args[1]
    else:
        choices = []
        for k, v in data.items():
            choices += [k]*len(v["image_list"])
        selected_user = random.choice(choices)
    print_log("user:{}".format(selected_user))
    if selected_user not in data:
        bot.send(context, "指定用户未上传过猫片")
        return
    if len(args) > 2:
        selected_file = str(args[2])
    else:
        selected_file = random.choice(data[selected_user]["image_list"])

    def send():
        file_name = "{}/{}".format(selected_user, selected_file)
        try:
            stream = bucket.get_object(
                file_name)
            encode = base64.encodebytes(
                stream.read()).decode().replace("\n", "")
            # print_log(encode)
            bot.send(context, "[CQ:image,file=base64://{}]\n来自{}的猫片{}".format(
                encode, selected_user, selected_file))
        except Exception as ex:
            bot.send(context, str(ex))
    threading.Thread(target=send).start()


@command(name="upload", help="上传猫猫图片")
def upload_cats(bot: CQHttp, context, args):
    if not str(context['group_id']) in config.WHITE_LIST_GROUPS:
        bot.send(context, "本群无权限上传图片!")
        return

    if len(args) < 2:
        bot.send(context, "请上传图片!")
        return
    uploader_id = str(context["sender"]["user_id"])
    data = load_data()

    def allocate_file_name():

        if uploader_id not in data:
            data[uploader_id] = {"image_list": []}
        # file_name = "%d.jpg" %
        next_name = len(data[uploader_id]["image_list"])
        while "%d.jpg" % next_name in data[uploader_id]["image_list"]:
            next_name += 1
        file_name = "%d.jpg" % next_name
        # data[uploader_id]["image_list"].append(file_name)
        return file_name
    pattern = re.compile(r"\[CQ:image.+url\=(?P<url>[^\[^\]]+)\]")
    result = pattern.search(args[1])
    if result is None:
        bot.send(context, "请上传图片")
        return
    url = result.group("url")
    bucket = global_vars.VARS["bucket"]

    def upload_image():
        name = allocate_file_name()
        print_log("Uploading %s" % name)
        bot.send(context, "{} 的猫猫图片 {} 开始上传.".format(uploader_id, name))
        buf = BytesIO()
        print_log("Downloading %s" % url)
        with urllib.request.urlopen(url) as src:
            while True:
                buffer = src.read(1024)
                if not buffer:
                    break
                if buf.tell() > config.IMAGE_SIZE_LIMIT:
                    bot.send(context, "{} 上传的图片 {} 过大".format(
                        uploader_id, name))
                    return
                buf.write(buffer)
        buf.flush()
        bucket.put_object("{}/{}".format(uploader_id, name), buf.getvalue())
        # bucket.put_object(name, )
        bot.send(context, "{} 的猫猫图片 {} 上传完成.".format(uploader_id, name))
        data[uploader_id]["image_list"].append(name)
        save_data(data)
    threading.Thread(target=upload_image).start()


def load_data()->dict:
    print_log(__file__)
    import os
    print_log(os.sys.path)
    config_path = os.path.join(os.path.dirname(__file__),"cats.json")
    if not os.path.exists(config_path):
        with open(config_path, "w") as file:
            file.write("{}")
    with open(config_path, "r") as file:
        text = file.read()
        obj = json.JSONDecoder().decode(text)
    return obj


def save_data(obj: dict):
    import os
    with open(os.path.join(os.path.dirname(__file__),"cats.json"), "w") as file:
        json.dump(obj, file)
