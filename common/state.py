from typing import List, Callable

StateHandler = Callable[[], str]


class StateManager:
    def __init__(self):
        self.state_callers: List[StateHandler] = []

    def register_state_caller(self, caller: StateHandler):
        self.state_callers.append(caller)

    def generate_message(self) -> str:
        from io import StringIO
        buf = StringIO()
        for item in self.state_callers:
            buf.write(item())
            buf.write("\n")
        return buf.getvalue()
