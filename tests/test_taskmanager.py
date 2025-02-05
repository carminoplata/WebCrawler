import pytest
import pytest_asyncio
import asyncio

from .utils.utility import read_file_content, extract_link
from webcrawler.taskmanager import TaskManager
from webcrawler.models import HttpUrl, Page, Link
from webcrawler.network.httpmanager import HttpManager, HttpResult

@pytest.mark.asyncio(loop_scope='class')
class TestTaskManager:
    
    @pytest.fixture(params=['google.html', 'example_nolink.html'])
    def htmlfile(self, request):
        return request.param

    @pytest.fixture()
    def base_page(self):
        return HttpUrl(url="https://google.com")

    @pytest_asyncio.fixture()
    async def http_manager(self, base_page):
        manager = HttpManager(base_url=base_page)
        yield manager
        await manager.close()

    @pytest_asyncio.fixture()
    async def task_manager(self, base_page: HttpUrl, http_manager: HttpManager):
        taskMgr = TaskManager(base_page)
        yield taskMgr
        await taskMgr.shutdown()

    @pytest.mark.asyncio()
    async def test_process_link_create_and_add_to_page(self, task_manager: TaskManager):
        # Test when the page URL is valid and the link is added properly
        page_url = 'http://example.com'
        link_url = 'http://example.com/link'
        
        # Call the method
        await task_manager.process_link(pageUrl=page_url, link=link_url)
        pages = task_manager.get_all_pages()
        
        # Assert that the page URL is in _pagesVisited
        assert page_url in pages
        assert pages[page_url] == Page(url=Link(url='http://example.com'), 
                                       links={Link(url='http://example.com/link')})
  
    @pytest.mark.asyncio()
    async def test_process_link_exist_link_in_page(self, task_manager: TaskManager):
        # Test when the page URL is valid and the link is added properly
        page_url = 'http://example.com'
        link_url1 = 'http://example.com/link'
        link_url2= 'http://example.com/link'

        expectedPage = Page(url=Link(url=HttpUrl(page_url)), 
                            links={Link(url=link_url1)})
        
        # Call the method
        await task_manager.process_link(pageUrl=page_url, link=link_url1)
        await task_manager.process_link(pageUrl=page_url, link=link_url2)
        pages = task_manager.get_all_pages()

        # Assert that the page URL is in _pagesVisited
        assert page_url in pages
        assert pages[page_url] == expectedPage
    
    @pytest.mark.asyncio()
    async def test_process_link_add_link_to_page(self, task_manager: TaskManager):
        # Test when the page URL is valid and the link is added properly
        page_url = 'http://example.com'
        link_url1 = 'http://example.com/link'
        link_url2= 'http://example.com/link2'

        expectedPage = Page(url=Link(url=HttpUrl(page_url)), 
                            links={Link(url=link_url1)})
        
        expectedPage.add_link(Link(url=link_url2))
        
        # Call the method
        await task_manager.process_link(pageUrl=page_url, link=link_url1)
        await task_manager.process_link(pageUrl=page_url, link=link_url2)
        pages = task_manager.get_all_pages()

        # Assert that the page URL is in _pagesVisited
        assert page_url in pages
        assert pages[page_url] == expectedPage

    @pytest.mark.asyncio()
    async def test_process_link_invalid_link(self, task_manager: TaskManager):
        # Test when the page URL is valid and the link is added properly
        page_url = 'http://example.com'
        link_url1 = 'http://example.com/link'
        link_url2= 'http://example.com/link2'

        expectedPage = Page(url=Link(url=HttpUrl(page_url)), 
                            links={Link(url=link_url1)})
        
        expectedPage.add_link(Link(url=link_url2))
        
        # Call the method
        await task_manager.process_link(pageUrl=page_url, link=link_url1)
        await task_manager.process_link(pageUrl=page_url, link=link_url2)
        await task_manager.process_link(pageUrl=page_url, 
                                        link='mailto:info@dorbit.space')
        pages = task_manager.get_all_pages()

        # Assert that the page URL is in _pagesVisited
        assert page_url in pages
        assert pages[page_url] == expectedPage

    @pytest.mark.asyncio()
    async def test_process_link_with_two_tasks(self, task_manager: TaskManager):
        # Test when the page URL is valid and the link is added properly
        page_url = 'http://example.com'
        link_url1 = 'http://example.com/link'
        link_url2= 'http://example.com/link2'

        expectedPage = Page(url=Link(url=HttpUrl(page_url)), 
                            links={Link(url=link_url1)})
        expectedPage.add_link(Link(url=link_url2))

        task1 = asyncio.create_task(task_manager.process_link(
            pageUrl=page_url, link=link_url1))
        task2 = asyncio.create_task(task_manager.process_link(
            pageUrl=page_url, link=link_url2))
        
        await asyncio.gather(task1, task2)
        
        pages = task_manager.get_all_pages()

        # Assert that the page URL is in _pagesVisited
        assert page_url in pages
        assert pages[page_url] == expectedPage

    @pytest.mark.asyncio
    async def test_get_links(self, htmlfile, task_manager: TaskManager):
        html_page = read_file_content(htmlfile)
        expected_urls = extract_link(html_page)
        # Collect URLs from the async generator
        result_urls = []
        task_manager.get_links(HttpResult(html_page, htmlfile), result_urls)
        assert len(result_urls) == len(expected_urls)
        assert result_urls.sort() == expected_urls.sort()












