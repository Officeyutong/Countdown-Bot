import aiohttp
import asyncio
import urllib.parse
from typing import Union
from concurrent.futures import Future

from .exceptions import InvalidAccessTokenException, APIError


class AsyncHTTPAPIClient:
    def __init__(self, loop: asyncio.AbstractEventLoop, server_url: str, access_token: str = "", secret: str = "", proxy: str = None):
        self.loop = loop
        self.client = aiohttp.ClientSession(headers={
            "Authorization": f"Token {access_token}"
        }, trust_env=True)
        self.server_url = server_url
        self.access_token = access_token
        self.secret = secret
        self.proxy = proxy

    def invoke_async(self, api_name: str, data: dict) -> Future:
        return self.invoke(api_name, data, False)

    def invoke(self, api_name: str, data: dict, wait_to_finish: bool = True) -> Union[dict, asyncio.Future]:
        """
        调用HTTPAPI
        @param api_name: API名
        @param data: 参数
        @param is_async: 是否等待调用完成，如果为True，则会等待相应的Future完成，否则返回Future
        @param async_api: 是否使用HTTP API所提供的异步版本

        @return: 调用结果或相应Future
        """
        async def wrapper():
            async with self.client.post(urllib.parse.urljoin(self.server_url, api_name), json=data, proxy=self.proxy) as resp:
                # print(resp.request_info.headers)
                resp: aiohttp.ClientResponse
                if resp.status == 401:
                    raise InvalidAccessTokenException(
                        f"Empty access token: {self.access_token}")
                elif resp.status == 403:
                    raise InvalidAccessTokenException(
                        f"Bad access token: {self.access_token}")
                json_resp = await resp.json(encoding="utf-8", content_type=None)
                if json_resp["status"] == "failed":
                    code = json_resp["retcode"]
                    raise APIError(
                        f"HTTP API returned {code}, see https://cqhttp.cc/docs for details")
                else:
                    return json_resp["data"]
        # print("invoking", locals())
        future = asyncio.run_coroutine_threadsafe(wrapper(), self.loop)
        if not wait_to_finish:
            return future
        else:
            return future.result()
