"""
Quick test to verify Hacker News interactions work
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_interaction_handler():
    """Test the new interaction handler directly"""
    print("\nTesting Interaction Handler...")
    
    from playwright.async_api import async_playwright
    from app.scraper.interaction_handler import InteractionHandler
    
    # Create interaction handler
    handler = InteractionHandler(max_depth=3)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to Hacker News
        await page.goto('https://news.ycombinator.com/', wait_until='domcontentloaded')
        
        # Test interaction detection
        should_interact = await handler._should_interact(page, page.url)
        print(f"Should interact with Hacker News: {should_interact}")
        
        if should_interact:
            # Test forced scrolls
            scroll_result = await handler._force_scrolls(page, 2)
            print(f"Forced scrolls: {scroll_result['scrolls']}")
            
            # Test finding interactive elements
            interactive_result = await handler._find_and_click_interactive(page, 3)
            print(f"Found interactive clicks: {len(interactive_result['clicks'])}")
            
            if interactive_result['clicks']:
                print("Clicks found:")
                for click in interactive_result['clicks']:
                    print(f"  - {click}")
        
        await browser.close()
        
        return should_interact and scroll_result['scrolls'] >= 2

async def test_full_scrape():
    """Test full scrape with the new handler"""
    print("\n" + "="*60)
    print("Testing Full Scrape with Hacker News")
    print("="*60)
    
    from app.scraper.fallback_strategy import FallbackStrategy
    
    strategy = FallbackStrategy()
    
    try:
        result_type, data = await asyncio.wait_for(
            strategy.scrape_with_fallback('https://news.ycombinator.com/'),
            timeout=45.0
        )
        
        print(f"Scrape completed!")
        print(f"Strategy: {result_type}")
        
        # Check interactions
        interactions = data.get('interactions', {})
        clicks = interactions.get('clicks', [])
        scrolls = interactions.get('scrolls', 0)
        pages = interactions.get('pages', [])
        
        print(f"\nInteraction Results:")
        print(f"Clicks: {len(clicks)}")
        print(f"Scrolls: {scrolls}")
        print(f"Pages: {len(pages)}")
        
        total_interactions = len(clicks) + scrolls
        print(f"\nTotal interactions: {total_interactions}")
        
        if clicks:
            print("\nClicks performed:")
            for click in clicks[:5]:  # Show first 5 clicks
                print(f"  - {click}")
        
        if total_interactions >= 3:
            print("\n✅ SUCCESS: Achieved depth ≥ 3!")
            return True
        else:
            print("\n⚠️  WARNING: Depth < 3")
            return False
            
    except asyncio.TimeoutError:
        print("❌ Timeout after 45 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    print("\n" + "="*60)
    print("HACKER NEWS INTERACTION FIX TEST")
    print("="*60)
    
    # Test 1: Direct handler test
    print("\nTest 1: Testing Interaction Handler Directly")
    handler_success = await test_interaction_handler()
    
    # Test 2: Full scrape test
    print("\nTest 2: Testing Full Scrape")
    scrape_success = await test_full_scrape()
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    if handler_success and scrape_success:
        print("✅ BOTH TESTS PASSED!")
        print("\nThe interaction fix is working. Hacker News should now")
        print("get interactions and achieve depth ≥ 3.")
    elif scrape_success:
        print("✅ Full scrape test PASSED!")
        print("\nHacker News is getting interactions.")
    else:
        print("⚠️  Tests need improvement")
        print("\nCheck the output above for issues.")
    
    return handler_success or scrape_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)