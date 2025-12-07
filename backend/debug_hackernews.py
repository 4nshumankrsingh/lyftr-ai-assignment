"""
Debug script to see exact JSON response for Hacker News
"""
import asyncio
import httpx
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def debug_hackernews():
    """Debug Hacker News scraping response"""
    print("\n" + "="*60)
    print("DEBUG HACKER NEWS RESPONSE")
    print("="*60)
    
    url = "https://news.ycombinator.com/"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print(f"Sending POST to /scrape for {url}")
            response = await client.post(
                "http://localhost:8000/scrape",
                json={"url": url},
                timeout=60.0
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Pretty print the response
                print("\n✅ FULL RESPONSE STRUCTURE:")
                print(json.dumps(data, indent=2)[:2000] + "...")
                
                # Check interactions specifically
                print("\n🔍 INTERACTIONS DETAIL:")
                if 'result' in data and 'interactions' in data['result']:
                    interactions = data['result']['interactions']
                    print(f"  Clicks: {len(interactions.get('clicks', []))}")
                    print(f"  Scrolls: {interactions.get('scrolls', 0)}")
                    print(f"  Pages: {len(interactions.get('pages', []))}")
                    print(f"  Total depth: {len(interactions.get('clicks', [])) + interactions.get('scrolls', 0)}")
                    
                    # Show click details
                    clicks = interactions.get('clicks', [])
                    if clicks:
                        print(f"\n  Click actions:")
                        for i, click in enumerate(clicks[:5]):
                            print(f"    {i+1}. {click}")
                else:
                    print("  ❌ No interactions found in response!")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text[:500])
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    print("Make sure backend is running on http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    await debug_hackernews()

if __name__ == "__main__":
    asyncio.run(main())