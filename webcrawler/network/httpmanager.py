import asyncio
import logging
from aiohttp import ClientSession, ClientTimeout
from pydantic import HttpUrl

HTML_MEDIA_TYPE = 'text/html'
XHTML_MEDIA_TYPE = 'application/xhtml+xml'
HEADERS = {
    'Accept': f'{HTML_MEDIA_TYPE}, {XHTML_MEDIA_TYPE}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/93.0.4577.82 Safari/537.36',}

logger = logging.getLogger('httpmanager')

class HttpResult:
    def __init__(self, htmlPage: str, url):
        self.htmlPage = htmlPage
        self.pageUrl = url

class HttpManager:
    def __init__(self, base_url: HttpUrl, **kwargs):
        self._timeout = 60 if 'timeout' not in kwargs else kwargs['timeout']
        self._base_url = base_url
        self._session = None
        
    
    async def fetch(self, url: str) -> HttpResult | None:
        task = asyncio.current_task().get_name()
        logger.info(f'[Task {task}] - GET {url}')
        await self.refresh_session()
        try:
            async with await self._session.get(url) as response:
                logger.info(f'[Task {task}] - Received Response from {url}')
                if response.status == 200:
                    if response.content_type == HTML_MEDIA_TYPE or \
                        response.content_type == XHTML_MEDIA_TYPE:
                        htmlPage = await response.text()
                        return HttpResult(htmlPage, url)
                    else:
                        logger.warning(f'[Task {task}] - Unexpected ContentType: {response.content_type}')
                        return HttpResult('', url)
                elif response.status == 404:
                    logger.warning(f'[Task {task}] - Error: Page NOT FOUND at {url}')
                else:
                    logger.warning(f'[Task {task}] - Error: {response.status} at {url}')
                return HttpResult('', url)
        except Exception as e:
            logger.error(f'[Task {task}] - Error on fetching url {url}: {e}')
            return HttpResult('', url)
    
    async def refresh_session(self) -> None:
        await self.close()
        self._session = ClientSession(timeout=ClientTimeout(total=self._timeout),
                                      headers=HEADERS)

    async def close(self):
        if self._session and not self._session.closed: 
            await self._session.close()