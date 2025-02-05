from pydantic import BaseModel, HttpUrl

class Link(BaseModel):
    """ Link is a Pydantic model to represent a valid http/https url. 
    Link has got only one field, visited, to track that the url has 
    been visited during an elaboration process (print, crawl, store).
    It can be used inside a dictionary as key via its physical url.

    Attributes:
        url (HttpUrl): HTTP/HTTPS URL
        visited (bool): status to check if the link has been visited or not
    """
    url: HttpUrl
    visited: bool = False


    def __hash__(self) -> int:
        return hash(self.url)
    
    def __eq__(self, other: 'Link') -> bool:
        return self.url == other.url

    def __str__(self) -> str:
        return str(self.url)
    
    def _display(self) -> str:
        return str(self.url)