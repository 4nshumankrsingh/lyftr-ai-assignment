"""
Debug Vercel JS rendering issue
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)

async def debug_vercel():
    """Test Vercel scraping directly"""
    print("="*60)
    print("DEBUG VERCEl JS RENDERING")
    print("="*60)
    
    try:
        # Test fallback strategy
        from app.scraper.fallback_strategy import FallbackStrategy
        
        strategy = FallbackStrategy()
        
        print("Testing Vercel (https://vercel.com/) with fallback strategy...")
        
        try:
            strategy_used, result = await strategy.scrape_with_fallback("https://vercel.com/")
            print(f"\nStrategy used: {strategy_used}")
            print(f"Result keys: {list(result.keys())}")
            
            sections = result.get('sections', [])
            print(f"Sections found: {len(sections)}")
            
            if sections:
                print(f"First section type: {sections[0].get('type')}")
                print(f"First section label: {sections[0].get('label')}")
            
            interactions = result.get('interactions', {})
            print(f"Interactions: {len(interactions.get('clicks', []))} clicks, {interactions.get('scrolls', 0)} scrolls")
            
            errors = result.get('errors', [])
            if errors:
                print(f"Errors: {errors}")
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()

async def test_playwright_directly():
    """Test Playwright scraper directly on Vercel"""
    print("\n" + "="*60)
    print("TESTING PLAYWRIGHT DIRECTLY ON VERCEl")
    print("="*60)
    
    try:
        from app.scraper.playwright_scraper import PlaywrightScraper
        
        scraper = PlaywrightScraper(headless=True)
        
        print("Running Playwright scraper directly on Vercel...")
        result = await scraper.scrape("https://vercel.com/")
        
        print(f"\nSections found: {len(result.sections)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.errors:
            for error in result.errors:
                print(f"  - {error.message} (phase: {error.phase})")
        
        print(f"Interactions: {len(result.interactions.clicks)} clicks, {result.interactions.scrolls} scrolls")
        
    except Exception as e:
        print(f"Playwright test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_static_on_vercel():
    """Test static scraper on Vercel to see what it gets"""
    print("\n" + "="*60)
    print("TESTING STATIC SCRAPER ON VERCEl")
    print("="*60)
    
    try:
        from app.scraper.static_scraper import StaticScraper
        
        scraper = StaticScraper()
        
        print("Running static scraper on Vercel...")
        result = await scraper.scrape("https://vercel.com/")
        
        print(f"\nSections found: {len(result.sections)}")
        
        if result.sections:
            for i, section in enumerate(result.sections[:3]):
                print(f"Section {i+1}: {section.type} - {section.label[:50]}...")
                print(f"  Text length: {len(section.content.text)} chars")
        
        print(f"Meta title: {result.meta.title}")
        
    except Exception as e:
        print(f"Static test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("This will test Vercel scraping step by step...")
    print("\nIMPORTANT: Make sure no other Playwright browsers are running")
    print("="*60)
    
    await debug_vercel()
    print("\n" + "="*60)
    await test_static_on_vercel()
    print("\n" + "="*60)
    await test_playwright_directly()

if __name__ == "__main__":
    asyncio.run(main())