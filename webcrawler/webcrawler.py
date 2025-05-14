import argparse
import asyncio
import sys
import logging
import logging.config
import time
from pydantic import HttpUrl, ValidationError
from models import Link, Page
from utils import is_valid_url
from taskmanager import TaskManager
from network.httpmanager import HttpManager

logging.config.fileConfig('conf/logging.conf')
logger = logging.getLogger('webcrawler')

async def runcrawler(url: str, debug: bool = False) -> dict[str, Page]:
    """" Coroutine to run the crawler
    
    Args:
        url (str): HTTP url of the domain to start crawling
        web pages.
    
    Returns:
        The dictionary built from crawler with visited web pages
        and their link. For each entry in the dictionary, there is
        the page's URL and the Page object built from crawler.
        In case of an error during crawling, an empty dictionary
        is retrieved.
    """
    netUrl = is_valid_url(url)
    if not netUrl:
        logger.error(f'invalid url {url}')
        raise ValueError('Invalid Url', url)
    logger.info(f'Starting webcrawler with root page: {netUrl}')
    taskMgr = TaskManager(netUrl, debug)
    foundPages = {}
    try:
        t1: float = time.time()
        await taskMgr.crawl()
        t2: float = time.time()
        taskMgr.print_stats(t2-t1)
        elapsedSeconds = t2 - t1
        if elapsedSeconds > 3600:
            elapsed = f'{str(elapsedSeconds // 3600)} h'
        elif elapsedSeconds > 60:
            elapsed = f'{str(elapsedSeconds // 60)} min'
        else:
            elapsed = f'{str(elapsedSeconds)} s'
        logger.info(f'Time to complete: {elapsed}')
        foundPages = taskMgr.get_all_pages()
        logger.info(f'WebCrawler Completed! Found {taskMgr.get_num_html_pages()} pages')
    except (asyncio.exceptions.CancelledError, KeyboardInterrupt, 
            TimeoutError) as e:
        logger.info(f'WebCrawler Interrupted! Error: {e}')
        e.with_traceback()
    except Exception as e:
        logger.error(f'WebCrawler Failed! Error: {e} {str(e)} {e.args}')
        e.with_traceback()
    finally:
        await taskMgr.shutdown()
        return foundPages
    
def visit_page(page: Page, 
               pages: dict[str, Page], 
               visited: set[str],
               func: any,
               indent=0,):
    """Visit_Page allow to apply a function to each link
    stored inside the page."""
    pageUrl = page.get_page_url()
    visited.add(pageUrl)
    tabs = ''.join(['\t' for i in range(indent)])
    func(f'{tabs}{pageUrl.upper()}')
    if page.links:
        for link in page.links:
            linkUrl = str(link)
            func(f'{tabs}\t{linkUrl}')
            if linkUrl in pages and link != page.url and \
                linkUrl not in visited:
                visit_page(pages[linkUrl], pages, visited, func, indent+1)

                

def visit_pages(pages: dict[str | Page], apply_func:any):
    visited: set[str] = set()
    for link, page in pages.items():
        if link not in visited:
            visit_page(page, pages, visited, apply_func)
    

if __name__  == '__main__':
    # Start the webcrawler
    if len(sys.argv) < 2:
        logger.error('Usage: python webcrawler.py <url>')
        sys.exit(1)
    parser = argparse.ArgumentParser(description='WebCrawler to collect links into page')
    parser.add_argument('url', type=str, help='http or https url like http://example.com')
    parser.add_argument('-d', '--debug', type=int, required=False, default=0, choices=[0, 1])
    args = parser.parse_args()
    try:
        pages = asyncio.run(runcrawler(args.url, args.debug))
        visit_pages(pages, print)
    except ValueError as e:
        logger.error(f'Error: {e}')
        print(*e.args)
        sys.exit(1)
    except Exception as e:
        logger.error(f'Unexpected Error: {e}')
        sys.exit(1)
    