from common.datatypes import PluginMeta
from common.plugin import dataclass_wrapper

from register import command
from global_vars import CONFIG, VARS
from .pysynth_b import make_wav
from pysynth_b import mix_files
from cqhttp import CQHttp
from typing import List, Tuple, Callable
from pydub import AudioSegment
from redis import Redis, ConnectionPool
# from flask import Flask
import global_vars
import flask
import base64
import threading
import tempfile
import os
import sox
import requests
import bs4
# import numpy as np
# import wave
config = CONFIG.get(__name__, None)
plugin = dataclass_wrapper(lambda: PluginMeta(
    author="officeyutong",
    version=1.0,
    description="生成音乐"
))

web_app: flask.Flask = VARS["web_app"]


def load():
    # 创建Redis连接池
    global connection_pool
    connection_pool = ConnectionPool.from_url(config.REDIS_URI)
    print("Redis连接池已加载..")


@web_app.route("/music/download/<string:token>")
def download_music_mp3(token: str):
    client = Redis(connection_pool=connection_pool)
    key = f"countdownbot-music-{token}"
    if not client.exists(key):
        # return 404, "Bad token"
        flask.abort(404)
    # file_bytes=
    from io import BytesIO
    buf = BytesIO(client.get(key))
    buf.seek(0)
    # client.delete(key)
    return flask.send_file(buf, as_attachment=True, attachment_filename=f"{token}.mp3", conditional=True)


def store_into_redis(token: str, data: bytes):
    client = Redis(connection_pool=connection_pool)
    key = f"countdownbot-music-{token}"
    my_keys = list(client.keys("countdownbot-music-*"))
    # print(my_keys)
    if len(my_keys) >= config.MAX_STORING_FILES:
        print("Too many files stored...")
        print(my_keys)
        my_keys.sort(key=lambda x: client.pttl(x))
        print(f"Dropping {my_keys[0]}")
        client.delete(my_keys[0])
    print(token, "stored")
    client.set(key, data, px=config.DOWNLOAD_TIMEOUT)


def load_from_ubntupastebin(url: str) -> str:
    with requests.get(url) as urlf:
        soup = bs4.BeautifulSoup(urlf.text, "lxml")
    code_pre = soup.select_one(".code > .paste > pre")
    return str(list(code_pre.children)[1])


def parse_major(major_note: str) -> int:
    """
    解析基准音,返回绝对音高
    [b或#或忽略][音符]
    """
    BASE_MAPPING = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11
    }
    result = 0
    if major_note[0] in {"b", "#"}:
        result += {"b": -1, "#": 1}[major_note[0]]
        major_note = major_note[1:]
    return result+BASE_MAPPING[major_note[0].upper()]


def parse_note(note: str) -> int:
    """
    解析简谱,返回绝对音高
    [b或#或忽略][音符][八度(默认为4)]
    例如#12 #23
    """
    NOTE_LIST = [0, 2, 4, 5, 7, 9, 11]
    result = 0
    if note[0] in {"#", "b"}:
        result += {"b": -1, "#": 1}[note[0]]
        note = note[1:]
    note_chr = note[0]
    octave = 4
    # starred = False
    # left, right = note[1:].split(".", 1)
    if len(note) == 2:
        octave = int(note[1])
    # print("octave =", octave)
    result += NOTE_LIST[ord(note_chr)-ord('1')]
    result += 12*octave
    return result


def transform_single_note(note: str, major_height: int) -> str:
    NOTE_LIST = ["c", "c#", "d", "d#", "e",
                 "f", "f#", "g", "g#", "a", "a#", "b"]
    # print("transforming ", note)
    # 特殊的用以标记的音符不处理
    if "." not in note:
        return note
    note, duration = note.split(".", 1)
    starred = note[-1] == '*'
    if starred:
        note = note[:-1]
    height = major_height+parse_note(note)
    return f"{NOTE_LIST[height%12]}{height//12}{'*' if starred else ''}.{duration}"

