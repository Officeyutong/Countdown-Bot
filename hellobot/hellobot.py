# import websockets
import aiohttp
import asyncio
import uuid
import json
import threading
from concurrent.futures import wait, Future
from typing import Dict


class HelloBot:
    def __init__(
            self,
            server_url: str,
            access_token: str,
            secret: str = "",
            timeout: int = 30,
            retry_times: int = 5):
        self.__server_url = server_url
        self.__access_token = access_token
        self.__secret = secret
        self.__timeout = timeout
        self.__retry_times = retry_times
        # event_id -> 回调队列
        self.__api_callback_queues: Dict[str, asyncio.Queue] = dict()
        self.loop = asyncio.get_event_loop()
        self.__started = False
        self.__session = aiohttp.ClientSession()

    def post_event(self, context: dict):
        print("processing event", context)
        print("echo", self.call({
            "action": "send_group_msg",
            "params": {
                "message": f'[CQ:at,qq={context["user_id"]}] {context["raw_message"]}',
                "group_id": context["group_id"]
            },
            "echo": str(uuid.uuid1())
        }))
    # def start(self):

    def start(self):
        self.loop.run_until_complete(
            asyncio.gather(self.__cycle())
        )
        # threading.Thread(target=self.loop.run_forever).start()
        # asyncio.run_coroutine_threadsafe(self.__api_cycle(
        # ), self.loop).add_done_callback(lambda x: print(x.exception()))
        # asyncio.run_coroutine_threadsafe(self.__event_cycle(
        # ), self.loop).add_done_callback(lambda x: print(x.exception()))

    async def __async_start(self):
        # aiohttp.http_websocket.co
        # await self.__session.ws_connect()
        self.ws_client = await self.__session.ws_connect(
            self.__server_url, headers={"Authorization": f"Bearer {self.__access_token}"})
        # self.event_ws_client = await self.__session.ws_connect(
        #     self.__server_url+"/event", headers={"Authorization": f"Bearer {self.__access_token}"})
        # self.event_ws_client.send_json()

    async def __invoke(self, data: dict, wait_for_response=False):
        if wait_for_response:
            self.__api_callback_queues[data["echo"]] = asyncio.Queue(maxsize=1)
        print("invoked")
        await self.ws_client.send_json(data)
        print("send ok")
        if wait_for_response:
            resp = await self.__api_callback_queues[data["echo"]].get()
            del self.__api_callback_queues[data["echo"]]
            return resp

    async def __cycle(self):
        if not self.__started:
            await self.__async_start()
            self.__started = True
        while not self.ws_client.closed:
            resp = await self.ws_client.receive_json()
            if "post_type" in resp:
                self.post_event(resp)
            else:
                if "echo" in resp and resp["echo"] in self.__api_callback_queues:
                    self.__api_callback_queues[resp["echo"]].put(resp)

    def call(self, data, sync=True, sync_timeout=10):
        future = asyncio.run_coroutine_threadsafe(
            self.__invoke(data), self.loop)
        future.add_done_callback(lambda x: print(x.exception()))
        if sync:
            print("waiting..")
            return future.result(sync_timeout)
        else:
            return future
