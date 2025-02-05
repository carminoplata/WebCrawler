import pytest
from pydantic import HttpUrl
from webcrawler.utils import *


def build_test(url, result):
    return (HttpUrl(url), result)

@pytest.fixture(params=[False, True])
def expected_ext(request):
    return request.param

@pytest.fixture
def testcase(request, expected_ext):
    return [
        (HttpUrl('https://www.google.com/imghp?hl=it&tab=wi'), False),
        (HttpUrl('https://www.facebook.com'), True)
    ]

@pytest.fixture
def base_url():
    return HttpUrl('https://google.com')


def test_is_external(base_url, testcase):
    print('TEST')
    for test in testcase:
        url, expected = test
        assert is_external(url, base_url) == expected
    

@pytest.mark.parametrize("base_url, new_url, expected", [
    # Relative URLs should return True if they are valid path.
    pytest.param("https://www.google.com/imghp?hl=it&tab=wi", 
     HttpUrl('https://google.com'), 
     (True, HttpUrl("https://www.google.com/imghp?hl=it&tab=wi")),
     id='www_url_is_relative_to_base'
    ),
    pytest.param("/preferences?hl=it", 
     HttpUrl('https://google.com'), 
     (True, HttpUrl(f'{str('https://google.com')}/preferences?hl=it')),
     id='relative_url_build_url_from_base_url'
    ),
    pytest.param("?id=123", 
                 HttpUrl('https://google.com'), 
                 (False, None),
                 id='query_param_is_not_valid_url'),
    pytest.param("#section", 
                 HttpUrl('https://google.com'), 
                 (False, None),
                 id='hashtag_is_not_valid_url'),
    pytest.param("http://www.example.com/history/optout?hl=it", 
                 HttpUrl("http://www.example.com/history"), 
                 (True, HttpUrl('http://www.example.com/history/optout?hl=it')),
                 id='the_url_is_child_of_base'),
    #Absolute URL with different domain should return False.
    pytest.param("https://www.youtube.com/?tab=w1", 
                 HttpUrl('https://google.com'), 
                 (False, None),
                 id='youtube_is_not_google'),
    pytest.param("https://news.google.com/?tab=wn", 
                 HttpUrl('https://google.com'), 
                 (False, None),
                 id='google_news_domain_is_another_google_domain'),
    pytest.param("https://accounts.google.com/ServiceLogin?hl=it&passive=true&continue=https://www.google.com/&ec=GAZAAQ",
                 HttpUrl('https://google.com'), 
                 (False, None),
                 id='google_account_is_another_google_domain'
                ),
    pytest.param("http://www.google.it/history/optout?hl=it", 
                 HttpUrl('https://google.com'), 
                 (False, None),
                 id='google_account_is_another_google_domain'
                ),
])
def test_is_relative_to_base(new_url, base_url, expected):
    result = is_relative_to_base(base_url, new_url)
    assert result == expected