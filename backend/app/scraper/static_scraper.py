"""
Enhanced static scraper for Lyftr AI assignment
Implements metadata extraction, section parsing, and content cleaning
"""
import httpx
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Any
import logging

from .base_scraper import BaseScraper
from ..models.schemas import ScrapeResult, Meta, Section, Content, Link, Image, Interaction, Error, SectionType

logger = logging.getLogger(__name__)

class StaticScraper(BaseScraper):
    """Static HTML scraper with enhanced content extraction"""
    
    def __init__(self):
        super().__init__()
        self.sections: List[Section] = []
        
        # Noise selectors - common elements to filter out
        self.noise_selectors = [
            'script', 'style', 'noscript', 'iframe',
            '[class*="cookie"]', '[class*="banner"]', '[class*="popup"]',
            '[class*="modal"]', '[class*="advertisement"]', '[class*="ad-"]',
            '[id*="cookie"]', '[id*="banner"]', '[id*="popup"]',
            '[role="alert"]', '[aria-label*="cookie"]'
        ]
        
        # Section type mapping
        self.section_type_map = {
            'header': SectionType.NAV,
            'nav': SectionType.NAV,
            'main': SectionType.SECTION,
            'footer': SectionType.FOOTER,
            'aside': SectionType.SECTION,
            'article': SectionType.SECTION,
            'section': SectionType.SECTION
        }
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Main scraping method"""
        self.url = url
        self.base_url = self._get_base_url(url)
        self.errors = []
        
        try:
            # Fetch HTML
            html_content = await self._fetch_html(url)
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove noise elements
            self._remove_noise(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            # Extract sections
            sections = self._extract_sections(soup)
            
            return ScrapeResult(
                url=url,
                scrapedAt=datetime.utcnow().isoformat() + "Z",
                meta=Meta(**metadata),
                sections=sections,
                interactions=Interaction(
                    clicks=[],
                    scrolls=0,
                    pages=[url]
                ),
                errors=[Error(message=e["message"], phase=e["phase"]) for e in self.errors]
            )
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            self.add_error(str(e), "scraping")
            return ScrapeResult(
                url=url,
                scrapedAt=datetime.utcnow().isoformat() + "Z",
                meta=Meta(),
                sections=[],
                interactions=Interaction(
                    clicks=[],
                    scrolls=0,
                    pages=[url]
                ),
                errors=[Error(message=str(e), phase="scraping")]
            )
    
    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.reason_phrase}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to fetch HTML: {str(e)}")
    
    def _remove_noise(self, soup: BeautifulSoup) -> None:
        """Remove noise elements like ads, banners, popups"""
        for selector in self.noise_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except Exception as e:
                self.add_error(f"Failed to remove noise selector {selector}: {str(e)}", "parsing")
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata"""
        metadata = {
            "title": "",
            "description": "",
            "language": "en",
            "canonical": None
        }
        
        try:
            # Title
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                metadata["title"] = og_title['content'].strip()
            elif soup.title and soup.title.string:
                metadata["title"] = soup.title.string.strip()
            
            # Description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            og_desc = soup.find('meta', property='og:description')
            twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
            
            if og_desc and og_desc.get('content'):
                metadata["description"] = og_desc['content'].strip()
            elif twitter_desc and twitter_desc.get('content'):
                metadata["description"] = twitter_desc['content'].strip()
            elif meta_desc and meta_desc.get('content'):
                metadata["description"] = meta_desc['content'].strip()
            
            # Language
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                metadata["language"] = html_tag['lang'].split('-')[0]
            
            # Canonical URL
            canonical = soup.find('link', rel='canonical')
            if canonical and canonical.get('href'):
                metadata["canonical"] = self._make_absolute_url(canonical['href'])
            
        except Exception as e:
            self.add_error(f"Metadata extraction error: {str(e)}", "parsing")
        
        return metadata
    
    def _extract_sections(self, soup: BeautifulSoup) -> List[Section]:
        """Extract sections from HTML"""
        sections = []
        
        try:
            # SPECIAL HANDLING FOR WIKIPEDIA
            parsed_url = urlparse(self.url)
            if 'wikipedia.org' in parsed_url.netloc:
                wikipedia_sections = self._extract_wikipedia_specific(soup)
                if wikipedia_sections:
                    return wikipedia_sections

            # First try to find semantic landmarks
            landmarks = ['header', 'nav', 'main', 'footer', 'aside', 'article', 'section']
            
            for landmark in landmarks:
                elements = soup.find_all(landmark)
                for element in elements:
                    section = self._create_section_from_element(element, landmark)
                    if section:
                        sections.append(section)
            
            # If no landmarks found, create sections from headings
            if not sections:
                sections = self._create_sections_from_headings(soup)
            
            # Ensure we have at least one section
            if not sections:
                sections = [self._create_fallback_section(soup)]
            
        except Exception as e:
            self.add_error(f"Section extraction error: {str(e)}", "parsing")
            sections = [self._create_fallback_section(soup)]
        
        return sections
    
    def _create_section_from_element(self, element: Tag, tag_name: str) -> Optional[Section]:
        """Create a section from a semantic HTML element - SKIP NAVIGATION"""
        try:
            # SKIP NAVIGATION ELEMENTS for Wikipedia
            element_text = element.get_text(strip=True).lower()
            element_str = str(element).lower()

            # Skip navigation/menu/sidebar elements
            skip_keywords = ['menu', 'navigation', 'sidebar', 'toc', 'table of contents', 'nav']
            for keyword in skip_keywords:
                if keyword in element_text or keyword in element_str:
                    logger.debug(f"Skipping {tag_name} element with keyword: {keyword}")
                    return None

            # Skip elements that are too small (likely navigation links)
            if len(element_text) < 50 and 'href' in element_str:
                logger.debug(f"Skipping small link element: {element_text[:30]}...")
                return None

            # Get section type
            section_type = self._determine_section_type(element, tag_name)

            # Generate ID
            section_id = f"{tag_name}-{len(element.find_parents())}"

            # Get label from heading or generate from content
            label = self._extract_section_label(element)

            # Extract content as dict
            content_dict = self._extract_content(element)

            # Convert to Content model
            content = Content(
                headings=content_dict.get("headings", []),
                text=content_dict.get("text", ""),
                links=[Link(**link) for link in content_dict.get("links", [])],
                images=[Image(**img) for img in content_dict.get("images", [])],
                lists=content_dict.get("lists", []),
                tables=content_dict.get("tables", [])
            )

            # Get raw HTML (truncated)
            raw_html = str(element)
            truncated = False
            if len(raw_html) > 2000:
                raw_html = raw_html[:2000] + "..."
                truncated = True

            return Section(
                id=section_id,
                type=section_type,
                label=label,
                sourceUrl=self.url,
                content=content,
                rawHtml=raw_html,
                truncated=truncated
            )

        except Exception as e:
            logger.debug(f"Skipping section creation: {e}")
            return None
    
    def _determine_section_type(self, element: Tag, tag_name: str) -> SectionType:
        """Determine section type based on element"""
        # Check for specific classes
        element_classes = element.get('class', [])
        element_id = element.get('id', '').lower()
        element_str = str(element).lower()
        
        if 'hero' in element_str or any('hero' in cls.lower() for cls in element_classes) or 'hero' in element_id:
            return SectionType.HERO
        elif 'pricing' in element_str or any('pricing' in cls.lower() for cls in element_classes) or 'pricing' in element_id:
            return SectionType.PRICING
        elif 'faq' in element_str or any('faq' in cls.lower() for cls in element_classes) or 'faq' in element_id:
            return SectionType.FAQ
        elif 'grid' in element_str or any('grid' in cls.lower() for cls in element_classes) or 'grid' in element_id:
            return SectionType.GRID
        elif 'list' in element_str or any('list' in cls.lower() for cls in element_classes) or 'list' in element_id:
            return SectionType.LIST
        elif tag_name == 'nav':
            return SectionType.NAV
        elif tag_name == 'footer':
            return SectionType.FOOTER
        else:
            return self.section_type_map.get(tag_name, SectionType.SECTION)
    
    def _extract_section_label(self, element: Tag) -> str:
        """Extract or generate section label"""
        # Try to find a heading within the section
        headings = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headings:
            return headings[0].get_text(strip=True)
        
        # Try to find aria-label or title
        aria_label = element.get('aria-label')
        if aria_label:
            return aria_label.strip()
        
        title = element.get('title')
        if title:
            return title.strip()
        
        # Generate from first few words of content
        text = element.get_text(strip=True)
        if text:
            words = text.split()[:7]
            return ' '.join(words) + '...'
        
        return "Unlabeled Section"
    
    def _extract_content(self, element: Tag) -> Dict[str, Any]:
        """Extract content from element - FIXED FOR WIKIPEDIA"""
        content = {
            "headings": [],
            "text": "",
            "links": [],
            "images": [],
            "lists": [],
            "tables": []
        }
        
        try:
            # Extract headings
            headings = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content["headings"] = [h.get_text(strip=True) for h in headings if h.get_text(strip=True)]
            
            # For Wikipedia, look for the main content div
            # Wikipedia has <div id="mw-content-text"> for main content
            main_content = element.find('div', id='mw-content-text')
            if main_content:
                element = main_content
            
            # Create a clean copy for text extraction
            element_copy = element.copy()
            
            # Remove all unwanted elements
            for tag in element_copy.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                                              'table', 'form', 'button', 'input', 'select']):
                tag.decompose()
            
            # Get all paragraph text
            paragraphs = element_copy.find_all('p')
            if paragraphs:
                para_texts = []
                for p in paragraphs[:8]:  # Check first 8 paragraphs
                    p_text = p.get_text(strip=True)
                    # Filter: at least 20 chars, not just links/navigation
                    if p_text and len(p_text) > 20:
                        # Clean Wikipedia citations [1], [2], etc.
                        clean_text = re.sub(r'\[\d+\]', '', p_text)
                        # Remove extra whitespace
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        if clean_text:
                            para_texts.append(clean_text)
                
                if para_texts:
                    # Join meaningful paragraphs
                    combined_text = ' '.join(para_texts[:5])  # First 5 meaningful paragraphs
                    if len(combined_text) > 500:
                        content["text"] = combined_text[:500] + '...'
                    else:
                        content["text"] = combined_text
            
            # If no paragraphs or text is too short, try general text extraction
            if not content["text"] or len(content["text"]) < 50:
                text = element_copy.get_text(separator=' ', strip=True)
                if text:
                    # Clean the text
                    text = re.sub(r'\s+', ' ', text)
                    text = re.sub(r'\[\d+\]', '', text)
                    words = text.split()
                    if len(words) > 30:
                        content["text"] = ' '.join(words[:150]) + '...'
                    else:
                        content["text"] = text
            
            # Extract links (simplified)
            links = element.find_all('a', href=True)
            for link in links[:10]:
                try:
                    link_text = link.get_text(strip=True)
                    if link_text and len(link_text) < 100:
                        href = link['href']
                        if href and not href.startswith(('#', 'javascript:')):
                            absolute_url = self._make_absolute_url(href) if hasattr(self, '_make_absolute_url') else href
                            content["links"].append({
                                "text": link_text[:50],
                                "href": absolute_url
                            })
                except:
                    continue
            
            # Extract images
            images = element.find_all('img', src=True)
            for img in images[:5]:
                try:
                    src = img['src']
                    if src and not src.startswith('data:'):
                        absolute_src = self._make_absolute_url(src) if hasattr(self, '_make_absolute_url') else src
                        content["images"].append({
                            "src": absolute_src,
                            "alt": img.get('alt', '')[:50]
                        })
                except:
                    continue
            
            # Extract lists
            lists = element.find_all(['ul', 'ol'])
            for lst in lists[:3]:
                try:
                    list_items = []
                    for li in lst.find_all('li')[:10]:
                        item_text = li.get_text(strip=True)
                        if item_text:
                            list_items.append(item_text[:100])
                    if list_items:
                        content["lists"].append(list_items)
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Content extraction error in _extract_content: {e}")
            # Don't fail, return empty content
        
        return content
    
    def _create_sections_from_headings(self, soup: BeautifulSoup) -> List[Section]:
        """Create sections based on headings"""
        sections = []
        current_section = None
        
        try:
            # Find all heading elements
            headings = soup.find_all(['h1', 'h2', 'h3'])
            
            for heading in headings:
                # Create section for each heading
                section_element = heading.find_parent(['div', 'section', 'article', 'main']) or heading
                section = self._create_section_from_element(section_element, 'section')
                if section:
                    sections.append(section)
            
        except Exception as e:
            self.add_error(f"Heading section creation error: {str(e)}", "parsing")
        
        return sections

    def _extract_wikipedia_specific(self, soup: BeautifulSoup) -> List[Section]:
        """Special handling for Wikipedia pages"""
        sections: List[Section] = []
        try:
            # Wikipedia main content container
            content_div = soup.find('div', id='mw-content-text')
            if content_div:
                # Extract paragraphs from main content
                paragraphs = content_div.find_all('p')
                if paragraphs:
                    para_texts = []
                    for p in paragraphs[:10]:
                        text = p.get_text(strip=True)
                        if text and len(text) > 50:
                            # Clean citations and trim
                            clean = re.sub(r'\[\d+\]', '', text)
                            clean = re.sub(r'\s+', ' ', clean).strip()
                            para_texts.append(clean[:500])

                    if para_texts:
                        # Create a single main content section
                        main_section = Section(
                            id="wikipedia-main-0",
                            type=SectionType.SECTION,
                            label="Main Content",
                            sourceUrl=self.url,
                            content=Content(
                                text=' '.join(para_texts[:3]) + '...',
                                links=[],
                                images=[],
                                lists=[],
                                tables=[]
                            ),
                            rawHtml=str(content_div)[:2000] + "...",
                            truncated=True
                        )
                        return [main_section]
        except Exception:
            pass

        return sections
    
    def _create_fallback_section(self, soup: BeautifulSoup) -> Section:
        """Create a fallback section when no sections are found"""
        try:
            # Use body or first div as fallback
            body = soup.find('body') or soup.find('div') or soup
            text = body.get_text(strip=True)
            truncated_text = ' '.join(text.split()[:100]) + '...' if len(text.split()) > 100 else text
            
            return Section(
                id="fallback-0",
                type=SectionType.SECTION,
                label="Main Content",
                sourceUrl=self.url,
                content=Content(
                    text=truncated_text
                ),
                rawHtml=str(body)[:2000] + "..." if len(str(body)) > 2000 else str(body),
                truncated=len(str(body)) > 2000
            )
        except:
            return Section(
                id="error-0",
                type=SectionType.UNKNOWN,
                label="Error - No Content Found",
                sourceUrl=self.url,
                content=Content(),
                rawHtml="<div>No content could be extracted</div>",
                truncated=False
            )