from dataclasses import dataclass


@dataclass
class SignInData:
    group_id: int
    user_id: int
    time: int = 0
    duration: int = 0
    score: int = 0
    score_changes: int = 0


@dataclass
class UserData:
    group_id: int
    user_id: int
    score: int
