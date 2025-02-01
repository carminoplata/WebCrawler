import pytest

from webcrawler.network.parser import Parser
from utils.utility import read_file_content, extract_link

@pytest.fixture(params=['google.html', 'example_nolink.html'])
def htmlfile(request):
    return request.param

@pytest.mark.asyncio
async def test_async_parse_urls_extraction(htmlfile):
    parser = Parser()
    html_page = read_file_content(htmlfile)
    expected_urls = extract_link(html_page)
    # Collect URLs from the async generator
    result_urls = [url async for url in parser.get_link(html_page)]
    assert len(result_urls) == len(expected_urls)
    assert result_urls.sort() == expected_urls.sort()
