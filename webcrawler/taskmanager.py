import utils
import asyncio
import logging
from pydantic import HttpUrl, ValidationError
from models import Link, Page
from network.httpmanager import HttpManager, HttpResult
from selectolax.lexbor import LexborHTMLParser

logger = logging.getLogger('taskmanager')

class TaskManager():
    """TaskManager is the core of the webcrawler since it's goal 
    is to create and manage the tasks to download and parse the 
    html pages inside a domain.
    TaskManager requires only the base url from which it starts
    to visit the web pages. 
    By default, it's configured to run with only 1 task for
    downloading the html pages and 1 task for parsing the
    html pages.
    max_pages_in_mem is used to limit the amount of pages
    in memory (default = 1 page at time).
    Attributes:
        max_producers: maximum amount of tasks for downloading html pages
        max_consumers: maximum amount of tasks for parsing html pages
    """
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
        """ Makes the parsing of html page retrieving only the links
        available in the attribute href of the anchor

        Args:
            htmlPage: HttpResult provided by HttpManager
            links: output list filled with links found in the web page

        Returns:
            The list of links will be inside the links provided as argument
        """
        html_doc = LexborHTMLParser(htmlPage.htmlPage)
        for anchor in html_doc.select('a').matches:
            if 'href' in anchor.attributes:
                links.append(anchor.attributes['href'])

    async def crawl(self) -> None:
        """
        Crawl is the coroutine responsible of running and closing all tasks
        to getting all links available in the webpages of a specific domain
        At the end of its processing, the pages with relative links will be 
        retrieved with get_all_pages
        """
        await self._linksToVisit.put(str(self._baseurl))
        self._consumers = [asyncio.create_task(self.process_page(), name=f'Parser_{i}')
                           for i in range(self.max_consumers)]
        self._producers = [asyncio.create_task(self.produce_html(), 
                                               name=f'HtmlProducer_{i}')
                           for i in range(self.max_producers)]

        await self.monitor_crawler()
        
        await self.shutdown()

    async def produce_html(self):
        """Producer Coroutine downloads the web page"""
        task = asyncio.current_task().get_name()
        while True:
            logger.debug(f'[{task}] - Produce New Page')
            # MAYBE LOCK IN ORDER TO AVOID THAT MULTIPLE PRODUCER 
            # READ THE SAME LINK
            link = await self._linksToVisit.get()
            if str(link) not in self._visitedLinks:
                logger.debug(f'[{task}] - Links to visit {str(self._linksToVisit)}')
                logger.debug(f'[{task}] - GET {str(link)}')
                httpResult = await self._httpmanager.fetch(str(link))
                if httpResult.htmlPage:
                    await self._pages.put(httpResult)
                async with self._visitedLock:
                    self._visitedLinks.add(str(link))
            else:
                logger.debug(f'[{task}] - {str(link)} already visited')
            self._linksToVisit.task_done()
            checkAgain=1
            while(self._linksToVisit.empty()):
                checkAgain+=1
                await asyncio.sleep(checkAgain)

    async def process_page(self):
        """Consumer Coroutine parse the web page to get all 
        available links.
        """
        task = asyncio.current_task().get_name()
        while True:
            logger.debug(f'[{task}] - Consume New Page')
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
        """
        Coroutine to process a link in order to validate it
        and adding it at visited pages. Only HTTP/HTTPS URL
        are considered valid. 
        """
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
                logger.debug(f'Invalid url {link}')
    
    async def monitor_crawler(self) -> None:
        """ 
        Manages the queues in order to understand
        when the task are completed and the crawler 
        completed its job successfully.
        """
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


    def print_stats(self, time: float) -> None:
        """Show some statistics about the execution of web crawler.
        Require an execution of crawl before calling it, otherwise
        all zero values are retrieved
        """
        logger.info("to_visit: %s", str(self._linksToVisit.qsize()))
        logger.info("visited: %s", str(len(self._visitedLinks)))
        if len(self._visitedLinks) > 0:
            logger.info("Avg time per page: %s", str(time/len(self._visitedLinks)))

    def get_visited_pages(self, visited: list[str]) -> None:
        """Retrieves the links of visited pages
        
        Args:
            visited (list[str]): list to fill with the visited web page's url 
        """
        for url in  self._pagesVisited.keys():
            visited.append(url)
    
    def get_all_pages(self) -> dict[str, Page]:
        """Retrieves the access to the whole tree of 
        downloaded pages
        
        Returns:
            A dictionary of <url (str), page (Page)> with all downloaded 
            and visited pages. Page will contain only its own url and the
            referred links  
        """
        return self._pagesVisited
    
    def get_no_visit_pages(self, noVisited: dict[str, set[HttpUrl]]) -> None :
        """Retrieves the access to the whole tree of 
        downloaded pages
        
        Returns:
            A dictionary of <url (str), page (Page)> with all downloaded 
            and visited pages. Page will contain only its own url and the
            referred links  
        """
        for k, v in self._pagesVisited.items(): 
            if k not in noVisited:
                for l in v.links:
                    if l not in noVisited:
                        noVisited[k].add(l.url)

    def get_num_html_pages(self) -> int:
        """ Retrieves the amount of visited pages
        into a domain.

        Returns:
            The amount of visited pages
        """
        return len(self._pagesVisited)
    
    async def shutdown(self):
        """Close everything that is still opened"""
        for t in self._consumers + self._producers:
            t.cancel()

        await asyncio.gather(*self._consumers, *self._producers, 
                         return_exceptions=True)
        if self._httpmanager:
            await self._httpmanager.close()