# 将简谱转换为PySynth谱


def transform_notes(notes: List[str], major: str):
    """
    转换全部音符
    每个音符形如[#或b或空][1...7][八度(可空,默认为4)][*加重符号,可选].[节拍]

    输出形如
    [a...g音符名][#或b,可选][八度,可空,默认为4][*加重符号].[节拍]
    """
    major_height = parse_major(major)
    result = []
    for note in notes:

        if "r" not in note:
            if note.strip():
                try:
                    result.append(transform_single_note(
                        note.strip(), major_height))
                except Exception as ex:
                    print(f"Bad note: {note}")
                    raise
        else:
            result.append(note)
    return result


def noteconvert(note_string: str, update_status: Callable[[str], None], finish_callback: Callable[[str], None]):
    major = "C"
    try:
        tracks: List[List[str]] = []
        for track in note_string.split("|"):
            filtered = []
            for note in track.split(" "):
                note = note.strip()
                if note:
                    # print(note)
                    if note.startswith('major:'):
                        major = note[note.index(":")+1:]
                    else:
                        filtered.append(note)
            # print(tracks)
            tracks.append(transform_notes(filtered, major))
        from io import StringIO
        buf = StringIO()
        for i, track in enumerate(tracks):
            buf.write(" ".join(track))
            if i != len(tracks)-1:
                buf.write("| \n")
        finish_callback(buf.getvalue())

    except Exception as ex:
        # bot.send(context, f"发生错误: {ex}")
        update_status(f"发生错误: {ex}")
        raise ex


@command(name="convert-play", help="转换简谱并播放 | 使用genhelp指令查看帮助")
def convert_play(bot: CQHttp, context: dict, args: List[str]):
    def callback(x): bot.send(context, x)
    filtered: List[str] = []
    for item in " ".join(args[1:]).split():
        item = item.strip()
        if item.startswith("from:"):
            url = item[item.index(":")+1:]
            filtered.extend(load_from_ubntupastebin(url).split())
        else:
            filtered.append(item)
    major = "C"
    bpm = config.DEFAULT_BPM
    for item in filtered:
        if item.startswith("major:"):
            major = item[item.index(":")+1:]
        elif item.startswith("bpm:"):
            bpm = int(item[item.index(":")+1:])
    note_string = " ".join(
        (x for x in filtered if not x.startswith("major") and not x.startswith("bpm")))
    noteconvert(
        f"major:{major} "+note_string,
        callback,
        lambda result: generate_music(f"bpm:{bpm} "+result, callback, callback)
    )


@command(name="noteconvert", help="转换简谱 | 使用genhelp指令查看帮助")
def noteconvert_command(bot: CQHttp, context: dict, args: List[str] = None):
    def callback(x): return bot.send(context, x)
    # noteconvert(" ".join(args[1:]), callback, callback)
    filtered: List[str] = []
    for item in " ".join(args[1:]).split():
        item = item.strip()
        if item.startswith("from:"):
            url = item[item.index(":")+1:]
            # noteconvert(, callback, callback)
            # return
            filtered.extend(load_from_ubntupastebin(url).split())
        else:
            filtered.append(item)
    noteconvert(" ".join(filtered), callback, callback)


