import utils
import asyncio
import logging
from pydantic import HttpUrl, ValidationError
from models import Link, Page
from network.httpmanager import HttpManager, HttpResult
from selectolax.lexbor import LexborHTMLParser

logger = logging.getLogger('taskmanager')

class TaskManager():
    def __init__(self, base_url: HttpUrl, 
                 #httpmgr: HttpManager,
                 #parser: Parser,
                 max_producers: int = 1,
                 max_consumers: int = 1,
                 max_pages_in_mem: int = 1):
        self._baseurl: HttpUrl = base_url
        self._pagesVisited: dict[str, Page] = {}
        self._producers: set[asyncio.Task] = set()
        self._consumers: set[asyncio.Task] = set()
        self._pages: asyncio.Queue[HttpResult] = asyncio.Queue(max_pages_in_mem)
        self._visitedLinks: set[str] = set()
        self._linksToVisit: asyncio.Queue[HttpUrl]  = asyncio.Queue()
        self._visitedLock: asyncio.Lock = asyncio.Lock()
        self.max_producers = max_producers
        self.max_consumers = max_consumers
        self._httpmanager = HttpManager(self._baseurl)

    def get_links(self, htmlPage: HttpResult, links: list[str]) -> None: 
        html_doc = LexborHTMLParser(htmlPage.htmlPage)
        for anchor in html_doc.select('a').matches:
            if 'href' in anchor.attributes:
                links.append(anchor.attributes['href'])

    async def crawl(self) -> None:
        await self._linksToVisit.put(str(self._baseurl))
        #self._consumers = [asyncio.create_task(self.process_page(), name=f'Parser_{i}')
        #                   for i in range(self.max_consumers)]
        #self._producers = [asyncio.create_task(self.produce_html(), 
        #                                       name=f'HtmlProducer_{i}')
        #                   for i in range(self.max_producers)]
        #self._monitor_task = asyncio.create_task(self.monitor_crawler(), name='CrawlerMonitor')
        consumer = asyncio.create_task(self.process_page(), name='Parser')
        producer = asyncio.create_task(self.produce_html(), name='HtmlProduer')

        await self.monitor_crawler()
        consumer.cancel()
        producer.cancel()
        await asyncio.gather(consumer, producer, #monitor_task,
                         return_exceptions=True)

    async def produce_html(self):
        task = asyncio.current_task().get_name()
        while True:
            logger.debug(f'[{task}] - Produce New Page')
            # MAYBE LOCK IN ORDER TO AVOID THAT MULTIPLE PRODUCER 
            # READ THE SAME LINK
            link = await self._linksToVisit.get()
            if str(link) not in self._visitedLinks:
                logger.debug(f'[{task}] - Links to visit {str(self._linksToVisit)}')
                logger.info(f'[{task}] - Downloading {str(link)}')
                httpResult = await self._httpmanager.fetch(str(link))
                if httpResult.htmlPage:
                    await self._pages.put(httpResult)
                async with self._visitedLock:
                    self._visitedLinks.add(str(link))
            else:
                logger.debug(f'[{task}] - {str(link)} already visited')
            await asyncio.sleep(1)
            self._linksToVisit.task_done()

    async def process_page(self):
        task = asyncio.current_task().get_name()
        while True:
            logger.debug(f'[{task}] -Consume New Page')
            page: HttpResult = await self._pages.get()
            foundLinks: list[str] = []
            logger.debug(f'[{task}] - Look for links inside {page.pageUrl}')
            self.get_links(page, foundLinks)
            for link in foundLinks:
                await self.process_link(link, page.pageUrl)
            else:
                # IF NO LINK ARE FOUND, THE PAGE MUST BE CREATED
                self._add_link_to_page(page.pageUrl, None)
            self._pages.task_done()
    
    async def process_link(self, link: str, pageUrl: str):
        newLink = utils.is_valid_url(link)
        if newLink:
            # VALID LINK CHECK IF it's already visited or not 
            # and if it's external or inside the same domain
            async with self._visitedLock:
                if not utils.is_external(newLink, self._baseurl) and \
                    str(link) not in self._visitedLinks:
                    logger.debug(f'[process_link] - Adding New Link {str(link)}')
                    logger.debug(f'[process_link] - VisitedLinks {str(self._visitedLinks)}')
                    await self._linksToVisit.put(newLink)
            self._add_link_to_page(pageUrl, newLink)
        else:
            # Check if it's relative url
            isChildPage, newLink = utils.is_relative_to_base(link, self._baseurl)
            if isChildPage:
                async with self._visitedLock:
                    if str(newLink) not in self._visitedLinks:
                        logger.debug(f'Adding Child Page {str(link)}')
                        logger.debug(f'DBG: VisitedLinks {str(self._visitedLinks)}')
                        await self._linksToVisit.put(newLink)
                    self._add_link_to_page(pageUrl, newLink)
            else:
                logger.error(f'Invalid url {link}')
    
    async def monitor_crawler(self):
        logger.debug('Monitor Start')
        await self._linksToVisit.join()
        await self._pages.join()
        logger.debug('Monitor End')

    def _add_link_to_page(self, pageUrl: str, link: HttpUrl | None):
        try:
            if pageUrl not in self._pagesVisited:
                self._pagesVisited[pageUrl] = Page(url=Link(url=pageUrl, visited=True))
            if link:
                self._pagesVisited[pageUrl].add_link(Link(url=link))
        except ValidationError as e:
            logger.error(f'[add_link_to_page] - Error some urls are invalid')
            logger.error(f'[add_link_to_page] - {e.errors()}')

    def get_visited_pages(self, visited: list[str]) -> None:
        for url in  self._pagesVisited.keys():
            visited.append(url)
    
    def get_all_pages(self) -> dict[str, Page]:
        return self._pagesVisited
    
    def get_no_visit_pages(self, noVisited: dict[str, set[HttpUrl]]) -> None :
        for k, v in self._pagesVisited.items(): 
            if k not in noVisited:
                for l in v.links:
                    if l not in noVisited:
                        noVisited[k].add(l.url)

    def get_num_html_pages(self) -> int:
        return len(self._pages)
    
    async def shutdown(self):
        await asyncio.gather(*self._consumers, *self._producers, 
                         return_exceptions=True)
        if self._httpmanager:
            await self._httpmanager.close()