"""
Enhanced schemas with Phase 4 & 5 additions
"""
from pydantic import BaseModel, field_validator
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
    TIMEOUT = "timeout"
    INTERACTION = "interaction"
    NAVIGATION = "navigation"

class ScrapeStrategy(str, Enum):
    STATIC = "static"
    JS = "js"
    HYBRID = "hybrid"
    ERROR = "error"

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

class EnhancedMeta(BaseModel):
    title: str = ""
    description: str = ""
    language: str = ""
    canonical: Optional[str] = None
    strategy: Optional[ScrapeStrategy] = None
    keywords: List[str] = []
    author: str = ""
    viewport: str = ""
    themeColor: str = ""
    ogType: str = ""
    scrapeDuration: Optional[str] = None
    interactionDepth: Optional[int] = None

class EnhancedInteraction(BaseModel):
    clicks: List[str] = []
    scrolls: int = 0
    pages: List[str] = []
    totalDepth: int = 0

class Error(BaseModel):
    message: str
    phase: str
    timestamp: Optional[str] = None

class PerformanceMetrics(BaseModel):
    duration_ms: float
    sections_found: int
    interaction_depth: int
    pages_visited: int
    unique_sections: Optional[int] = None

class ScrapeResult(BaseModel):
    url: str
    scrapedAt: str
    meta: EnhancedMeta
    sections: List[Section]
    interactions: EnhancedInteraction
    errors: List[Error] = []
    performance: Optional[PerformanceMetrics] = None
    warnings: List[str] = []

class ScrapeResponse(BaseModel):
    result: ScrapeResult
    status: str = "success"
    message: Optional[str] = None