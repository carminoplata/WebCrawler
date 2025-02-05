import asyncio
import sys
import logging
import logging.config
import os
from pydantic import HttpUrl, ValidationError
from models import Link, Page
from utils import is_valid_url
from taskmanager import TaskManager
from network.httpmanager import HttpManager

logging.config.fileConfig('conf/logging.conf')
logger = logging.getLogger('webcrawler')

async def runcrawler(url: str) -> dict[str, Page]:
    netUrl = is_valid_url(url)
    if not netUrl:
        logger.error(f'invalid url {url}')
        raise ValueError('Invalid Url', url)
    logger.info(f'Starting webcrawler with root page: {netUrl}')
    #httpMgr = HttpManager(netUrl)
    taskMgr = TaskManager(netUrl)#, httpmgr=httpMgr)
    foundPages = {}
    try:
        await taskMgr.crawl()
        foundPages = taskMgr.get_all_pages()
        logger.info(f'WebCrawler Completed!')
    except (asyncio.exceptions.CancelledError, KeyboardInterrupt, 
            TimeoutError) as e:
        logger.info(f'WebCrawler Interrupted! Error: {e}')
        e.with_traceback()
    except Exception as e:
        print(f'WebCrawler Failed! Error: {e} {str(e)} {e.args}')
        e.with_traceback()
    finally:
        await taskMgr.shutdown()
        return foundPages
    
def visit_page(page: Page, 
               pages: dict[str, Page], 
               visited: set[str],
               func: any,
               indent=0,):
    pageUrl = page.get_page_url()
    visited.add(pageUrl)
    tabs = ''.join(['\t' for i in range(indent)])
    func(f'{tabs}{pageUrl}')
    if page.links:
        for link in page.links:
            linkUrl = str(link)
            if linkUrl in pages:
                visit_page(pages[linkUrl], pages, visited, indent+1)
            else:
                func(f'{tabs}\t{linkUrl}')

def visit_pages(pages: dict[str | Page], apply_func:any):
    visited = set()
    for link, page in pages.items():
        if link not in visited:
            visit_page(page, pages, visited, apply_func)
    

if __name__  == '__main__':
    # Start the webcrawler
    if len(sys.argv) < 2:
        logger.error('Usage: python webcrawler.py <url>')
        sys.exit(1)
    try:
        pages = asyncio.run(runcrawler(sys.argv[1]))
        visit_pages(pages, print)
    except ValueError as e:
        logger.error(f'Error: {e}')
        print(*e.args)
        sys.exit(1)
    except Exception as e:
        logger.error(f'Unexpected Error: {e}')
        sys.exit(1)
    