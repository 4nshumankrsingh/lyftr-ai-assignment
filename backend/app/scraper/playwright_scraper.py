"""
Enhanced Playwright scraper with Phase 4 & 5 improvements
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import re

try:
    from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not installed. JS rendering will not work.")

from .base_scraper import BaseScraper
from .static_scraper import StaticScraper
from .interaction_handler import InteractionHandler
from .content_comparator import ContentComparator
from .performance_optimizer import PerformanceOptimizer
from ..models.schemas import ScrapeResult, Meta, Section, Content, Link, Image, Interaction, Error, SectionType

logger = logging.getLogger(__name__)

class PlaywrightScraper(BaseScraper):
    """Enhanced scraper for JavaScript-rendered websites"""
    
    def __init__(self, headless: bool = True, max_depth: int = 3):
        super().__init__()
        self.headless = headless
        self.max_depth = max_depth
        self.timeout = 45000  # 45 seconds timeout
        self.interaction_handler = InteractionHandler(max_depth=max_depth)
        self.content_comparator = ContentComparator()
        self.performance_optimizer = PerformanceOptimizer(max_total_time=180000)  # 3 minutes total
        
        # Initialize interactions
        self.interactions_recorded = Interaction(
            clicks=[],
            scrolls=0,
            pages=[]
        )
        
        # Reuse static parsing logic
        self.static_scraper = StaticScraper()
        
        # Enhanced noise selectors
        self.noise_selectors = [
            'script', 'style', 'noscript', 'iframe',
            '[class*="cookie"]', '[class*="banner"]', '[class*="popup"]',
            '[class*="modal"]', '[class*="advertisement"]', '[class*="ad-"]',
            '[id*="cookie"]', '[id*="banner"]', '[id*="popup"]',
            '[role="alert"]', '[aria-label*="cookie"]',
            '.ad-container', '.adsbygoogle', '.ad-slot',
            '.newsletter', '.subscribe-modal',
            '.chat-widget', '.live-chat',
            '.notification', '.alert-banner'
        ]
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Enhanced main scraping method with Phase 4 features"""
        if not PLAYWRIGHT_AVAILABLE:
            error_msg = "Playwright not installed. Cannot perform JS rendering."
            logger.error(error_msg)
            return self._create_error_result(url, error_msg)
        
        self.url = url
        self.base_url = self._get_base_url(url)
        self.errors = []
        visited_pages = [url]
        
        # Start performance monitoring
        self.performance_optimizer.start_time = time.time()
        
        try:
            async with async_playwright() as p:
                # Launch browser with enhanced options
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',
                        '--disable-software-rasterizer',
                        '--disable-extensions'
                    ],
                    timeout=60000
                )
                
                # Create context with realistic settings
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation'],
                    color_scheme='dark'
                )
                
                # Create page with enhanced settings
                page = await context.new_page()
                
                # Set timeouts
                page.set_default_timeout(self.timeout)
                page.set_default_navigation_timeout(self.timeout)
                
                # Add request interception to block ads and trackers
                await self._setup_request_interception(page)
                
                # Navigate to URL with enhanced wait strategy
                logger.info(f"Navigating to {url}")
                try:
                    await self._navigate_with_retry(page, url)
                except Exception as e:
                    self.add_error(f"Navigation failed: {str(e)}", "navigation")
                    # Try without interception
                    await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                
                # Wait for content with multiple strategies
                await self._wait_for_content_enhanced(page)
                
                # Record initial page
                current_page_url = page.url
                if current_page_url not in visited_pages:
                    visited_pages.append(current_page_url)
                
                # Remove noise elements before interactions
                await self._remove_noise_elements(page)
                
                # Perform enhanced interactive scraping
                logger.info("Starting enhanced interactive scraping...")
                clicks, pages, scrolls = await self.interaction_handler.handle_interactive_scraping(
                    page, visited_pages, self.max_depth
                )
                
                # Update interactions
                self.interactions_recorded.clicks = clicks
                self.interactions_recorded.scrolls = scrolls
                self.interactions_recorded.pages = pages
                
                # Check if we achieved minimum depth
                total_interactions = len(clicks) + scrolls
                if total_interactions < 3:
                    logger.warning(f"Only achieved depth {total_interactions} < 3")
                    self.add_error(f"Minimum depth not reached: {total_interactions} interactions", "interaction")
                else:
                    logger.info(f"Successfully achieved depth {total_interactions} >= 3")
                
                # Get final HTML after all interactions
                final_html = await page.content()
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(final_html, 'lxml')
                
                # Remove noise from parsed HTML
                self._remove_noise_from_soup(soup)
                
                # Extract metadata
                metadata = self._extract_enhanced_metadata(soup)
                
                # Extract sections with deduplication
                self.static_scraper.url = url
                self.static_scraper.base_url = self.base_url
                sections = self.static_scraper._extract_sections(soup)
                
                # Filter duplicate sections
                unique_sections = self.content_comparator.get_new_sections([s.dict() for s in sections])
                sections = [Section(**s) for s in unique_sections]
                
                # Close browser
                await browser.close()
                
                # Check performance
                elapsed_time = (time.time() - self.performance_optimizer.start_time) * 1000
                logger.info(f"Scraping completed in {elapsed_time:.0f}ms with {len(sections)} unique sections")
                
                # Add performance metrics to metadata
                metadata["scrapeDuration"] = f"{elapsed_time:.0f}ms"
                metadata["interactionDepth"] = total_interactions
                
                return ScrapeResult(
                    url=url,
                    scrapedAt=datetime.utcnow().isoformat() + "Z",
                    meta=Meta(**metadata),
                    sections=sections,
                    interactions=self.interactions_recorded,
                    errors=[Error(message=e["message"], phase=e["phase"]) for e in self.errors],
                    performance={
                        "duration_ms": elapsed_time,
                        "sections_found": len(sections),
                        "interaction_depth": total_interactions,
                        "pages_visited": len(pages)
                    }
                )
                
        except asyncio.TimeoutError as e:
            error_msg = f"Scraping timeout after {self.timeout}ms"
            logger.error(error_msg)
            self.add_error(error_msg, "timeout")
            return self._create_error_result(url, error_msg)
            
        except Exception as e:
            logger.error(f"Playwright scraping error: {e}")
            self.add_error(str(e), "js_render")
            return self._create_error_result(url, str(e))
    
    async def _setup_request_interception(self, page: Page):
        """Setup request interception to block ads and trackers"""
        await page.route("**/*", lambda route: self._route_handler(route))
    
    async def _route_handler(self, route):
        """Handle route interception"""
        request = route.request
        resource_type = request.resource_type
        
        # Block unnecessary resources for faster loading
        if resource_type in ["image", "stylesheet", "font", "media"]:
            await route.abort()
        elif any(domain in request.url for domain in [
            "google-analytics.com",
            "googletagmanager.com",
            "facebook.com/tr",
            "doubleclick.net",
            "adsystem.com"
        ]):
            await route.abort()
        else:
            await route.continue_()
    
    async def _navigate_with_retry(self, page: Page, url: str, max_retries: int = 2):
        """Navigate with retry logic"""
        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    # First attempt: networkidle
                    await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                elif attempt == 1:
                    # Second attempt: load
                    await page.goto(url, wait_until='load', timeout=self.timeout)
                else:
                    # Last attempt: domcontentloaded
                    await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                break
            except Exception as e:
                if attempt == max_retries:
                    raise
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2000)  # Wait 2 seconds before retry
    
    async def _wait_for_content_enhanced(self, page: Page):
        """Enhanced wait strategy for dynamic content"""
        try:
            # Strategy 1: Wait for network idle
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Strategy 2: Wait for body to have substantial content
            await page.wait_for_function(
                '''
                () => {
                    const body = document.body;
                    if (!body) return false;
                    
                    const text = body.textContent || '';
                    const textLength = text.replace(/\\s+/g, ' ').trim().length;
                    
                    const visibleElements = body.querySelectorAll('*:not(script):not(style):not(iframe)');
                    const visibleCount = Array.from(visibleElements).filter(el => {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               style.opacity !== '0';
                    }).length;
                    
                    return textLength > 100 && visibleCount > 10;
                }
                ''',
                timeout=10000
            )
            
            # Strategy 3: Wait for common content containers
            content_selectors = ['main', 'article', '#content', '.content', '[role="main"]']
            for selector in content_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Found content container: {selector}")
                    break
                except:
                    continue
            
            # Strategy 4: Check for loading indicators
            await page.wait_for_function(
                '''
                () => {
                    const loadingSelectors = [
                        '.loading', '[data-loading]', '.spinner',
                        '.loader', '[aria-busy="true"]'
                    ];
                    
                    for (const selector of loadingSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            const style = window.getComputedStyle(el);
                            if (style.display !== 'none') {
                                return false; // Still loading
                            }
                        }
                    }
                    return true; // No loading indicators visible
                }
                ''',
                timeout=10000
            )
            
            # Small delay for dynamic content
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            self.add_error(f"Enhanced wait strategy failed: {str(e)}", "wait")
            # Continue with basic wait
            await page.wait_for_timeout(3000)
    
    async def _remove_noise_elements(self, page: Page):
        """Remove noise elements from the page"""
        try:
            for selector in self.noise_selectors:
                try:
                    await page.evaluate(f'''
                        (selector) => {{
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {{
                                try {{
                                    el.remove();
                                }} catch (e) {{
                                    // Ignore errors
                                }}
                            }});
                        }}
                    ''', selector)
                except:
                    continue
            logger.info("Removed noise elements from page")
        except Exception as e:
            self.add_error(f"Failed to remove noise elements: {str(e)}", "noise_removal")
    
    def _remove_noise_from_soup(self, soup: BeautifulSoup):
        """Remove noise elements from BeautifulSoup"""
        for selector in self.noise_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except:
                continue
    
    def _extract_enhanced_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract enhanced metadata"""
        metadata = {
            "title": "",
            "description": "",
            "language": "en",
            "canonical": None,
            "keywords": [],
            "author": "",
            "viewport": "",
            "themeColor": "",
            "ogType": ""
        }
        
        try:
            # Title
            title_elem = soup.find('title')
            og_title = soup.find('meta', property='og:title')
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            
            if og_title and og_title.get('content'):
                metadata["title"] = og_title['content'].strip()
            elif twitter_title and twitter_title.get('content'):
                metadata["title"] = twitter_title['content'].strip()
            elif title_elem and title_elem.string:
                metadata["title"] = title_elem.string.strip()
            
            # Description
            desc_selectors = [
                ('meta', {'name': 'description'}),
                ('meta', {'property': 'og:description'}),
                ('meta', {'name': 'twitter:description'}),
                ('meta', {'itemprop': 'description'})
            ]
            
            for tag, attrs in desc_selectors:
                elem = soup.find(tag, attrs)
                if elem and elem.get('content'):
                    metadata["description"] = elem['content'].strip()
                    break
            
            # Language
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                metadata["language"] = html_tag['lang'].split('-')[0]
            
            # Canonical
            canonical = soup.find('link', rel='canonical')
            if canonical and canonical.get('href'):
                metadata["canonical"] = self._make_absolute_url(canonical['href'])
            
            # Keywords
            keywords = soup.find('meta', attrs={'name': 'keywords'})
            if keywords and keywords.get('content'):
                metadata["keywords"] = [k.strip() for k in keywords['content'].split(',')]
            
            # Author
            author = soup.find('meta', attrs={'name': 'author'})
            if author and author.get('content'):
                metadata["author"] = author['content'].strip()
            
            # Viewport
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport and viewport.get('content'):
                metadata["viewport"] = viewport['content'].strip()
            
            # Theme Color
            theme_color = soup.find('meta', attrs={'name': 'theme-color'})
            if theme_color and theme_color.get('content'):
                metadata["themeColor"] = theme_color['content'].strip()
            
            # Open Graph Type
            og_type = soup.find('meta', property='og:type')
            if og_type and og_type.get('content'):
                metadata["ogType"] = og_type['content'].strip()
            
        except Exception as e:
            self.add_error(f"Enhanced metadata extraction error: {str(e)}", "metadata")
        
        return metadata
    
    def _create_error_result(self, url: str, error_message: str) -> ScrapeResult:
        """Create error result when scraping fails"""
        from ..models.schemas import ScrapeResult, Meta, Interaction, Error
        
        return ScrapeResult(
            url=url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=Meta(),
            sections=[],
            interactions=self.interactions_recorded,
            errors=[Error(message=error_message, phase="js_render")],
            performance={
                "duration_ms": 0,
                "sections_found": 0,
                "interaction_depth": 0,
                "pages_visited": 0
            }
        )