def generate_music(note_string: str, updater: Callable[[str], None], callback: Callable[[str], None]):
    tracks: List[List[Tuple[str, int]]] = []
    bpm = config.DEFAULT_BPM

    def process_track(string: str, inversed_duration: bool, beats: int):
        notes: List[Tuple[str, int]] = []
        # print(f"Processing track '{string}'")
        for note_ in string.split():
            note = note_.strip()
            if not note:
                continue
            if note.startswith("bpm:"):
                nonlocal bpm
                bpm = int(note[note.index(":")+1:])
                continue
            try:
                note_name, duration = note.split(".", 1)
                if inversed_duration:
                    duration = beats/(float(duration))
                if abs(float(duration)) < 0.1:
                    raise ValueError("abs(Duration) >= 0.1")
                notes.append((
                    note_name, float(duration)
                ))
            except Exception as ex:
                updater(f"存在非法音符: {note}\n{ex}")
                raise ValueError(f"存在非法音符: {note}\n{ex}")
        return notes
    string = note_string
    # inversed4 = "inverse4" in string
    inversed = "inverse" in string
    string = string.replace("inverse", "")
    import re
    if "beats" in string:

        expr = re.compile(r"beats:([0-9]{1,2})")
        beats = expr.search(string).groups()[0]
        string = string.replace(f"beats:{beats}", "")
    else:
        beats = 4
    track_count = string.count("|")+1
    if "volume:" in string:
        matched = re.compile(
            r"volume:([,0-9]+)").search(string).groups()[0]
        volume = [int(x) for x in matched.split(",")]
        string = string.replace(f"volume:{matched}", "")
        if len(volume) != track_count:
            if len(volume) == 1:
                volume = [volume[0] for i in range(track_count)]
    else:
        volume = [config.DEFAULT_VOLUME for i in range(track_count)]
    if "download" in string:
        string = string.replace("download", "")
        will_download = True
    else:
        will_download = False
    if len(volume) != track_count:
        updater("音量个数需要与音轨个数相等.")
        return
    print(volume)

    for track_string in string.split("|"):
        track_string = track_string.strip()
        if track_string:
            # print("track:"+track_string)
            tracks.append(process_track(
                track_string, inversed, int(beats)))
    # print(tracks)
    for i, track in enumerate(tracks):
        print(f"音轨 {i+1} 长度 {len(track)}")
    notes_count = sum((len(x) for x in tracks))
    if notes_count > config.MAX_NOTES:
        updater("超出音符数上限")
        return

    mp3_output = tempfile.mktemp(".mp3")

    def process():
        track_files: List[str] = []
        combiner = sox.Combiner()
        updater(f"生成中...共计{len(tracks)}个音轨,{notes_count}个音符")
        for i, track in enumerate(tracks):
            track_file = tempfile.mktemp(".wav")
            try:
                make_wav(
                    track, bpm, fn=track_file, silent=True
                )
            except Exception as ex:
                updater(f"音轨{i+1}出现错误: {ex}")
                raise ex
            track_files.append(track_file)
        print(track_files)

        if len(track_files) == 1:
            wav_output = track_files[0]
        else:
            wav_output = tempfile.mktemp(".wav")
            combiner.build(track_files, wav_output, "mix-power", volume)
        song = AudioSegment.from_wav(wav_output)
        song.export(mp3_output)
        with open(mp3_output, "rb") as f:
            mp3_data = f.read()
            base64_data = "[CQ:record,file=base64://{}]".format(
                base64.encodebytes(mp3_data).decode(
                    "utf-8").replace("\n", ""))
        os.remove(wav_output)
        os.remove(mp3_output)
        # print(mp3_output)

        for file in track_files:
            if os.path.exists(file):
                os.remove(file)
        callback(base64_data)
        if will_download:
            import uuid
            import urllib.parse
            token = str(uuid.uuid1())
            store_into_redis(token, mp3_data)
            download_url = urllib.parse.urljoin(
                f"{global_vars.config.SERVER_URL}:{global_vars.config.POST_PORT}", f"/music/download/{token}")
            updater(
                f"请前往 {download_url} 下载您的文件,此链接将在 {config.DOWNLOAD_TIMEOUT} 毫秒后失效.")

    threading.Thread(target=process).start()


@command(name="gen", help="生成音乐 | 帮助请使用 genhelp 指令查看")
def generate_music_command(bot: CQHttp, context: dict, args: List[str] = None):
    def callback(msg): return bot.send(context, msg)
    filtered: List[str] = []
    for item in " ".join(args[1:]).split():
        item = item.strip()
        if item.startswith("from:"):
            url = item[item.index(":")+1:]
            # generate_music(, callback, callback)
            # return
            filtered.extend(load_from_ubntupastebin(url).split())
        else:
            filtered.append(item)
    generate_music(" ".join(filtered), callback, callback)

