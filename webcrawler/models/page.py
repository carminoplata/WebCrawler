from pydantic import BaseModel
from models import Link

class Page(BaseModel):
    """ Page is a Pydantic Model to represent a web page described
    by its url (Link) and the list of links to subpage or external
    websites. Page class avoid to keep duplicates if there are.

    Attributes:
        url (Link): Link object that represent webpage's URL
        links (set[Link]): list of unique links inside the webpage
    """
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
        
    def add_link(self, link: Link) -> None:
        """Insert the link into page's links list if it hasn't ever been added. 
        
        Args:
        link : Link
            Link object to add at page's links list

        """
        if link not in self.links:
            self.links.add(link)

    def set_link_visited(self):
        """Allow to set a page as visited. """
        self.url.visited = True
    
    def get_page_url(self) -> str:
        """Retrives page's url as string"""
        return str(self.url) 