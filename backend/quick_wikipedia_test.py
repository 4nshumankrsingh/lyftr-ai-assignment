"""
Quick test to debug Wikipedia
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import re

async def test_wikipedia():
    url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        
        print("=== CHECKING WIKIPEDIA STRUCTURE ===")
        
        # Check for main content
        main_content = soup.find('div', id='mw-content-text')
        if main_content:
            print("✅ Found mw-content-text div!")
            
            # Get all child divs
            child_divs = main_content.find_all('div', recursive=False)
            print(f"Found {len(child_divs)} direct child divs")
            
            # Get all paragraphs
            paragraphs = main_content.find_all('p')
            print(f"Found {len(paragraphs)} paragraphs total")
            
            # Check first 5 paragraphs
            for i, p in enumerate(paragraphs[:5]):
                text = p.get_text(strip=True)
                if text:
                    print(f"\nParagraph {i+1} ({len(text)} chars):")
                    # Clean and show first 100 chars
                    clean = re.sub(r'\[\d+\]', '', text)
                    print(clean[:100] + "...")
        else:
            print("❌ No mw-content-text div found!")
            
            # Alternative: look for main content
            main_tag = soup.find('main')
            if main_tag:
                print("Found <main> tag instead")
            else:
                print("Checking for #content")
                content_div = soup.find('div', id='content')
                if content_div:
                    print("Found #content div")
            
        print("\n=== CHECKING WHAT YOUR STATIC SCRAPER SEES ===")
        
        # Simulate what your scraper does
        from app.scraper.static_scraper import StaticScraper
        scraper = StaticScraper()
        scraper.url = url
        scraper.base_url = scraper._get_base_url(url)
        
        sections = scraper._extract_sections(soup)
        print(f"Sections found: {len(sections)}")
        
        for i, section in enumerate(sections):
            print(f"\nSection {i+1}:")
            print(f"  ID: {section.id}")
            print(f"  Type: {section.type}")
            print(f"  Label: {section.label[:50]}...")
            print(f"  Has text: {bool(section.content.text)}")
            print(f"  Text length: {len(section.content.text)}")
            if section.content.text:
                print(f"  Text sample: {section.content.text[:100]}...")

asyncio.run(test_wikipedia())