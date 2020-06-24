from dataclasses import dataclass
from typing import List, Awaitable

from dataclasses import dataclass
import asyncio
@dataclass
class TimeTuple:
    hour: int
    minute: int


class ScheduleLoopManager:
    def __init__(self, check_interval: int, execute_delay: int, bot):
        self.tasks: List[Awaitable] = []
        self.check_interval = check_interval
        self.execute_delay = execute_delay
        self.bot = bot

    def register(self, execute_time: TimeTuple, coro, name: str = "", init=None):
        async def wrapper():
            
            from datetime import datetime
            self.bot.logger.info(f"Loop {name} started")
            if init:
                await init
            while True:
                while True:
                    now = datetime.now()
                    self.bot.logger.debug(f"Checking schedule loop {name}")
                    if now.hour == execute_time.hour and now.minute == execute_time.minute:
                        break
                    await asyncio.sleep(self.check_interval)
                self.bot.logger.info(f"Executing schedule loop {name}")
                self.bot.logger.debug(f"{coro} {type(coro)}")
                # import pdb; pdb.set_trace()
                try:
                    await coro
                    self.bot.logger.info(f"{name} executed.")
                    
                except:
                    self.bot.logger.exception("Exception:")
                    import traceback
                    traceback.print_exc()
                await asyncio.sleep(self.execute_delay)
        self.tasks.append(wrapper())
