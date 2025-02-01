import pytest
import pytest_asyncio
import sys

sys.path.append('..')

#from aioresponses import aioresponses
from pydantic import HttpUrl
from webcrawler.network.httpmanager import HttpManager
from utils.utility import read_file_content
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
        #with aioresponses() as m:
            #m.get(url, status=200, body="Success")
        ##expectedPage = read_file_content('googlePage.html')
        response = await http_manager.fetch()
        assert len(response) > 0 and 'Google' in response

    @pytest.mark.asyncio(loop_scope='class')
    async def test_fetch_child_success(self, http_manager: HttpManager):
        #with aioresponses() as m:
            #m.get(url, status=200, body="Success")
        ##expectedPage = read_file_content('googlePage.html')
        response = await http_manager.fetch('https://www.google.com/imghp?hl=it&tab=wi')
        assert len(response) > 0 and 'Google' in response

    @pytest.mark.asyncio(loop_scope='class')
    async def test_fetch_diff_domain(self, http_manager: HttpManager):
        #with aioresponses() as m:
            #m.get(url, status=200, body="Success")
        ##expectedPage = read_file_content('googlePage.html')
        response = await http_manager.fetch('https://facebook.com')
        assert len(response) > 0 and 'Facebook' in response

    @pytest.mark.asyncio(loop_scope='class')
    async def test_fetch_not_found(self, http_manager):
        response = await http_manager.fetch('https://example.com/notfound')
        assert response is None
        #with aioresponses() as m:
        #    m.get(url, status=404)
        #    response = await http_manager.fetch(url)
        #    assert response is None
        #    captured = capsys.readouterr()
        #    assert "Error: Page NOT FOUND at" in captured.out

    @pytest.mark.asyncio(loop_scope='class')
    async def test_fetch_no_html_page(self, http_manager):
        response = await http_manager.fetch('https://google.com/favicon.ico')
        assert response is None

    @pytest.mark.asyncio
    async def test_fetch_other_error(self, http_manager, capsys):
        url = HttpUrl("https://example.com/error")
        #with aioresponses() as m:
        #    m.get(url, status=500)
        #    response = await http_manager.fetch(url)
        #    assert response is None
        #    captured = capsys.readouterr()
        #    assert "Error: 500 at" in captured.out