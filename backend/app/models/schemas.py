from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

# Enums for validation
class SectionType(str, Enum):
    HERO = "hero"
    SECTION = "section"
    NAV = "nav"
    FOOTER = "footer"
    LIST = "list"
    GRID = "grid"
    FAQ = "faq"
    PRICING = "pricing"
    UNKNOWN = "unknown"

class ErrorPhase(str, Enum):
    FETCH = "fetch"
    RENDER = "render"
    PARSE = "parse"
    CLICK = "click"
    SCROLL = "scroll"
    GENERAL = "general"

# Request schemas
class ScrapeRequest(BaseModel):
    url: str
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

# Content schemas
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
    tables: List[Dict[str, Any]] = []

class Section(BaseModel):
    id: str
    type: SectionType = SectionType.UNKNOWN
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
    phase: ErrorPhase

class ScrapeResult(BaseModel):
    url: str
    scrapedAt: datetime
    meta: Meta
    sections: List[Section]
    interactions: Interaction
    errors: List[Error] = []

class ScrapeResponse(BaseModel):
    result: ScrapeResult