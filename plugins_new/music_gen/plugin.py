from common.plugin import Plugin
from common.datatypes import PluginMeta
from common.config_loader import ConfigBase
from common.event import MessageEvent, GroupMessageEvent
from common.command import ChatType
from common.countdown_bot import CountdownBot
from typing import List, Dict, Tuple
from pydub import AudioSegment
from redis import Redis, ConnectionPool
from io import StringIO
from .notes import *
from .pysynth_b import make_wav

import tempfile
import re
import sox
import os
import base64
import requests
import bs4
import flask


class MusicGenConfig(ConfigBase):
    # 默认BPM
    DEFAULT_BPM = 120
    # 最多的音符个数
    MAX_NOTES = 500
    # 单纯通过消息发送时，所允许的最多的音符个数
    MAX_NOTES_THROUGH_MESSAGE = 30
    # 默认音量
    DEFAULT_VOLUME = 1
    # Redis的地址
    REDIS_URI = "redis://127.0.0.1/0"
    # 下载文件超时时间,毫秒
    DOWNLOAD_TIMEOUT = 3*1000*60
    # 所存储的最多的文件数
    MAX_STORING_FILES = 10
    # 这些群单独的长度限制
    GROUP_LIMITS: Dict[int, int] = {

    }
    # 音乐最大长度，秒
    MAX_LENGTH_IN_SECONDS = 6*60


