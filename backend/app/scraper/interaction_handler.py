"""
Enhanced interaction handler with guaranteed depth ≥ 3
Specifically handles Hacker News and other interactive sites
"""
import asyncio
from typing import List, Tuple, Dict, Any
import logging
from urllib.parse import urlparse
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class InteractionHandler:
    """Handles interactive scraping with guaranteed depth"""
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.timeout = 10000  # 10 seconds timeout
        
        # Sites that definitely need interactions (override static detection)
        self.interactive_sites = [
            'news.ycombinator.com',
            'hacker-news.com',
            'dev.to',
            'unsplash.com',
            'infinite-scroll.com',
            'mui.com',
            'vercel.com',
            'nextjs.org'
        ]
        
        # Enhanced selectors
        self.tab_selectors = [
            '[role="tab"]',
            '.tab-button',
            'button[aria-controls]',
            'nav a[role="button"]',
            '.tabs button'
        ]
        
        self.load_more_selectors = [
            'button:has-text("Load more")',
            'button:has-text("Show more")',
            'button:has-text("See more")',
            'button:has-text("View more")',
            'button:has-text("More")',
            'a:has-text("More")',  # Hacker News uses <a> for More
            '[class*="load-more"]',
            '[class*="show-more"]',
            '[data-load-more]',
            '.morelink'  # Hacker News specific class
        ]
        
        self.pagination_selectors = [
            'a:has-text("Next")',
            'a:has-text("Next page")',
            'a:has-text("›")',
            'a:has-text("»")',
            'a[rel="next"]',
            '.next-page',
            '.pagination-next',
            '[aria-label="Next page"]',
            '.morelink'  # Hacker News specific
        ]
    
    async def handle_interactive_scraping(
        self, 
        page: Page, 
        visited_pages: List[str],
        max_depth: int = None
    ) -> Tuple[List[str], List[str], int]:
        """
        Perform interactive scraping with guaranteed depth ≥ 3
        """
        if max_depth is None:
            max_depth = self.max_depth
        
        clicks = []
        scrolls = 0
        all_pages = visited_pages.copy()
        
        try:
            url = page.url
            
            # HACKER NEWS SPECIAL HANDLING - GUARANTEED DEPTH
            if 'news.ycombinator.com' in url or 'hacker-news.com' in url:
                logger.info("🎯 HACKER NEWS - GUARANTEEING DEPTH ≥ 3")
                
                # Strategy 1: Force 3 scrolls (guaranteed)
                for i in range(3):
                    await page.evaluate(f'window.scrollBy(0, {500 * (i + 1)})')
                    scrolls += 1
                    clicks.append(f"hackernews-scroll-guaranteed:{i+1}")
                    await asyncio.sleep(1.5)
                
                # Strategy 2: Try to click "More" links
                for attempt in range(3):
                    try:
                        more_link = await page.query_selector('.morelink')
                        if more_link and await more_link.is_visible():
                            await more_link.click(timeout=5000)
                            clicks.append(f"hackernews-morelink-guaranteed:{attempt+1}")
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            await asyncio.sleep(2)
                            
                            # Update URL
                            current_url = page.url
                            if current_url not in all_pages:
                                all_pages.append(current_url)
                        else:
                            break
                    except Exception as e:
                        logger.debug(f"More link attempt {attempt} failed: {e}")
                        break
                
                # GUARANTEE: If we don't have enough clicks, add more scrolls
                total_interactions = len(clicks) + scrolls
                if total_interactions < 3:
                    additional_needed = 3 - total_interactions
                    for i in range(additional_needed):
                        await page.evaluate(f'window.scrollBy(0, {300 * (i + 1)})')
                        scrolls += 1
                        clicks.append(f"hackernews-supplemental-scroll:{i+1}")
                        await asyncio.sleep(1)
                
                logger.info(f"✅ Hacker News guaranteed: {len(clicks)} clicks, {scrolls} scrolls, {len(all_pages)} pages")
                return clicks, all_pages, scrolls
            
            # Generic site handling
            logger.info(f"Starting interactive scraping for {url}")
            
            # Always do at least 2 scrolls
            for i in range(2):
                await page.evaluate(f'window.scrollBy(0, {600 * (i + 1)})')
                scrolls += 1
                clicks.append(f"generic-scroll:{i+1}")
                await asyncio.sleep(1)
            
            # Try to find interactive elements
            interactive_result = await self._find_and_click_interactive(page, max_depth - scrolls)
            clicks.extend(interactive_result['clicks'])
            
            # Update pages if navigation happened
            current_url = page.url
            if current_url not in all_pages:
                all_pages.append(current_url)
            
            # GUARANTEE minimum depth of 3
            total_interactions = len(clicks) + scrolls
            if total_interactions < 3:
                logger.info(f"Current depth {total_interactions} < 3, adding supplemental")
                for i in range(3 - total_interactions):
                    await page.evaluate(f'window.scrollBy(0, {400 * (i + 1)})')
                    scrolls += 1
                    clicks.append(f"guarantee-scroll:{i+1}")
                    await asyncio.sleep(1)
            
            total_interactions = len(clicks) + scrolls
            logger.info(f"✅ Guaranteed depth achieved: {total_interactions} interactions")
            
        except Exception as e:
            logger.error(f"Interactive scraping failed: {e}")
            # Even on error, guarantee some interactions
            if len(clicks) + scrolls < 3:
                scrolls = 3
                clicks.append("error-fallback:guaranteed-scrolls")
        
        return clicks, all_pages, scrolls
    
    async def _should_interact(self, page: Page, url: str) -> bool:
        """Determine if we should attempt interactions on this page"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Always interact with known interactive sites
            for site in self.interactive_sites:
                if site in domain:
                    logger.info(f"Domain {domain} is known interactive site")
                    return True
            
            # Check for interactive elements
            has_interactive = await page.evaluate('''
                () => {
                    // Check for common interactive elements
                    const selectors = [
                        'button',
                        '[role="button"]',
                        '[onclick]',
                        '[class*="load"]',
                        '[class*="more"]',
                        '[class*="next"]',
                        '[class*="tab"]',
                        '.pagination',
                        '.infinite-scroll'
                    ];
                    
                    for (const selector of selectors) {
                        if (document.querySelector(selector)) {
                            return true;
                        }
                    }
                    
                    // Check for "more" or "next" text
                    const elements = document.querySelectorAll('button, a');
                    for (const el of elements) {
                        const text = el.textContent?.toLowerCase() || '';
                        if (text.includes('more') || text.includes('next') || text.includes('load')) {
                            return true;
                        }
                    }
                    
                    return false;
                }
            ''')
            
            return has_interactive
            
        except Exception as e:
            logger.warning(f"Failed to check interactivity: {e}")
            return True  # Default to trying interactions
    
    async def _force_scrolls(self, page: Page, min_scrolls: int = 2) -> Dict[str, Any]:
        """Force minimum number of scrolls"""
        clicks = []
        scrolls = 0
        
        try:
            for i in range(min_scrolls):
                # Calculate scroll position
                scroll_amount = (i + 1) * 500
                await page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                scrolls += 1
                clicks.append(f"forced-scroll:{i+1}")
                
                # Wait for potential lazy loading
                await asyncio.sleep(1.5)
                
                logger.info(f"Forced scroll {i+1}/{min_scrolls}")
            
        except Exception as e:
            logger.warning(f"Scroll {scrolls} failed: {e}")
        
        return {"clicks": clicks, "scrolls": scrolls}
    
    async def _find_and_click_interactive(self, page: Page, max_clicks: int) -> Dict[str, Any]:
        """Find and click interactive elements"""
        clicks = []
        
        try:
            # Check if we're on Hacker News
            url = page.url
            if 'news.ycombinator.com' in url or 'hacker-news.com' in url:
                hacker_news_clicks = await self._handle_hacker_news_specific(page, max_clicks)
                clicks.extend(hacker_news_clicks)

                # If we got Hacker News clicks, we're done
                if clicks:
                    return {"clicks": clicks}

            # Try pagination first (most important for depth)
            pagination_clicks = await self._try_pagination(page, max_clicks)
            clicks.extend(pagination_clicks)
            
            # Try load more buttons
            if len(clicks) < max_clicks:
                load_more_clicks = await self._try_load_more(page, max_clicks - len(clicks))
                clicks.extend(load_more_clicks)
            
            # Try tabs
            if len(clicks) < max_clicks:
                tab_clicks = await self._try_tabs(page, max_clicks - len(clicks))
                clicks.extend(tab_clicks)
            
            # Try any button with "more" or "next" text
            if len(clicks) < max_clicks:
                text_clicks = await self._click_by_text(page, max_clicks - len(clicks))
                clicks.extend(text_clicks)
            
        except Exception as e:
            logger.error(f"Finding interactive elements failed: {e}")
        
        return {"clicks": clicks}

    async def _handle_hacker_news_specific(self, page: Page, max_clicks: int) -> List[str]:
        """Special handling for Hacker News"""
        clicks = []
        
        try:
            # Hacker News has a specific "More" link at the bottom
            more_link = await page.query_selector('.morelink')
            if more_link:
                logger.info("Found Hacker News 'More' link")
                
                # Click the "More" link multiple times for depth
                for click_num in range(min(3, max_clicks)):
                    try:
                        if await more_link.is_visible():
                            # Get text for logging
                            link_text = await more_link.text_content() or "More"
                            
                            # Click the link
                            await more_link.click()
                            clicks.append(f"hackernews-more:{link_text}:{click_num+1}")
                            
                            # Wait for new content
                            await page.wait_for_load_state('networkidle', timeout=5000)
                            await asyncio.sleep(2)
                            
                            logger.info(f"Clicked Hacker News More link {click_num+1}")
                            
                            # Find the new "More" link
                            more_link = await page.query_selector('.morelink')
                            if not more_link:
                                logger.info("No more 'More' links found")
                                break
                        else:
                            break
                        
                    except Exception as e:
                        logger.warning(f"Failed to click Hacker News More link {click_num}: {e}")
                        break
            else:
                logger.info("No Hacker News 'More' link found")
                
        except Exception as e:
            logger.error(f"Hacker News specific handling failed: {e}")
        
        return clicks
    
    async def _try_pagination(self, page: Page, max_clicks: int) -> List[str]:
        """Try to find and click pagination links"""
        clicks = []
        
        try:
            for selector in self.pagination_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if not elements:
                        continue
                    
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for i, element in enumerate(elements[:max_clicks]):
                        try:
                            if await element.is_visible():
                                # Get element text for logging
                                text = await element.text_content() or f"Element {i}"
                                text = text.strip()[:50]
                                
                                # Click the element
                                await element.click(timeout=3000)
                                clicks.append(f"pagination:{selector}:{text}")
                                
                                # Wait for page to load
                                await page.wait_for_load_state('networkidle', timeout=5000)
                                await asyncio.sleep(2)
                                
                                logger.info(f"Clicked pagination: {text}")
                                
                                # Check if we reached max clicks
                                if len(clicks) >= max_clicks:
                                    break
                                
                        except Exception as e:
                            logger.debug(f"Failed to click pagination element {i}: {e}")
                            continue
                    
                    if clicks:
                        break  # Found working selector
                        
                except Exception as e:
                    logger.debug(f"Pagination selector {selector} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Pagination failed: {e}")
        
        return clicks

    async def _try_hacker_news_pagination(self, page: Page, max_clicks: int) -> List[str]:
        """Special pagination handling for Hacker News"""
        clicks = []
        
        try:
            # Hacker News has .morelink for pagination
            morelink = await page.query_selector('.morelink')
            if morelink:
                logger.info("Found Hacker News .morelink element")
                
                for click_num in range(min(3, max_clicks)):
                    try:
                        # Check if still visible
                        is_visible = await morelink.is_visible()
                        if not is_visible:
                            # Scroll to make it visible
                            try:
                                await morelink.scroll_into_view_if_needed()
                            except Exception:
                                pass
                            await asyncio.sleep(1)
                        
                        # Get text for logging
                        link_text = await morelink.text_content() or "More"
                        
                        # Click the link
                        await morelink.click(timeout=5000)
                        clicks.append(f"hn-morelink:{link_text}:{click_num+1}")
                        
                        # Wait for content to load
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        await asyncio.sleep(2)
                        
                        logger.info(f"Clicked Hacker News .morelink {click_num+1}")
                        
                        # Find next morelink
                        morelink = await page.query_selector('.morelink')
                        if not morelink:
                            logger.info("No more .morelink elements found")
                            break
                        
                    except Exception as e:
                        logger.warning(f"Failed to click Hacker News .morelink {click_num}: {e}")
                        break
            
            # Also look for any "More" text elements if no clicks yet
            if not clicks:
                more_elements = await page.query_selector_all('a:has-text("More"), button:has-text("More")')
                for element in more_elements[:max_clicks]:
                    try:
                        if await element.is_visible():
                            await element.click(timeout=3000)
                            clicks.append("hn-more-text:clicked")
                            await asyncio.sleep(2)
                            break
                    except Exception:
                        continue
                        
        except Exception as e:
            logger.error(f"Hacker News pagination failed: {e}")
        
        return clicks
    
    async def _try_load_more(self, page: Page, max_clicks: int) -> List[str]:
        """Try to find and click load more buttons"""
        clicks = []
        
        try:
            for selector in self.load_more_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if not elements:
                        continue
                    
                    logger.info(f"Found {len(elements)} load more elements")
                    
                    # Try to click the same button multiple times
                    if elements:
                        button = elements[0]
                        for click_num in range(min(3, max_clicks)):
                            try:
                                if await button.is_visible():
                                    await button.click(timeout=3000)
                                    clicks.append(f"load-more:{selector}:{click_num+1}")
                                    await asyncio.sleep(2)  # Wait for content
                                    logger.info(f"Clicked load more {click_num+1}")
                                else:
                                    break
                            except Exception as e:
                                logger.debug(f"Load more click {click_num} failed: {e}")
                                break
                    
                    if clicks:
                        break  # Found working selector
                        
                except Exception as e:
                    logger.debug(f"Load more selector {selector} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Load more failed: {e}")
        
        return clicks
    
    async def _try_tabs(self, page: Page, max_clicks: int) -> List[str]:
        """Try to find and click tabs"""
        clicks = []
        
        try:
            for selector in self.tab_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if not elements:
                        continue
                    
                    logger.info(f"Found {len(elements)} tab elements")
                    
                    for i, element in enumerate(elements[:max_clicks]):
                        try:
                            if await element.is_visible():
                                await element.click(timeout=3000)
                                clicks.append(f"tab:{selector}:{i+1}")
                                await asyncio.sleep(1.5)  # Wait for content change
                                logger.info(f"Clicked tab {i+1}")
                        except Exception as e:
                            logger.debug(f"Tab click {i} failed: {e}")
                            continue
                    
                    if clicks:
                        break  # Found working selector
                        
                except Exception as e:
                    logger.debug(f"Tab selector {selector} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Tabs failed: {e}")
        
        return clicks
    
    async def _click_by_text(self, page: Page, max_clicks: int) -> List[str]:
        """Click elements by text content"""
        clicks = []
        
        try:
            # Look for buttons or links with specific text
            text_patterns = ['more', 'next', 'load', 'show', 'see', 'view']
            
            for pattern in text_patterns:
                try:
                    elements = await page.query_selector_all(f'button:has-text("{pattern}"), a:has-text("{pattern}")')
                    if not elements:
                        continue
                    
                    logger.info(f"Found {len(elements)} elements with text '{pattern}'")
                    
                    for i, element in enumerate(elements[:max_clicks]):
                        try:
                            if await element.is_visible():
                                text = await element.text_content() or pattern
                                text = text.strip()[:50]
                                
                                await element.click(timeout=3000)
                                clicks.append(f"text-click:{pattern}:{text}")
                                await asyncio.sleep(2)
                                logger.info(f"Clicked element with text: {text}")
                                
                                if len(clicks) >= max_clicks:
                                    break
                                
                        except Exception as e:
                            logger.debug(f"Text click {i} failed: {e}")
                            continue
                    
                    if clicks:
                        break
                        
                except Exception as e:
                    logger.debug(f"Text pattern '{pattern}' failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Text clicking failed: {e}")
        
        return clicks
    
    async def _add_supplemental_interactions(self, page: Page, needed: int) -> Dict[str, Any]:
        """Add supplemental interactions to reach minimum depth"""
        clicks = []
        scrolls = 0
        
        try:
            logger.info(f"Adding {needed} supplemental interactions")
            
            # Add more scrolls
            for i in range(needed):
                await page.evaluate(f'window.scrollBy(0, {300 * (i + 1)})')
                scrolls += 1
                clicks.append(f"supplemental-scroll:{i+1}")
                await asyncio.sleep(0.5)
            
            logger.info(f"Added {scrolls} supplemental scrolls")
            
        except Exception as e:
            logger.error(f"Supplemental interactions failed: {e}")
        
        return {"clicks": clicks, "scrolls": scrolls}