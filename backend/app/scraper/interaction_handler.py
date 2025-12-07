"""
Enhanced interaction handler for click flows and scroll tracking
"""
import asyncio
from typing import List, Dict, Any, Set, Tuple
import logging
from playwright.async_api import Page, ElementHandle, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class InteractionHandler:
    """Handles interactive scraping with depth tracking"""
    
    def __init__(self, max_depth: int = 3, timeout: int = 30000):
        self.max_depth = max_depth
        self.timeout = timeout
        
        # Enhanced selectors for interactions
        self.tab_selectors = [
            '[role="tab"]',
            '[role="tablist"] [role="button"]',
            '.tab-button',
            '.tab-item',
            'button[aria-controls]',
            'nav a[role="tab"]',
            '.tabs button',
            '.tab-nav button',
            '[class*="tab"][role="button"]'
        ]
        
        self.load_more_selectors = [
            'button:has-text("Load more")',
            'button:has-text("Show more")',
            'button:has-text("See more")',
            'button:has-text("View more")',
            'button:has-text("Load")',
            'button:has-text("Show")',
            'a:has-text("Load more")',
            'a:has-text("Show more")',
            '[class*="load-more"]',
            '[class*="show-more"]',
            '#load-more',
            '#show-more',
            '.load-more',
            '.show-more',
            '[data-load-more]',
            '[data-action="load-more"]'
        ]
        
        self.pagination_selectors = [
            'a:has-text("Next")',
            'a:has-text("Next page")',
            'a:has-text("›")',
            'a:has-text("»")',
            'a[rel="next"]',
            '[class*="next"]',
            '[class*="pagination-next"]',
            'button:has-text("Next")',
            '.next-page',
            '.pagination-next',
            '[aria-label="Next page"]',
            '[title="Next page"]'
        ]
        
        self.infinite_scroll_selectors = [
            '[class*="infinite-scroll"]',
            '[class*="scroll-load"]',
            '[data-infinite-scroll]',
            '[data-scroll-load]'
        ]
        
        # Content indicators to check for new content
        self.content_indicators = [
            'article',
            '.post',
            '.item',
            '.card',
            '.product',
            '.entry',
            '[class*="content"]',
            '[class*="item"]',
            '[class*="card"]',
            '[class*="post"]'
        ]
    
    async def handle_interactive_scraping(
        self, 
        page: Page, 
        visited_pages: List[str],
        max_depth: int = None
    ) -> Tuple[List[str], List[str], int]:
        """
        Perform all interactive scraping actions
        
        Returns:
            Tuple of (clicks, pages, scrolls)
        """
        if max_depth is None:
            max_depth = self.max_depth
        
        clicks = []
        scrolls = 0
        all_pages = visited_pages.copy()
        
        try:
            # 1. Handle tabs (depth = number of tabs clicked)
            tab_clicks = await self._handle_tabs_with_depth(page, max_depth)
            clicks.extend(tab_clicks)
            
            # 2. Handle load more buttons (depth = number of clicks)
            load_more_clicks = await self._handle_load_more_with_depth(page, max_depth)
            clicks.extend(load_more_clicks)
            
            # 3. Handle pagination (depth = number of pages)
            pagination_data = await self._handle_pagination_with_depth(page, max_depth, all_pages)
            clicks.extend(pagination_data['clicks'])
            all_pages = pagination_data['pages']
            
            # 4. Handle infinite scroll (depth = number of scrolls)
            scrolls_result = await self._handle_infinite_scroll_with_depth(page, max_depth)
            scrolls = scrolls_result['scrolls']
            clicks.extend(scrolls_result['clicks'])
            
            # 5. Additional interaction: Expand/collapse elements
            expand_clicks = await self._handle_expandable_elements(page)
            clicks.extend(expand_clicks)
            
            # Ensure we have at least depth 3
            total_interactions = len(clicks) + scrolls
            if total_interactions < 3:
                logger.info(f"Only {total_interactions} interactions, attempting more...")
                await self._ensure_minimum_depth(page, clicks, scrolls, max_depth)
            
        except Exception as e:
            logger.error(f"Interactive scraping failed: {e}")
        
        return clicks, all_pages, scrolls
    
    async def _handle_tabs_with_depth(self, page: Page, max_depth: int) -> List[str]:
        """Click tabs with depth tracking"""
        clicks = []
        
        try:
            for selector in self.tab_selectors:
                try:
                    tabs = await page.query_selector_all(selector)
                    if not tabs:
                        continue
                    
                    logger.info(f"Found {len(tabs)} tabs with selector: {selector}")
                    
                    # Click tabs up to max_depth
                    tabs_clicked = 0
                    for i, tab in enumerate(tabs):
                        if tabs_clicked >= max_depth:
                            break
                        
                        try:
                            # Check if tab is clickable
                            is_visible = await tab.is_visible()
                            is_enabled = await tab.is_enabled()
                            
                            if is_visible and is_enabled:
                                # Get tab text for recording
                                tab_text = await tab.text_content() or f"Tab {i}"
                                
                                # Click the tab
                                await tab.click()
                                await page.wait_for_timeout(1500)  # Wait for content to load
                                
                                # Check if new content appeared
                                content_changed = await self._check_content_change(page)
                                if content_changed:
                                    clicks.append(f"tab:{tab_text}:{selector}")
                                    tabs_clicked += 1
                                    logger.info(f"Clicked tab: {tab_text} (depth: {tabs_clicked})")
                                else:
                                    logger.info(f"Tab click didn't reveal new content: {tab_text}")
                                
                                # Wait a bit between clicks
                                await page.wait_for_timeout(500)
                                
                        except Exception as e:
                            logger.warning(f"Failed to click tab {i}: {e}")
                            continue
                    
                    if tabs_clicked > 0:
                        break  # Found working selector
                        
                except Exception as e:
                    logger.warning(f"Tab selector {selector} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Tab handling failed: {e}")
        
        return clicks
    
    async def _handle_load_more_with_depth(self, page: Page, max_depth: int) -> List[str]:
        """Click load more buttons with depth tracking"""
        clicks = []
        
        try:
            # First, check if we're on an infinite scroll page
            has_infinite_scroll = await self._detect_infinite_scroll(page)
            if has_infinite_scroll:
                logger.info("Page has infinite scroll, will handle separately")
                return clicks
            
            for selector in self.load_more_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    if not buttons:
                        continue
                    
                    logger.info(f"Found {len(buttons)} load more buttons with selector: {selector}")
                    
                    # Find the most likely load more button (usually only one)
                    load_more_button = None
                    for button in buttons:
                        text = await button.text_content() or ""
                        if any(keyword in text.lower() for keyword in ['load', 'show', 'see', 'more']):
                            load_more_button = button
                            break
                    
                    if not load_more_button and buttons:
                        load_more_button = buttons[0]
                    
                    if load_more_button:
                        # Click load more up to max_depth times
                        for depth in range(max_depth):
                            try:
                                # Check if button is still visible and enabled
                                is_visible = await load_more_button.is_visible()
                                is_enabled = await load_more_button.is_enabled()
                                
                                if not (is_visible and is_enabled):
                                    logger.info("Load more button no longer available")
                                    break
                                
                                # Scroll to button
                                await load_more_button.scroll_into_view_if_needed()
                                await page.wait_for_timeout(1000)
                                
                                # Get button text
                                button_text = await load_more_button.text_content() or f"Load More {depth+1}"
                                
                                # Take screenshot of current content
                                before_content = await self._get_content_hash(page)
                                
                                # Click the button
                                await load_more_button.click()
                                
                                # Wait for content to load (with dynamic timeout)
                                await self._wait_for_new_content(page, timeout=5000)
                                
                                # Check if new content loaded
                                after_content = await self._get_content_hash(page)
                                content_changed = before_content != after_content
                                
                                if content_changed:
                                    clicks.append(f"load-more:{button_text}:{depth+1}")
                                    logger.info(f"Clicked load more (depth: {depth+1}): {button_text}")
                                    
                                    # Wait for content to settle
                                    await page.wait_for_timeout(2000)
                                else:
                                    logger.info("Load more didn't reveal new content, stopping")
                                    break
                                
                            except Exception as e:
                                logger.warning(f"Failed to click load more at depth {depth}: {e}")
                                break
                        
                        break  # Found working selector
                        
                except Exception as e:
                    logger.warning(f"Load more selector {selector} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Load more handling failed: {e}")
        
        return clicks
    
    async def _handle_pagination_with_depth(
        self, 
        page: Page, 
        max_depth: int, 
        visited_pages: List[str]
    ) -> Dict[str, Any]:
        """Follow pagination links with depth tracking"""
        clicks = []
        pages = visited_pages.copy()
        
        try:
            for selector in self.pagination_selectors:
                try:
                    next_links = await page.query_selector_all(selector)
                    if not next_links:
                        continue
                    
                    logger.info(f"Found {len(next_links)} pagination links with selector: {selector}")
                    
                    # Follow pagination up to max_depth pages
                    for depth in range(max_depth):
                        try:
                            # Find the next link
                            next_link = None
                            link_text = ""
                            
                            for link in next_links:
                                text = await link.text_content() or ""
                                if any(keyword in text.lower() for keyword in ['next', '›', '»', '>']):
                                    next_link = link
                                    link_text = text.strip()
                                    break
                            
                            if not next_link and next_links:
                                next_link = next_links[0]
                                link_text = await next_link.text_content() or ""
                                link_text = link_text.strip()
                            
                            if not next_link:
                                logger.info("No more pagination links")
                                break
                            
                            # Get URL before clicking
                            href = await next_link.get_attribute('href')
                            if not href:
                                logger.info("Pagination link has no href")
                                break
                            
                            # Click and navigate
                            await next_link.click()
                            await page.wait_for_load_state('networkidle')
                            await page.wait_for_timeout(2000)  # Wait for content
                            
                            # Get new page URL
                            current_url = page.url
                            if current_url not in pages:
                                pages.append(current_url)
                            
                            clicks.append(f"pagination:{link_text}:{depth+1}")
                            logger.info(f"Followed pagination to page {depth+2}: {current_url}")
                            
                            # Find next links on new page
                            next_links = await page.query_selector_all(selector)
                            
                            # Ensure we're not in a loop
                            if len(pages) > 1 and pages[-1] == pages[-2]:
                                logger.info("Detected pagination loop, stopping")
                                break
                            
                        except Exception as e:
                            logger.warning(f"Failed pagination step {depth}: {e}")
                            break
                    
                    break  # Found working selector
                    
                except Exception as e:
                    logger.warning(f"Pagination selector {selector} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Pagination handling failed: {e}")
        
        return {"clicks": clicks, "pages": pages}
    
    async def _handle_infinite_scroll_with_depth(self, page: Page, max_depth: int) -> Dict[str, Any]:
        """Handle infinite scroll with depth tracking"""
        clicks = []
        scrolls = 0
        
        try:
            # Check if page supports infinite scroll
            has_infinite_scroll = await self._detect_infinite_scroll(page)
            
            if has_infinite_scroll:
                logger.info("Detected infinite scroll, starting scroll sequence")
                
                # Take initial measurements
                prev_height = await page.evaluate('document.body.scrollHeight')
                prev_content = await self._get_content_hash(page)
                
                for depth in range(max_depth):
                    try:
                        # Scroll to bottom
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        
                        # Wait for potential content load
                        await page.wait_for_timeout(3000)
                        
                        # Check for new content
                        new_height = await page.evaluate('document.body.scrollHeight')
                        new_content = await self._get_content_hash(page)
                        
                        if new_height > prev_height or new_content != prev_content:
                            scrolls += 1
                            clicks.append(f"infinite-scroll:scroll:{depth+1}")
                            logger.info(f"Scroll {depth+1}: New content detected (height: {prev_height} → {new_height})")
                            
                            prev_height = new_height
                            prev_content = new_content
                            
                            # Wait for content to settle
                            await page.wait_for_timeout(2000)
                            
                            # Check for load more buttons that might appear after scroll
                            for selector in self.load_more_selectors:
                                try:
                                    buttons = await page.query_selector_all(selector)
                                    if buttons:
                                        button = buttons[0]
                                        if await button.is_visible() and await button.is_enabled():
                                            await button.click()
                                            await page.wait_for_timeout(2000)
                                            clicks.append(f"infinite-scroll:load-more:{depth+1}")
                                            logger.info(f"Clicked load more after scroll {depth+1}")
                                            break
                                except:
                                    continue
                        else:
                            logger.info(f"Scroll {depth+1}: No new content, stopping")
                            break
                            
                    except Exception as e:
                        logger.warning(f"Failed scroll {depth}: {e}")
                        break
                
                # Scroll back to top for consistent results
                await page.evaluate('window.scrollTo(0, 0)')
                await page.wait_for_timeout(1000)
                
        except Exception as e:
            logger.error(f"Infinite scroll handling failed: {e}")
        
        return {"clicks": clicks, "scrolls": scrolls}
    
    async def _handle_expandable_elements(self, page: Page) -> List[str]:
        """Handle expand/collapse elements (FAQ, accordions, etc.)"""
        clicks = []
        
        try:
            # Common expandable element selectors
            expand_selectors = [
                '[aria-expanded="false"]',
                '.accordion-button:not([aria-expanded="true"])',
                '.faq-question',
                '.expand-button',
                '[class*="expand"]',
                '[class*="accordion"] button',
                'summary',  # HTML5 details/summary
                '[role="button"][aria-controls]'
            ]
            
            for selector in expand_selectors:
                try:
                    expand_buttons = await page.query_selector_all(selector)
                    if not expand_buttons:
                        continue
                    
                    logger.info(f"Found {len(expand_buttons)} expandable elements with selector: {selector}")
                    
                    # Click up to 3 expandable elements
                    for i, button in enumerate(expand_buttons[:3]):
                        try:
                            if await button.is_visible() and await button.is_enabled():
                                # Get button text
                                button_text = await button.text_content() or f"Expand {i}"
                                
                                # Click to expand
                                await button.click()
                                await page.wait_for_timeout(1000)
                                
                                clicks.append(f"expand:{button_text}:{selector}")
                                logger.info(f"Expanded element: {button_text}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to expand element {i}: {e}")
                            continue
                    
                    break  # Found working selector
                    
                except Exception as e:
                    logger.warning(f"Expand selector {selector} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Expandable elements handling failed: {e}")
        
        return clicks
    
    async def _ensure_minimum_depth(
        self, 
        page: Page, 
        clicks: List[str], 
        scrolls: int, 
        min_depth: int = 3
    ):
        """Ensure we reach minimum interaction depth"""
        total = len(clicks) + scrolls
        
        if total >= min_depth:
            return
        
        logger.info(f"Current depth {total} < {min_depth}, attempting additional interactions")
        
        try:
            # Try to scroll more
            while total < min_depth and scrolls < min_depth:
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await page.wait_for_timeout(2000)
                scrolls += 1
                total += 1
                clicks.append(f"supplemental:scroll:{scrolls}")
                logger.info(f"Supplemental scroll {scrolls} for minimum depth")
            
            # Try to find and click any button
            if total < min_depth:
                buttons = await page.query_selector_all('button, a[role="button"]')
                for i, button in enumerate(buttons[:min_depth - total]):
                    try:
                        if await button.is_visible() and await button.is_enabled():
                            await button.click()
                            await page.wait_for_timeout(1000)
                            clicks.append(f"supplemental:button:{i+1}")
                            total += 1
                            logger.info(f"Supplemental button click {i+1} for minimum depth")
                    except:
                        continue
            
            logger.info(f"Final interaction depth: {total}")
            
        except Exception as e:
            logger.warning(f"Failed to ensure minimum depth: {e}")
    
    async def _check_content_change(self, page: Page) -> bool:
        """Check if content changed after interaction"""
        try:
            # Simple check: look for new elements with content indicators
            for selector in self.content_indicators:
                count = await page.query_selector_all(selector)
                if len(count) > 0:
                    return True
            return False
        except:
            return False
    
    async def _get_content_hash(self, page: Page) -> str:
        """Create a simple hash of page content for comparison"""
        try:
            content = await page.evaluate('''
                () => {
                    const elements = document.querySelectorAll('article, .post, .item, .card, [class*="content"]');
                    let text = '';
                    elements.forEach(el => text += el.textContent);
                    return text.length.toString() + '-' + elements.length.toString();
                }
            ''')
            return content
        except:
            return "error"
    
    async def _detect_infinite_scroll(self, page: Page) -> bool:
        """Detect if page uses infinite scroll"""
        try:
            # Check for infinite scroll indicators
            for selector in self.infinite_scroll_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    return True
            
            # Check for scroll event listeners
            has_scroll_listeners = await page.evaluate('''
                () => {
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        const listeners = getEventListeners(el);
                        if (listeners && listeners.scroll) {
                            return true;
                        }
                    }
                    return false;
                }
            ''')
            
            return has_scroll_listeners
            
        except:
            return False
    
    async def _wait_for_new_content(self, page: Page, timeout: int = 5000):
        """Wait for new content to load"""
        try:
            start_time = asyncio.get_event_loop().time()
            initial_content = await self._get_content_hash(page)
            
            while asyncio.get_event_loop().time() - start_time < timeout / 1000:
                await page.wait_for_timeout(500)
                current_content = await self._get_content_hash(page)
                if current_content != initial_content:
                    return True
            
            return False
        except:
            return False