from pydantic import BaseModel
from models import Link

class Page(BaseModel):
    url: Link
    links: set[Link] = set()

    def __eq__(self, value):
        if self.url == value.url:
            if len(self.links) == len(value.links):
                for l in self.links:
                    if l not in value.links:
                        return False
                return True
            else:
                return False
        else:
            return False
        
    def add_link(self, link: Link):
        if link not in self.links:
            self.links.add(link)

    def set_link_visited(self):
        self.url.visited = True
    
    def get_page_url(self) -> str:
        return str(self.url) 