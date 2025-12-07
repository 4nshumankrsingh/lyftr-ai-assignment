"""
Quick test to verify the fix works
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def quick_wikipedia_test():
    """Quick test with Wikipedia"""
    print("Testing Wikipedia (should be FAST - no Playwright)...")
    
    from app.scraper.fallback_strategy import FallbackStrategy
    
    strategy = FallbackStrategy()
    
    start = asyncio.get_event_loop().time()
    
    try:
        result_type, data = await asyncio.wait_for(
            strategy.scrape_with_fallback('https://en.wikipedia.org/wiki/Artificial_intelligence'),
            timeout=10.0  # Should complete in < 10 seconds
        )
        
        elapsed = asyncio.get_event_loop().time() - start
        
        print(f"✓ SUCCESS in {elapsed:.1f} seconds!")
        print(f"Strategy: {result_type}")
        print(f"Sections: {len(data.get('sections', []))}")
        print(f"Errors: {len(data.get('errors', []))}")
        
        if result_type == 'static' and elapsed < 5.0:
            print("✅ PERFECT! Wikipedia uses static scraper and is fast!")
            return True
        else:
            print("⚠️  Warning: Might still be using Playwright")
            return False
            
    except asyncio.TimeoutError:
        print("✗ FAILED: Timeout after 10 seconds")
        return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

async def main():
    print("\n" + "="*50)
    print("QUICK FIX TEST - Wikipedia Static Scraping")
    print("="*50)
    
    success = await quick_wikipedia_test()
    
    print("\n" + "="*50)
    if success:
        print("✅ FIX SUCCESSFUL!")
        print("Wikipedia now uses static scraper and completes in < 5 seconds.")
    else:
        print("❌ FIX NEEDED")
        print("The timeout issue is still present.")
    
    print("\nTo test API:")
    print("1. Make sure backend is running: uvicorn app.main:app --reload --port 8000")
    print("2. Test with: curl -X POST http://localhost:8000/scrape -H 'Content-Type: application/json' -d '{\"url\":\"https://en.wikipedia.org/wiki/Artificial_intelligence\"}'")

if __name__ == "__main__":
    asyncio.run(main())