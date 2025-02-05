import pytest
import pytest_asyncio
import sys

sys.path.append('..')

#from aioresponses import aioresponses
from pydantic import HttpUrl
from webcrawler.network.httpmanager import HttpManager, HttpResult
#from utils.utility import read_file_content
# webcrawler/network/test_httpmanager.py


@pytest.mark.asyncio
class TestHttpManager:

    @pytest_asyncio.fixture(loop_scope='class')
    async def http_manager(self):
        manager = HttpManager(HttpUrl("https://google.com"))
        yield manager
        await manager.close()

    @pytest_asyncio.fixture(loop_scope='class', 
                    params=["https://example.com/notfound", 
                            "https://localhost:8000", 
                            "https://google.com/favicon.ico"])
    def error_page(request):
        return request.param
    
    @pytest.mark.asyncio(loop_scope='class')
    async def test_fetch_success(self, http_manager: HttpManager):
        response = await http_manager.fetch('http://www.google.com')
        assert len(response.htmlPage) > 0 and \
            'Google' in response.htmlPage and \
            response.pageUrl == 'http://www.google.com'

    @pytest.mark.asyncio(loop_scope='class')
    async def test_fetch_child_success(self, http_manager: HttpManager):
        response = await http_manager.fetch('https://www.google.com/imghp?hl=it&tab=wi')
        assert len(response.htmlPage) > 0 and 'Google' in response.htmlPage

    @pytest.mark.asyncio(loop_scope='class')
    async def test_fetch_not_found(self, http_manager: HttpManager):
        response = await http_manager.fetch('https://example.com/notfound')
        assert response == HttpResult(htmlPage='', url='https://example.com/notfound')

    @pytest.mark.asyncio(loop_scope='class')
    async def test_fetch_no_html_page(self, http_manager: HttpManager):
        response = await http_manager.fetch('https://google.com/favicon.ico')
        assert response == HttpResult(htmlPage='', url='https://google.com/favicon.ico')

    @pytest.mark.asyncio
    async def test_fetch_other_error(self, http_manager, capsys):
        url = HttpUrl("https://example.com/error")
        #with aioresponses() as m:
        #    m.get(url, status=500)
        #    response = await http_manager.fetch(url)
        #    assert response is None
        #    captured = capsys.readouterr()
        #    assert "Error: 500 at" in captured.out