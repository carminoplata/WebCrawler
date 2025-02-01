from selectolax.lexbor import LexborHTMLParser
from pydantic import HttpUrl, ValidationError

class Parser:
    def __init__(self):
        pass

    async def get_link(self, html_page: str): 
        html_doc = LexborHTMLParser(html_page)
        for anchor in html_doc.select('a').matches:
            if 'href' in anchor.attributes:
                yield anchor.attributes['href']
