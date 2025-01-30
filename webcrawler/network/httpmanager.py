import aiohttp
import asyncio


async def fetch(self, url: str, timeout: int = 10) -> any:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as response:
            if response.status == 200:
                return await response.text()
            elif response.status >= 300 and response.status < 400:
                # return the redirect location
                print(f'Redirected to {response.headers["Location"]}')
            elif response.status == 404:
                print(f'Error: Page NOT FOUND at {url}')
            else:
                print(f'Error: {response.status} at {url}')
