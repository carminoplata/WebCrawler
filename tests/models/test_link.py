import pytest
from pydantic import HttpUrl, ValidationError
from webcrawler.models.link import Link

class TestLink:
    def test_link_creation(self):
        url = "https://example.com"
        link = Link(url=url)
        assert link.url == HttpUrl(url)
        assert link.visited is False

    def test_link_creation_invalid_url(self):
        with pytest.raises(ValidationError):
            Link(url="invalid-url")

    def test_link_display(self):
        url = "https://example.com"
        link = Link(url=url)
        assert link._display() == f'{url}/'

    def test_link_hash_no_match_url_with_literal(self):
        url = "https://example.com"
        link = Link(url=url)
        assert hash(link) != hash(url)

    def test_link_hash_match_url_with_literal(self):
        url = HttpUrl("https://example.com")
        link = Link(url=url)
        assert hash(link) == hash(url)
    
    def test_link_not_equals(self):
        expected = Link(url="http://example.com")
        link = Link(url="https://example.com/")
        assert link != expected

    def test_link_are_equals(self):
        expected = Link(url="https://example.com")
        link = Link(url="https://example.com/")
        assert link == expected