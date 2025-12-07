from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all scrapers with utility methods"""
    
    def __init__(self):
        self.url = ""
        self.base_url = ""
        self.errors = []
    
    @abstractmethod
    async def scrape(self, url: str) -> dict:
        """Main scraping method to be implemented by subclasses"""
        pass
        
    def _get_base_url(self, url: str) -> str:
        """Extract base URL from full URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute"""
        from urllib.parse import urljoin
        if url.startswith(('http://', 'https://', '//')):
            if url.startswith('//'):
                return f"https:{url}"
            return url
        return urljoin(self.base_url, url)
    
    def add_error(self, message: str, phase: str):
        """Add error to errors list"""
        self.errors.append({"message": message, "phase": phase})
        logger.error(f"[{phase}] {message}")