# @command(name="merge-music",help="合并音频文件 ")

@command(name="genhelp", help="查看音乐生成器帮助")
def genhelp(bot: CQHttp, context: dict, *args):
    bot.send(context, f"""本功能基于PySynth，通过numpy输出wav的方式生成音频流。

    使用方式:
    gen [bpm:BPM(可选,用于指定BPM数(每分钟播放的四分音符的个数),默认为{config.DEFAULT_BPM})] [音轨1:音符1] [音轨1:音符2]....| [音轨2:音符1] [音轨2:音符2...]

    其中以|分割不同音轨
    其中音符的格式如下:
    [音符名(a-g,r表示休止符)][#或b(可选,#为升调,b为降调)][八度(可选,默认为4)][*(可选,表示重音)].[节拍,x表示x分音符或该音符占y分音符之比(见下文),-x表示x分附点]
    例如以下均为合法音符
    c.1   --- 普通的音符C,四拍
    c*.2  --- 普通的音符C,重音,两拍
    g5.3  --- 音符G,高一个八度,三分之四个四分音符
    g5*.1 --- 音符G,高一个八度,重音,四拍
    c#5*.2 --- 音符C,升调,高一个八度,重音,两拍
    c.-2 --- 音符C,二分附点
    以下为部分合法的指令调用:
    gen bpm:130 c.1 d.1 e.1 f.1 g.1 a.1 b.1
    
    # Dotted notes can be written in two ways:
    # 1.33 = -2 = dotted half
    # 2.66 = -4 = dotted quarter
    # 5.33 = -8 = dotted eighth

    关于简谱转换:
    可以使用notecover指令从简谱转换谱子到PySynth的格式
    其使用方式为
    noteconvert [major:大调,可选,例如#G,A,C,默认为C] [简谱音符1] [简谱音符2]... | [音轨2...]
    其中简谱音符的格式为:
    [#或b或留空(表示升调或降调)][音符,1...7或r,其中r表示休止符][八度(可空,默认为4)][*,重音符号,可空].[节拍]
    其中节拍参考PySynth谱部分
    以下为合法的指令调用:
    noteconvert major:bB 5.4 3.4 2.4 1.4 2.8 1.8 2.4 5.-4 r.8 5.4 3.4 2.4 1.4 2.8 1.8 5.4 3.-4 r.8
    
    关于简谱转换并播放:
    基本与noteconvert指令相同,但可以使用bpm:指定BPM

    关于从UbuntuPastebin下载:
    由于QQ的限制,单条消息长度不能超过4.5K，故本插件的gen,noteconvert,convert-play指令均支持从UbuntuPastebin下载数据.
    使用方式:
    使用gen,noteconvert,convert-play指令时,使用from:url来指定UbuntuPastebin的URL,比如:
    convert-play from:https://pastebin.ubuntu.com/p/xxxxxxxx/
    使用此方式时,除了from:参数外,其他参数均会被忽略

    特殊参数:
    
    inverse 与 beats:
    当乐谱中出现inverse参数时,节拍x表示的意义将会变成"这个音占y分音符的比例",其中y通过另一个参数beats指定,默认为4
    例如以下调用
    convert-play major:F bpm:120 inverse beats:3 1.1 2.1 3.1
    将会生成三个三分音符
    
    volume:
    此参数用于指定多个音轨的音量,有以下两种使用方式
    volume:x --- 指定所有音轨的音量均为x,默认为{config.DEFAULT_VOLUME}
    volume:a,b,c... --- 依次指定各个音轨的音量,音量个数需要与音轨个数相等
    
    download:
    添加此参数将会允许用户下载所生成的音乐文件
    """)
