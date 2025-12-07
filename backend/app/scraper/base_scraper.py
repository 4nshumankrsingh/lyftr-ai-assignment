from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List 
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, url: str):
        self.url = url
        self.base_url = self._get_base_url(url)
        self.errors = []
        
    def _get_base_url(self, url: str) -> str:
        """Extract base URL from full URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute"""
        if url.startswith(('http://', 'https://', '//')):
            if url.startswith('//'):
                return f"https:{url}"
            return url
        return urljoin(self.base_url, url)
    
    def add_error(self, message: str, phase: str):
        """Add error to errors list"""
        self.errors.append({"message": message, "phase": phase})
        logger.error(f"[{phase}] {message}")
    
    @abstractmethod
    async def scrape(self) -> Dict[str, Any]:
        """Main scraping method to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def extract_metadata(self, html: str) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        pass
    
    @abstractmethod
    def parse_sections(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML into sections"""
        pass