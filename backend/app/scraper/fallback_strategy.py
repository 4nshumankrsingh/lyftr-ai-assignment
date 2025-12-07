"""
Intelligent fallback strategy for choosing between static and JS rendering
"""
import re
from typing import Tuple, Optional
import logging

from .static_scraper import StaticScraper
from .playwright_scraper import PlaywrightScraper

logger = logging.getLogger(__name__)

class FallbackStrategy:
    """Decides when to use static vs JS rendering"""
    
    def __init__(self):
        self.static_scraper = StaticScraper()
        self.playwright_scraper = PlaywrightScraper(headless=True)
        
        # Patterns that suggest JS-rendered content
        self.js_patterns = [
            r'data-react',
            r'data-vue',
            r'data-angular',
            r'ng-',
            r'v-',
            r'x-data',
            r'_next',
            r'__next',
            r'hydrated',
            r'client-side',
            r'spa',
            r'single-page'
        ]
        
        # Selectors that suggest dynamic content
        self.dynamic_selectors = [
            '[data-component]',
            '[data-page]',
            '[data-state]',
            '[data-fetch]',
            '.js-',
            '.dynamic',
            '.async'
        ]
        
        # Websites known to require JS
        self.js_required_domains = [
            'vercel.com',
            'nextjs.org',
            'react.dev',
            'vuejs.org',
            'angular.io',
            'svelte.dev',
            'nuxt.com'
        ]
    
    async def scrape_with_fallback(self, url: str) -> Tuple[str, dict]:
        """
        Scrape with intelligent fallback strategy
        
        Returns:
            Tuple[str, dict]: (strategy_used, scraped_data)
            strategies: 'static', 'js', 'hybrid'
        """
        logger.info(f"Applying fallback strategy for: {url}")
        
        # Check if JS is definitely required
        if self._requires_javascript(url):
            logger.info("Domain requires JavaScript - using Playwright")
            result = await self.playwright_scraper.scrape(url)
            return 'js', result.dict()
        
        # Try static scraping first
        try:
            static_result = await self.static_scraper.scrape(url)
            
            # Check if static scraping was sufficient
            if self._static_sufficient(static_result):
                logger.info("Static scraping sufficient")
                return 'static', static_result.dict()
            
            # Check if JS might help
            if self._might_need_javascript(static_result):
                logger.info("Content suggests JS might be needed - falling back to Playwright")
                
                # Try JS rendering
                js_result = await self.playwright_scraper.scrape(url)
                
                # Compare results
                if self._js_provided_more_content(static_result, js_result):
                    logger.info("JS provided additional content")
                    return 'js', js_result.dict()
                else:
                    logger.info("JS didn't provide additional useful content")
                    return 'static', static_result.dict()
            else:
                logger.info("Static content looks complete")
                return 'static', static_result.dict()
                
        except Exception as e:
            logger.warning(f"Static scraping failed, falling back to JS: {e}")
            
            # Fallback to JS rendering
            try:
                js_result = await self.playwright_scraper.scrape(url)
                return 'js', js_result.dict()
            except Exception as js_error:
                logger.error(f"Both static and JS scraping failed: {js_error}")
                raise js_error
    
    def _requires_javascript(self, url: str) -> bool:
        """Check if URL domain requires JavaScript"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check against known JS-heavy domains
        for js_domain in self.js_required_domains:
            if js_domain in domain:
                return True
        
        # Check URL patterns
        js_url_patterns = ['#', '#!/', '_next/']
        for pattern in js_url_patterns:
            if pattern in url:
                return True
        
        return False
    
    def _static_sufficient(self, result: dict) -> bool:
        """Determine if static scraping provided sufficient content"""
        if not result.get('sections'):
            return False
        
        sections = result.get('sections', [])
        
        # Check total text content
        total_text = sum(len(section.get('content', {}).get('text', '')) for section in sections)
        if total_text < 100:  # Less than 100 characters
            return False
        
        # Check if we have meaningful sections
        meaningful_sections = 0
        for section in sections:
            content = section.get('content', {})
            text = content.get('text', '')
            headings = content.get('headings', [])
            links = content.get('links', [])
            
            if len(text) > 50 or len(headings) > 0 or len(links) > 0:
                meaningful_sections += 1
        
        if meaningful_sections < 1:
            return False
        
        # Check for common static content indicators
        has_main_content = any('main' in section.get('label', '').lower() 
                              or 'content' in section.get('label', '').lower() 
                              for section in sections)
        
        return has_main_content and total_text > 200
    
    def _might_need_javascript(self, result: dict) -> bool:
        """Check if the page might benefit from JS rendering"""
        sections = result.get('sections', [])
        
        # Check for common JS-rendered page indicators
        indicators = []
        
        # 1. Very little text
        total_text = sum(len(section.get('content', {}).get('text', '')) for section in sections)
        if total_text < 500:
            indicators.append("low_text_content")
        
        # 2. Many script tags in raw HTML
        script_count = 0
        for section in sections:
            raw_html = section.get('rawHtml', '').lower()
            script_count += raw_html.count('<script')
        
        if script_count > 5:
            indicators.append("many_scripts")
        
        # 3. Common JS framework patterns
        for section in sections:
            raw_html = section.get('rawHtml', '').lower()
            for pattern in self.js_patterns:
                if re.search(pattern, raw_html):
                    indicators.append(f"js_pattern_{pattern}")
                    break
        
        # 4. Empty or placeholder content
        placeholder_patterns = [
            'loading...',
            'please wait',
            'fetching',
            '<!-- empty -->',
            'data-loading',
            'data-placeholder'
        ]
        
        for section in sections:
            raw_html = section.get('rawHtml', '').lower()
            for pattern in placeholder_patterns:
                if pattern in raw_html:
                    indicators.append("placeholder_content")
                    break
        
        # Decision logic
        if len(indicators) >= 2:
            logger.info(f"JS might be needed. Indicators: {indicators}")
            return True
        
        return False
    
    def _js_provided_more_content(self, static_result: dict, js_result: dict) -> bool:
        """Compare static and JS results to see if JS provided more/better content"""
        static_sections = static_result.get('sections', [])
        js_sections = js_result.get('sections', [])
        
        if not js_sections:
            return False
        
        # Compare text content
        static_text = sum(len(section.get('content', {}).get('text', '')) 
                         for section in static_sections)
        js_text = sum(len(section.get('content', {}).get('text', '')) 
                     for section in js_sections)
        
        # JS should provide at least 50% more text
        if js_text > static_text * 1.5:
            return True
        
        # Compare number of sections
        if len(js_sections) > len(static_sections) * 1.2:
            return True
        
        # Check if JS captured interactive content
        js_interactions = js_result.get('interactions', {})
        if js_interactions.get('clicks') or js_interactions.get('scrolls', 0) > 0:
            return True
        
        return False