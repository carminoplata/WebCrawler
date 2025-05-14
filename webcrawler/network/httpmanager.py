import asyncio
import logging
import os
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
    """
    HttpResult is the result provided by HttpManager.
    Each result will have the web page's url and its
    html file as text

    Attributes:
        htmlPage (str): Content of HTML file
        pageUrl (str): HTTP/HTTPS url of web page
    """
    def __init__(self, htmlPage: str, url:str):
        
        self.htmlPage = htmlPage
        self.pageUrl = url
    
    def __eq__(self, value):
        return self.htmlPage == value.htmlPage and \
            self.pageUrl == value.pageUrl

class HttpManager:
    """HttpManager makes the network requests to download an HTML page. 
       HttpManager require an HTTP/HTTPS URL to be created and can
       read some additional configuration's parameters from a
       dictionary, such as session timeout for the HTTP/HTTPS requests
    """

    def __init__(self, base_url: HttpUrl, **kwargs):
        # session timeout
        self._timeout = 60 if 'timeout' not in kwargs else kwargs['timeout']
        self._base_url = base_url
        self._session = None
        self._debug: bool = kwargs['debug'] if 'debug' in kwargs else False        
    
    async def fetch(self, url: str) -> HttpResult:
        """ Fetch Coroutine to download html file of a web page

        Args:
            url (str): HTTP/HTTPS url to query for downloading the page

        Returns: 
            HttpResult with the html page stored as string and its own
            url.
            In case of any error during the downloading process, an
            HttpResult object with an empty htmlPage will be retrieved,
            only the webpage's url will be configured. 
        """
        task = asyncio.current_task().get_name()
        logger.debug(f'[Task {task}] - GET {url}')
        await self.refresh_session()
        try:
            async with await self._session.get(url) as response:
                if response.status == 200:
                    if response.content_type == HTML_MEDIA_TYPE or \
                        response.content_type == XHTML_MEDIA_TYPE:
                        logger.debug(f'[Task {task}] - 200 OK {url}')
                        htmlPage = await response.text()
                        if self._debug:
                            suffix = f'.{url.split('.')[-1]}'
                            logger.debug(f'Suffix {suffix}')
                            with open(f'pages\\{url.split('//')[-1].removesuffix(suffix)}.html', 'w',
                                      encoding='utf-8') as f:
                                f.write(htmlPage)
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
            logger.debug(f'[Task {task}] - ERROR {e}')
            logger.error(f'[Task {task}] - Error on fetching url {url}: {e}')
            return HttpResult('', url)
    
    async def refresh_session(self) -> None:
        """Allow to recreate the session in case a timeout has fired or 
        the session has been closed.
        """
        await self.close()
        self._session = ClientSession(timeout=ClientTimeout(total=self._timeout),
                                      headers=HEADERS)

    async def close(self):
        """Close the session if it's still opened"""
        if self._session and not self._session.closed: 
            await self._session.close()