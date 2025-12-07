"""
Quick test to verify the fix works
"""
import asyncio
import httpx
import json

async def test_fix():
    print("Testing Hacker News with forced interactions...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://news.ycombinator.com/"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check interactions
            interactions = data.get('result', {}).get('interactions', {})
            clicks = len(interactions.get('clicks', []))
            scrolls = interactions.get('scrolls', 0)
            pages = len(interactions.get('pages', []))
            total_depth = clicks + scrolls
            
            print(f"\n✅ Response received")
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            
            print(f"\n📊 INTERACTIONS:")
            print(f"  Clicks: {clicks}")
            print(f"  Scrolls: {scrolls}")
            print(f"  Pages: {pages}")
            print(f"  Total depth: {total_depth}")
            
            if clicks > 0:
                print(f"\nClick actions:")
                for i, click in enumerate(interactions.get('clicks', [])[:3]):
                    print(f"  {i+1}. {click}")
            
            # Stage 4 requirements
            print(f"\n🎯 STAGE 4 REQUIREMENTS:")
            print(f"  Has clicks: {'✅' if clicks > 0 else '❌'}")
            print(f"  Has scrolls ≥ 2: {'✅' if scrolls >= 2 else '❌'} (actual: {scrolls})")
            print(f"  Has pages ≥ 3: {'✅' if pages >= 3 else '❌'} (actual: {pages})")
            print(f"  Total depth ≥ 3: {'✅' if total_depth >= 3 else '❌'} (actual: {total_depth})")
            
            if clicks > 0 and scrolls >= 2 and total_depth >= 3:
                print("\n🎉 STAGE 4 SHOULD PASS!")
                return True
            else:
                print("\n⚠️ Stage 4 might still fail")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
            return False

async def main():
    print("="*60)
    print("QUICK FIX VERIFICATION")
    print("="*60)
    
    print("Make sure backend is running on http://localhost:8000")
    print("Testing in 2 seconds...")
    await asyncio.sleep(2)
    
    success = await test_fix()
    
    print("\n" + "="*60)
    if success:
        print("✅ FIX WORKING! Now run evaluation_test.py")
    else:
        print("❌ FIX NEEDS ADJUSTMENT")

if __name__ == "__main__":
    asyncio.run(main())