class MusicGenPlugin(Plugin):
    def on_enable(self):
        self.bot: CountdownBot
        self.config: MusicGenConfig
        self.connection_pool = ConnectionPool.from_url(self.config.REDIS_URI)
        self.logger.info("Redis connected..")
        self.register_command_wrapped(
            command_name="gen",
            command_handler=self.command_generate_music,
            help_string="生成音乐 | 帮助请使用 genhelp 指令查看",
            chats={ChatType.group}
        )
        self.register_command_wrapped(
            command_name="genhelp",
            command_handler=self.command_help,
            help_string="查看音乐生成器帮助",
            chats=ChatType.all()
        )
        self.register_command_wrapped(
            command_name="noteconvert",
            command_handler=self.command_noteconvert,
            help_string="转换简谱 | 使用genhelp指令查看帮助",
            chats=ChatType.all()
        )
        self.register_command_wrapped(
            command_name="convert-play",
            command_handler=self.command_convert_play,
            help_string="转换简谱并播放 | 使用genhelp指令查看帮助",
            chats={ChatType.group}
        )
        self.bot.server_app.route(
            "/music/download/<string:token>")(self.web_download_music_mp3)

    def web_download_music_mp3(self, token: str):
        client = Redis(connection_pool=self.connection_pool)
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

    def command_convert_play(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):

        def wrapper():
            filtered: List[str] = []
            splited = " ".join(args).split()
            if len(splited) > self.config.MAX_NOTES_THROUGH_MESSAGE:
                self.bot.client.send(context, "消息过长，请尝试使用Ubuntu Pastebin传递参数")
                return
            for item in splited:
                item = item.strip()
                if item.startswith("from:"):
                    url = item[item.index(":")+1:]
                    filtered.extend(self.load_from_ubntupastebin(url).split())
                else:
                    filtered.append(item)
            major = "C"
            bpm = self.config.DEFAULT_BPM
            for item in filtered:
                if item.startswith("major:"):
                    major = item[item.index(":")+1:]
                elif item.startswith("bpm:"):
                    bpm = int(item[item.index(":")+1:])
            note_string = " ".join(
                (x for x in filtered if not x.startswith("major") and not x.startswith("bpm")))
            result = self.noteconvert(
                f"major:{major} "+note_string,
            )
            self.generate_music(f"bpm:{bpm} "+result, context, evt)
        self.bot.submit_multithread_task(wrapper)

    def noteconvert(self, note_string: str):
        major = "C"
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
        buf = StringIO()
        for i, track in enumerate(tracks):
            buf.write(" ".join(track))
            if i != len(tracks)-1:
                buf.write("| \n")
        return buf.getvalue()

    def command_noteconvert(self, plugin, args: List[str], raw_string: str, context: dict, evt: MessageEvent):
        # if evt.group_id in self.config.DISABLE_GROUPS:
        #     self.bot.client.send(context, "本群禁止使用该指令")
        #     return
        splited = " ".join(args).split()
        if len(splited) > self.config.MAX_NOTES_THROUGH_MESSAGE:
            self.bot.client.send(context, "消息过长，请尝试使用Ubuntu Pastebin传递参数")
            return
        filtered: List[str] = []
        for item in splited:
            item = item.strip()
            if item.startswith("from:"):
                url = item[item.index(":")+1:]
                filtered.extend(self.load_from_ubntupastebin(url).split())
            else:
                filtered.append(item)

        self.bot.client.send(context, self.noteconvert(
            " ".join(filtered)
        )
        )

    def command_generate_music(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        # if evt.group_id in self.config.DISABLE_GROUPS:
        #     self.bot.client.send(context, "本群禁止使用该指令")
        #     return

        def wrapper():
            filtered: List[str] = []
            splited = " ".join(args).split()
            if len(splited) > self.config.MAX_NOTES_THROUGH_MESSAGE:
                self.bot.client.send(context, "消息过长，请尝试使用Ubuntu Pastebin传递参数")
                return
            for item in splited:
                item = item.strip()
                if item.startswith("from:"):
                    url = item[item.index(":")+1:]
                    # generate_music(, callback, callback)
                    # return
                    filtered.extend(self.load_from_ubntupastebin(url).split())
                else:
                    filtered.append(item)
            self.generate_music(
                " ".join(filtered),
                context,
                evt
            )
        self.bot.submit_multithread_task(wrapper)

    def store_into_redis(self, token: str, data: bytes):
        client = Redis(connection_pool=self.connection_pool)
        key = f"countdownbot-music-{token}"
        my_keys = list(client.keys("countdownbot-music-*"))
        # print(my_keys)
        if len(my_keys) >= self.config.MAX_STORING_FILES:
            self.logger.info("Too many files stored...")
            self.logger.info(my_keys)
            my_keys.sort(key=lambda x: client.pttl(x))
            self.logger.info(f"Dropping {my_keys[0]}")
            client.delete(my_keys[0])
        self.logger.info(f"{token} stored")
        client.set(key, data, px=self.config.DOWNLOAD_TIMEOUT)

    def load_from_ubntupastebin(self, url: str) -> str:
        # with requests.get(url) as urlf:
        #     soup = bs4.BeautifulSoup(urlf.text, "lxml")
        # code_pre = soup.select_one(".code > .paste > pre")
        # return str(list(code_pre.children)[1])
        with requests.get(url) as urlf:
            return urlf.text
    def generate_music(self, note_string: str, context: dict, evt: GroupMessageEvent):
        tracks: List[List[Tuple[str, int]]] = []
        bpm = self.config.DEFAULT_BPM
        total_minutes = 0.0

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
                    duration = float(duration)
                    if inversed_duration:
                        duration = beats/(float(duration))
                    if abs(float(duration)) < 0.1:
                        raise ValueError("abs(Duration) >= 0.1")
                    nonlocal total_minutes
                    total_minutes += 4/duration/float(bpm)
                    notes.append((
                        note_name, float(duration)
                    ))
                except Exception as ex:
                    self.bot.client.send(context, f"存在非法音符: {note}\n{ex}")
                    raise ValueError(f"存在非法音符: {note}\n{ex}")
            return notes
        string = note_string
        inversed = "inverse" in string
        string = string.replace("inverse", "")

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
            volume = [self.config.DEFAULT_VOLUME for i in range(track_count)]
        if "download" in string:
            string = string.replace("download", "")
            will_download = True
        else:
            will_download = False
        if len(volume) != track_count:
            self.bot.client.send(context, "音量个数需要与音轨个数相等.")
            return
        self.logger.info(volume)

        for track_string in string.split("|"):
            track_string = track_string.strip()
            if track_string:
                tracks.append(process_track(
                    track_string, inversed, int(beats)))
                if total_minutes*60 > self.config.MAX_LENGTH_IN_SECONDS:
                    self.bot.client.send(
                        context, f"单个音轨的长度不能超过{self.config.MAX_LENGTH_IN_SECONDS}秒")
                    return
                total_minutes = 0
        for i, track in enumerate(tracks):
            self.logger.info(f"音轨 {i+1} 长度 {len(track)}")
        notes_count = sum((len(x) for x in tracks))
        if notes_count > self.config.GROUP_LIMITS.get(evt.group_id, self.config.MAX_NOTES):
            self.bot.client.send(context, "超出音符数上限")
            return

        mp3_output = tempfile.mktemp(".mp3")

        track_files: List[str] = []
        combiner = sox.Combiner()
        self.bot.client.send(
            context, f"生成中...共计{len(tracks)}个音轨,{notes_count}个音符")
        for i, track in enumerate(tracks):
            track_file = tempfile.mktemp(".wav")
            try:
                make_wav(
                    track, bpm, fn=track_file, silent=True
                )
            except Exception as ex:
                self.bot.client.send(context, f"音轨{i+1}出现错误: {ex}")
                raise ex
            track_files.append(track_file)
        self.logger.info(f"track_files {track_files}")

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

        if will_download:
            import uuid
            import urllib.parse
            token = str(uuid.uuid1())
            self.store_into_redis(token, mp3_data)
            download_url = urllib.parse.urljoin(
                f"{self.bot.config.SERVER_URL}:{self.bot.config.POST_PORT}", f"/music/download/{token}")
            self.bot.client.send(
                context, f"请前往 {download_url} 下载您的文件,此链接将在 {self.config.DOWNLOAD_TIMEOUT} 毫秒后失效.")
        self.bot.client.send(context, base64_data)

    def command_help(self, plugin, args: List[str], raw_string: str, context: dict, evt: GroupMessageEvent):
        self.bot.client.send(context, f"""本功能基于PySynth，通过numpy输出wav的方式生成音频流。

    使用方式:
    gen [bpm:BPM(可选,用于指定BPM数(每分钟播放的四分音符的个数),默认为{self.config.DEFAULT_BPM})] [音轨1:音符1] [音轨1:音符2]....| [音轨2:音符1] [音轨2:音符2...]

    已知Bug:
    - 休止符不支持附点

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
    volume:x --- 指定所有音轨的音量均为x,默认为{self.config.DEFAULT_VOLUME}
    volume:a,b,c... --- 依次指定各个音轨的音量,音量个数需要与音轨个数相等
    
    download:
    添加此参数将会允许用户下载所生成的音乐文件
    """)


def get_plugin_class():
    return MusicGenPlugin


def get_config_class():
    return MusicGenConfig


def get_plugin_meta():
    return PluginMeta(
        author="officeyutong",
        version=2.0,
        description="音乐生成"
    )
