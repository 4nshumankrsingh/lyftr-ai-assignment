"""
Test Hacker News specifically for interaction requirements
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_hackernews_interactions():
    """Test Hacker News specifically for depth ≥ 3"""
    print("\n" + "="*60)
    print("Testing Hacker News for Interaction Depth ≥ 3")
    print("="*60)
    
    from app.scraper.fallback_strategy import FallbackStrategy
    
    strategy = FallbackStrategy()
    
    try:
        # Test with timeout
        result_type, data = await asyncio.wait_for(
            strategy.scrape_with_fallback('https://news.ycombinator.com/'),
            timeout=45.0
        )
        
        print(f"✓ Scraping completed!")
        print(f"Strategy: {result_type}")
        print(f"Sections: {len(data.get('sections', []))}")
        
        # Check interactions
        interactions = data.get('interactions', {})
        clicks = interactions.get('clicks', [])
        scrolls = interactions.get('scrolls', 0)
        pages = interactions.get('pages', [])
        
        print(f"\nInteraction Results:")
        print(f"Clicks: {len(clicks)}")
        print(f"Scrolls: {scrolls}")
        print(f"Pages visited: {len(pages)}")
        
        total_interactions = len(clicks) + scrolls
        print(f"\nTotal interactions: {total_interactions}")
        
        if total_interactions >= 3:
            print("✅ SUCCESS: Achieved depth ≥ 3!")
        else:
            print("⚠️  WARNING: Depth < 3")
            
            # Show what we found
            if clicks:
                print("\nClicks attempted:")
                for click in clicks:
                    print(f"  - {click}")
            
            # Check if we should force more interactions
            print("\nSuggestions:")
            if scrolls == 0:
                print("  - Add more scrolling")
            if len(pages) <= 1:
                print("  - Try pagination")
            if len(clicks) == 0:
                print("  - Look for 'More' or 'Next' buttons")
        
        return total_interactions >= 3
        
    except asyncio.TimeoutError:
        print("❌ FAILED: Timeout after 45 seconds")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_hackernews_interactions()
    
    print("\n" + "="*60)
    if success:
        print("✅ Hacker News test PASSED - Ready for evaluation!")
    else:
        print("⚠️  Hacker News test needs improvement")
        print("\nQuick fix: Update interaction_handler.py to be more aggressive")
        print("with sites that have pagination like Hacker News.")

if __name__ == "__main__":
    asyncio.run(main())