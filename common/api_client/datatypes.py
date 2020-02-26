from dataclasses import dataclass

from enum import Enum


class Sex(Enum):
    male = "male"
    female = "female"
    unknown = "unknown"


@dataclass
class StrangerInfo:
    user_id: int
    nickname: str
    sex: Sex
    age: int

    def __init__(self, ctx: dict):
        self.user_id = ctx["user_id"]
        self.nickname = ctx["username"]
        self.sex = Sex(ctx["sex"])
        self.age = ctx["age"]
