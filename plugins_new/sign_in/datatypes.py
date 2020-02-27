from dataclasses import dataclass

@dataclass
class SignInData:
    group_id:int
    user_id:int
    time:int
    duration:int
    score:int
    score_changes:int