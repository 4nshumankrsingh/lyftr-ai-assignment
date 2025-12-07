from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ScrapeRequest(BaseModel):
    url: str

class Link(BaseModel):
    text: str
    href: str

class Image(BaseModel):
    src: str
    alt: str

class Content(BaseModel):
    headings: List[str] = []
    text: str = ""
    links: List[Link] = []
    images: List[Image] = []
    lists: List[List[str]] = []
    tables: List[Any] = []

class Section(BaseModel):
    id: str
    type: str  # hero, section, nav, footer, etc.
    label: str
    sourceUrl: str
    content: Content
    rawHtml: str
    truncated: bool

class Meta(BaseModel):
    title: str = ""
    description: str = ""
    language: str = ""
    canonical: Optional[str] = None

class Interaction(BaseModel):
    clicks: List[str] = []
    scrolls: int = 0
    pages: List[str] = []

class Error(BaseModel):
    message: str
    phase: str

class ScrapeResult(BaseModel):
    url: str
    scrapedAt: datetime
    meta: Meta
    sections: List[Section]
    interactions: Interaction
    errors: List[Error] = []

class ScrapeResponse(BaseModel):
    result: ScrapeResult