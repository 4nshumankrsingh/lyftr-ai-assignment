"""
Playwright-based scraper for JavaScript-rendered websites
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup, Tag
import re

try:
    from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not installed. JS rendering will not work.")

from .base_scraper import BaseScraper
from .static_scraper import StaticScraper
from ..models.schemas import ScrapeResult, Meta, Section, Content, Link, Image, Interaction, Error, SectionType

logger = logging.getLogger(__name__)

class PlaywrightScraper(BaseScraper):
    """Scraper for JavaScript-rendered websites using Playwright"""
    
    def __init__(self, headless: bool = True):
        super().__init__()
        self.headless = headless
        self.timeout = 30000  # 30 seconds timeout
        self.interactions_recorded = Interaction(
            clicks=[],
            scrolls=0,
            pages=[]
        )
        self.static_scraper = StaticScraper()  # Reuse static parsing logic
        
        # Selectors for common interactive elements
        self.tab_selectors = [
            '[role="tab"]',
            '[class*="tab"]',
            'button[aria-controls]',
            'nav a',
            '.tabs button',
            '.tab-nav button'
        ]
        
        self.load_more_selectors = [
            'button:has-text("Load more")',
            'button:has-text("Show more")',
            'button:has-text("See more")',
            'button:has-text("View more")',
            'a:has-text("Load more")',
            'a:has-text("Show more")',
            '[class*="load-more"]',
            '[class*="show-more"]',
            '#load-more',
            '#show-more'
        ]
        
        self.next_page_selectors = [
            'a:has-text("Next")',
            'a:has-text("Next page")',
            'a[rel="next"]',
            '[class*="next"]',
            '[class*="pagination-next"]',
            'button:has-text("Next")'
        ]
        
        # Wait selectors for common content containers
        self.content_selectors = [
            'main',
            'article',
            '[class*="content"]',
            '[class*="main"]',
            'body'
        ]
    
    async def scrape(self, url: str, max_depth: int = 3) -> ScrapeResult:
        """Main scraping method with Playwright"""
        if not PLAYWRIGHT_AVAILABLE:
            error_msg = "Playwright not installed. Cannot perform JS rendering."
            logger.error(error_msg)
            return self._create_error_result(url, error_msg)
        
        self.url = url
        self.base_url = self._get_base_url(url)
        self.errors = []
        visited_pages = [url]
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
                
                # Create context with realistic viewport
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US'
                )
                
                # Create page
                page = await context.new_page()
                
                # Set default timeout
                page.set_default_timeout(self.timeout)
                
                # Navigate to URL with wait strategies
                logger.info(f"Navigating to {url}")
                try:
                    await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                except PlaywrightTimeoutError:
                    logger.warning("Network idle timeout, continuing with DOM content loaded")
                    await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                
                # Wait for content to load
                await self._wait_for_content(page)
                
                # Record initial page
                current_page_url = page.url
                if current_page_url not in visited_pages:
                    visited_pages.append(current_page_url)
                
                # Perform interactive scraping
                html_content = await self._perform_interactive_scraping(page, max_depth, visited_pages)
                
                # Close browser
                await browser.close()
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Extract metadata
                metadata = self.static_scraper._extract_metadata(soup)
                
                # Extract sections
                self.static_scraper.url = url
                self.static_scraper.base_url = self.base_url
                sections = self.static_scraper._extract_sections(soup)
                
                # Update interactions with visited pages
                self.interactions_recorded.pages = visited_pages
                
                return ScrapeResult(
                    url=url,
                    scrapedAt=datetime.utcnow().isoformat() + "Z",
                    meta=Meta(**metadata),
                    sections=sections,
                    interactions=self.interactions_recorded,
                    errors=[Error(message=e["message"], phase=e["phase"]) for e in self.errors]
                )
                
        except Exception as e:
            logger.error(f"Playwright scraping error: {e}")
            self.add_error(str(e), "js_render")
            return self._create_error_result(url, str(e))
    
    async def _wait_for_content(self, page: Page) -> None:
        """Wait for content to load using multiple strategies"""
        try:
            # Strategy 1: Wait for network idle
            await page.wait_for_load_state('networkidle')
            
            # Strategy 2: Wait for any content selector
            for selector in self.content_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Found content selector: {selector}")
                    break
                except:
                    continue
            
            # Strategy 3: Wait for body to have some content
            await page.wait_for_function(
                '() => document.body && document.body.textContent && document.body.textContent.length > 100',
                timeout=5000
            )
            
            # Strategy 4: Small delay for dynamic content
            await page.wait_for_timeout(1000)
            
        except Exception as e:
            self.add_error(f"Wait strategy failed: {str(e)}", "wait")
            # Continue anyway - some content might be loaded
    
    async def _perform_interactive_scraping(
        self, 
        page: Page, 
        max_depth: int, 
        visited_pages: List[str]
    ) -> str:
        """Perform interactive actions and collect HTML"""
        html_contents = []
        
        # Get initial HTML
        html_contents.append(await page.content())
        
        # Try tab interactions
        await self._handle_tabs(page)
        
        # Try load more interactions
        await self._handle_load_more(page, max_depth)
        
        # Try pagination
        await self._handle_pagination(page, max_depth, visited_pages)
        
        # Try infinite scroll
        await self._handle_infinite_scroll(page, max_depth)
        
        # Get final HTML after all interactions
        final_html = await page.content()
        
        return final_html
    
    async def _handle_tabs(self, page: Page) -> None:
        """Click on tab elements to reveal hidden content"""
        try:
            for selector in self.tab_selectors:
                try:
                    tabs = await page.query_selector_all(selector)
                    if tabs:
                        logger.info(f"Found {len(tabs)} tabs with selector: {selector}")
                        
                        # Click on first 3 tabs
                        for i, tab in enumerate(tabs[:3]):
                            try:
                                # Check if tab is visible and clickable
                                is_visible = await tab.is_visible()
                                if is_visible:
                                    await tab.click()
                                    await page.wait_for_timeout(1000)  # Wait for content
                                    self.interactions_recorded.clicks.append(f"tab-{i}: {selector}")
                                    logger.info(f"Clicked tab {i}")
                            except Exception as e:
                                self.add_error(f"Failed to click tab {i}: {str(e)}", "click")
                                continue
                        
                        break  # Stop after first successful selector
                except:
                    continue
                    
        except Exception as e:
            self.add_error(f"Tab handling failed: {str(e)}", "click")
    
    async def _handle_load_more(self, page: Page, max_depth: int) -> None:
        """Click 'Load more' buttons to reveal additional content"""
        try:
            for selector in self.load_more_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    if buttons:
                        logger.info(f"Found {len(buttons)} load more buttons with selector: {selector}")
                        
                        # Click each button up to max_depth times
                        for i in range(min(max_depth, len(buttons))):
                            try:
                                button = buttons[i]
                                is_visible = await button.is_visible()
                                is_enabled = await button.is_enabled()
                                
                                if is_visible and is_enabled:
                                    # Scroll to button
                                    await button.scroll_into_view_if_needed()
                                    await page.wait_for_timeout(500)
                                    
                                    # Click button
                                    await button.click()
                                    await page.wait_for_timeout(2000)  # Wait for content to load
                                    
                                    self.interactions_recorded.clicks.append(f"load-more-{i}: {selector}")
                                    logger.info(f"Clicked load more button {i}")
                                    
                                    # Wait for new content
                                    await page.wait_for_timeout(1000)
                            except Exception as e:
                                self.add_error(f"Failed to click load more {i}: {str(e)}", "click")
                                continue
                        
                        break
                except:
                    continue
                    
        except Exception as e:
            self.add_error(f"Load more handling failed: {str(e)}", "click")
    
    async def _handle_pagination(self, page: Page, max_depth: int, visited_pages: List[str]) -> None:
        """Follow pagination links"""
        try:
            for selector in self.next_page_selectors:
                try:
                    next_links = await page.query_selector_all(selector)
                    if next_links:
                        logger.info(f"Found {len(next_links)} pagination links with selector: {selector}")
                        
                        # Follow up to max_depth pages
                        for i in range(max_depth):
                            try:
                                # Find the most likely "next" link
                                next_link = None
                                for link in next_links:
                                    text = await link.text_content()
                                    if text and any(word in text.lower() for word in ['next', '>', '»']):
                                        next_link = link
                                        break
                                
                                if not next_link and next_links:
                                    next_link = next_links[0]  # Use first if no obvious "next"
                                
                                if next_link:
                                    # Get URL
                                    href = await next_link.get_attribute('href')
                                    if href:
                                        # Click and navigate
                                        await next_link.click()
                                        await page.wait_for_load_state('networkidle')
                                        await self._wait_for_content(page)
                                        
                                        current_url = page.url
                                        if current_url not in visited_pages:
                                            visited_pages.append(current_url)
                                        
                                        self.interactions_recorded.clicks.append(f"pagination-{i}: {selector}")
                                        logger.info(f"Followed pagination link to page {i+2}")
                                        
                                        # Update next links for new page
                                        next_links = await page.query_selector_all(selector)
                                    else:
                                        break  # No href attribute
                                else:
                                    break  # No more links
                                    
                            except Exception as e:
                                self.add_error(f"Pagination step {i} failed: {str(e)}", "click")
                                break
                        
                        break
                except:
                    continue
                    
        except Exception as e:
            self.add_error(f"Pagination handling failed: {str(e)}", "click")
    
    async def _handle_infinite_scroll(self, page: Page, max_depth: int) -> None:
        """Scroll down to trigger infinite scroll"""
        try:
            logger.info(f"Attempting infinite scroll (depth: {max_depth})")
            
            # Get initial scroll position and content
            prev_height = await page.evaluate('document.body.scrollHeight')
            prev_content_length = len(await page.content())
            
            for i in range(max_depth):
                try:
                    # Scroll to bottom
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await page.wait_for_timeout(2000)  # Wait for potential content load
                    
                    # Check if new content loaded
                    new_height = await page.evaluate('document.body.scrollHeight')
                    new_content_length = len(await page.content())
                    
                    if new_height > prev_height or new_content_length > prev_content_length:
                        self.interactions_recorded.scrolls += 1
                        logger.info(f"Scroll {i+1}: New content detected")
                        prev_height = new_height
                        prev_content_length = new_content_length
                        
                        # Wait a bit more for content to settle
                        await page.wait_for_timeout(1000)
                    else:
                        logger.info(f"Scroll {i+1}: No new content, stopping")
                        break
                        
                except Exception as e:
                    self.add_error(f"Scroll {i} failed: {str(e)}", "scroll")
                    break
                    
        except Exception as e:
            self.add_error(f"Infinite scroll failed: {str(e)}", "scroll")
    
    def _create_error_result(self, url: str, error_message: str) -> ScrapeResult:
        """Create error result when scraping fails"""
        return ScrapeResult(
            url=url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=Meta(),
            sections=[],
            interactions=self.interactions_recorded,
            errors=[Error(message=error_message, phase="js_render")]
        )