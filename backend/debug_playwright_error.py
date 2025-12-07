"""
Debug why Playwright is returning empty interactions
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def debug_playwright():
    """Test Playwright directly to see what's happening"""
    print("Testing Playwright scraper directly...")
    
    from app.scraper.playwright_scraper import PlaywrightScraper
    
    scraper = PlaywrightScraper(headless=True)
    
    try:
        print("Scraping Hacker News...")
        result = await scraper.scrape('https://news.ycombinator.com/')
        
        print(f"\nResult status: {hasattr(result, 'sections')}")
        print(f"Sections found: {len(result.sections) if result.sections else 0}")
        print(f"Errors: {len(result.errors) if result.errors else 0}")
        
        if result.errors:
            for error in result.errors:
                print(f"Error: {error.message} (phase: {error.phase})")
        
        print(f"\nInteractions:")
        print(f"  Clicks: {len(result.interactions.clicks)}")
        print(f"  Scrolls: {result.interactions.scrolls}")
        print(f"  Pages: {len(result.interactions.pages)}")
        
        if result.interactions.clicks:
            print("Click actions:")
            for i, click in enumerate(result.interactions.clicks[:5]):
                print(f"  {i+1}. {click}")
                
    except Exception as e:
        print(f"Exception during scraping: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("="*60)
    print("DEBUG PLAYWRIGHT ERROR")
    print("="*60)
    
    await debug_playwright()

if __name__ == "__main__":
    asyncio.run(main())