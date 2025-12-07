"""
Intelligent fallback strategy for choosing between static and JS rendering
Prioritizes known static domains and lazy-initializes Playwright.
"""
import re
from typing import Tuple, Dict, Any
import logging
import asyncio
from urllib.parse import urlparse

from .static_scraper import StaticScraper
from .playwright_scraper import PlaywrightScraper

logger = logging.getLogger(__name__)


class FallbackStrategy:
    """Decides when to use static vs JS rendering"""

    def __init__(self):
        self.static_scraper = StaticScraper()
        self.playwright_scraper = None  # Initialize lazily

        # Websites known to be static (skip JS entirely)
        self.known_static_domains = [
            'wikipedia.org',
            'developer.mozilla.org',
            'mdn.io',
            'w3.org',
            'stackoverflow.com',
            'github.com',
            'gitlab.com',
            'python.org',
            'docs.python.org',
            'docs.microsoft.com',
            'nodejs.org',
            'ruby-lang.org',
            'php.net',
            'mysql.com'
        ]

        # Websites that definitely need JS
        self.js_required_domains = [
            'vercel.com',
            'nextjs.org',
            'react.dev',
            'vuejs.org',
            'angular.io',
            'svelte.dev',
            'nuxt.com',
            'infinite-scroll.com',
            'unsplash.com',
            'figma.com',
            'notion.so',
            'airtable.com',
            'news.ycombinator.com',  # Force JS for Hacker News
            'hacker-news.com'        # (rarely used)
        ]

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
            r'single-page',
            r'data-fetch',
            r'data-load'
        ]

    async def scrape_with_fallback(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Scrape with intelligent fallback strategy

        Returns:
            Tuple[str, dict]: (strategy_used, scraped_data)
            strategies: 'static', 'js', 'hybrid'
        """
        logger.info(f"Applying fallback strategy for: {url}")

        # Parse URL to get domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # Step 1: Check if domain is known to be static
        if self._is_known_static_domain(domain):
            logger.info(f"Domain {domain} is known static - using static scraper only")
            try:
                result = await self.static_scraper.scrape(url)
                return 'static', result.dict()
            except Exception as e:
                logger.error(f"Static scraping failed for known static site: {e}")
                # Even if it fails, don't try JS for known static sites
                raise

        # Step 2: Check if domain definitely needs JS
        if self._requires_javascript_by_domain(domain):
            logger.info(f"Domain {domain} requires JavaScript - using Playwright")
            try:
                result = await self._get_playwright_scraper().scrape(url)
                return 'js', result.dict()
            except Exception as e:
                logger.error(f"JS scraping failed for JS site: {e}")
                raise

        # Step 3: Try static first (default strategy)
        try:
            static_result = await self.static_scraper.scrape(url)
            static_data = static_result.dict()

            # Check if static scraping was sufficient
            if self._static_is_sufficient(static_data):
                logger.info("Static scraping sufficient")
                return 'static', static_data

            # If not sufficient, check if JS might help
            if self._js_might_help(static_data):
                logger.info("Content suggests JS might be needed - trying Playwright")
                try:
                    # Use shorter timeout for fallback
                    js_result = await self._get_playwright_scraper().scrape(url)
                    js_data = js_result.dict()

                    # Check if JS actually provided more content
                    if self._js_provided_more_content(static_data, js_data):
                        logger.info("JS provided additional content")
                        return 'js', js_data
                    else:
                        logger.info("JS didn't provide additional useful content")
                        return 'static', static_data
                except asyncio.TimeoutError:
                    logger.warning("Playwright timed out, using static results")
                    return 'static', static_data
                except Exception as js_error:
                    logger.warning(f"Playwright failed: {js_error}, using static results")
                    return 'static', static_data
            else:
                logger.info("Static content looks complete")
                return 'static', static_data

        except Exception as static_error:
            logger.warning(f"Static scraping failed: {static_error}, trying Playwright as fallback")
            try:
                js_result = await self._get_playwright_scraper().scrape(url)
                return 'js', js_result.dict()
            except Exception as js_error:
                logger.error(f"Both static and JS scraping failed: {js_error}")
                raise

    def _is_known_static_domain(self, domain: str) -> bool:
        """Check if domain is known to be static"""
        for static_domain in self.known_static_domains:
            if static_domain in domain:
                return True
        return False

    def _requires_javascript_by_domain(self, domain: str) -> bool:
        """Check if domain is known to require JS"""
        for js_domain in self.js_required_domains:
            if js_domain in domain:
                return True
        return False

    def _get_playwright_scraper(self):
        """Lazy initialize Playwright scraper"""
        if self.playwright_scraper is None:
            self.playwright_scraper = PlaywrightScraper(headless=True)
        return self.playwright_scraper

    def _static_is_sufficient(self, result: Dict[str, Any]) -> bool:
        """Determine if static scraping provided sufficient content"""
        if not result.get('sections'):
            return False

        sections = result.get('sections', [])

        # Check total text content
        total_text = 0
        for section in sections:
            content = section.get('content', {})
            text = content.get('text', '')
            total_text += len(text)

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

        # For Wikipedia-like sites, don't require 'main' in label
        # Wikipedia sections have labels like "Artificial intelligence", "History", etc.
        # So we're more lenient here
        return True

    def _js_might_help(self, result: Dict[str, Any]) -> bool:
        """Check if the page might benefit from JS rendering"""
        sections = result.get('sections', [])

        # 1. Very little text (less than 200 chars)
        total_text = 0
        for section in sections:
            content = section.get('content', {})
            text = content.get('text', '')
            total_text += len(text)

        if total_text < 200:
            return True

        # 2. Check for JS framework patterns in HTML
        js_indicators = 0
        for section in sections:
            raw_html = section.get('rawHtml', '').lower()

            # Check for common JS patterns
            for pattern in self.js_patterns:
                if re.search(pattern, raw_html):
                    js_indicators += 1
                    break

            # Check for placeholder content
            placeholder_patterns = [
                'loading...',
                'please wait',
                'fetching',
                '<!-- empty -->',
                'data-loading',
                'data-placeholder',
                'lazy-load'
            ]

            for pattern in placeholder_patterns:
                if pattern in raw_html.lower():
                    js_indicators += 1
                    break

        # If we found 2 or more JS indicators
        return js_indicators >= 2

    def _js_provided_more_content(self, static_result: Dict[str, Any], js_result: Dict[str, Any]) -> bool:
        """Compare static and JS results to see if JS provided more/better content"""
        static_sections = static_result.get('sections', [])
        js_sections = js_result.get('sections', [])

        if not js_sections:
            return False

        # Compare text content
        static_text = 0
        js_text = 0

        for section in static_sections:
            content = section.get('content', {})
            static_text += len(content.get('text', ''))

        for section in js_sections:
            content = section.get('content', {})
            js_text += len(content.get('text', ''))

        # JS should provide at least 50% more text
        if js_text > static_text * 1.5:
            return True

        # Compare number of sections
        if len(js_sections) > len(static_sections) + 2:  # At least 3 more sections
            return True

        # Check for interactive content that only JS could get
        js_interactions = js_result.get('interactions', {})
        if js_interactions.get('clicks') or js_interactions.get('scrolls', 0) > 0:
            return True

        return False