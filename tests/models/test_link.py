import pytest
from pydantic import HttpUrl, ValidationError
from webcrawler.models.link import Link

class TestLink:
    def test_link_creation(self):
        url = "https://example.com"
        link = Link(url=url)
        assert link.url == HttpUrl(url)
        assert link.visited is False
        assert link.links is None

    def test_link_creation_invalid_url(self):
        with pytest.raises(ValidationError):
            Link(url="invalid-url")

    def test_link_display(self):
        url = "https://example.com"
        link = Link(url=url)
        assert link._display() == f'{url}/'

    def test_link_is_page_with_links(self):
        url = "https://example.com"
        child_url = "https://example.com/child"
        child_link = Link(url=child_url)
        link = Link(url=url, links={child_link})
        assert link.is_page() is True

    def test_link_is_page_without_links(self):
        url = "https://example.com"
        link = Link(url=url)
        assert link.is_page() is False

    def test_link_is_page_with_empty_links(self):
        url = "https://example.com"
        link = Link(url=url, links=set())
        assert link.is_page() is True

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
    
    def test_link_are_equals_with_children(self):
        expected = Link(url="https://example.com")
        link = Link(url="https://example.com/")
        link.add_link(Link(url="https://example.com/child"))
        link.add_link(Link(url="https://example.com/child2"))
        assert link == expected
