"""
Debug Hacker News immediately
"""
import asyncio
import httpx
import json
import sys

async def debug_hackernews():
    print("="*60)
    print("IMMEDIATE HACKER NEWS DEBUG")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Testing Hacker News API...")
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://news.ycombinator.com/"}
        )
        
        print(f"Status code: {response.status_code}")
        data = response.json()
        
        print(f"\nResponse status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        
        if data.get('status') == 'error':
            print("\n❌ ERROR DETECTED!")
            result = data.get('result', {})
            errors = result.get('errors', [])
            if errors:
                print("Errors found:")
                for error in errors:
                    print(f"  - {error.get('message')} (phase: {error.get('phase')})")
        
        # Also check what the fallback strategy does
        print("\n" + "="*60)
        print("Testing fallback strategy directly...")
        print("="*60)
        
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            from app.scraper.fallback_strategy import FallbackStrategy
            
            strategy = FallbackStrategy()
            strategy_used, result = await strategy.scrape_with_fallback("https://news.ycombinator.com/")
            
            print(f"Strategy used: {strategy_used}")
            print(f"Sections: {len(result.get('sections', []))}")
            
            interactions = result.get('interactions', {})
            print(f"Interactions: {len(interactions.get('clicks', []))} clicks, {interactions.get('scrolls', 0)} scrolls")
            
        except Exception as e:
            print(f"Fallback test failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    print("Debugging Hacker News issue...")
    await asyncio.sleep(1)
    await debug_hackernews()

if __name__ == "__main__":
    asyncio.run(main())