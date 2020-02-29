from typing import List, Callable,Tuple
from common.countdown_bot import LOGGER as logger
from io import StringIO
from .pysynth_b import make_wav
from pydub import AudioSegment
import base64
import re
import tempfile
import sox

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
                except:
                    # print(f"Bad note: {note}")
                    logger.error(f"Bad note: {note}")
                    raise
        else:
            result.append(note)
    return result



