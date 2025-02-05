from typing import Optional
from pydantic import BaseModel, HttpUrl

class Link(BaseModel):
    url: HttpUrl
    visited: bool = False
    #links: 'Optional[set[Link]]' = None

    def __hash__(self):
        return hash(self.url)
    
    def __eq__(self, other: 'Link') -> bool:
        return self.url == other.url

    def __str__(self):
        return str(self.url)
    
    def _display(self) -> str:
        return str(self.url)
    
    def is_page(self) -> bool:
        return self.links is not None
    
    def add_link(self, link: 'Link') -> None:
        if self.links is None:
            self.links = set()
        self.links.add(link)

