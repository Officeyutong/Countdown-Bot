from dataclasses import dataclass
from typing import List

from dataclasses import dataclass
import asyncio
@dataclass
class TimeTuple:
    hour: int
    minute: int


class ScheduleLoopManager:
    def __init__(self, check_interval: int, execute_delay: int):
        self.tasks = []
        self.check_interval = check_interval
        self.execute_delay = execute_delay

    def register(self, execute_time: TimeTuple, coro, name: str = ""):
        async def wrapper():
            from datetime import datetime
            print(f"Loop {name} started")
            while True:
                while True:
                    now = datetime.now()
                    print(f"Checking schedule loop {name}")
                    if now.hour == execute_time.hour and now.minute == execute_time.minute:
                        break
                    asyncio.sleep(self.check_interval)
                print(f"Executing schedule loop {name}")
                await coro()
                asyncio.sleep(self.execute_delay)
        self.tasks.append(wrapper())
