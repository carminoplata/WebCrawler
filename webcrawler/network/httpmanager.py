import asyncio
from aiohttp import ClientSession, ClientTimeout
from pydantic import HttpUrl

class HttpManager:
    def __init__(self, base_url: HttpUrl, **kwargs):
        self._timeout = 60 if 'timeout' not in kwargs else kwargs['timeout']
        self._base_url = base_url
        self._session = ClientSession(timeout=ClientTimeout(total=self._timeout))
    
    async def fetch(self, url: str = '' ) -> str | None:
        if not url:
            url = str(self._base_url)
        await self.refresh_session()
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.text() \
                    if response.content_type == 'text/html' \
                    else None
            elif response.status == 404:
                print(f'Error: Page NOT FOUND at {url}')
            else:
                print(f'Error: {response.status} at {url}')
            return None
    
    async def refresh_session(self) -> None:
        if not self._session or self._session.closed:
            self._session = ClientSession(self._base_url, 
                                          timeout=ClientTimeout(total=self._timeout))

    async def close(self):
        if self._session and not self._session.closed: 
            await self._session.close()