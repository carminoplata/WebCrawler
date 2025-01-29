from pydantic import BaseModel, HttpUrl

class Link(BaseModel):
    url: HttpUrl
    visited: bool = False

class Page(BaseModel):
    link: Link
    links: set[Link] = set()

