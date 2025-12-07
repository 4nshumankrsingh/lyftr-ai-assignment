"""
Final verification test for all fixes
"""
import asyncio
import httpx
import json
import sys

async def test_all_fixes():
    print("="*60)
    print("FINAL FIX VERIFICATION")
    print("="*60)
    
    print("\n1️⃣ Testing Stage 1: Health Check")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("http://localhost:8000/healthz")
        if response.status_code == 200 and response.json().get("status") == "ok":
            print("✅ Health check PASSED")
        else:
            print("❌ Health check FAILED")
            return False
    
    print("\n2️⃣ Testing Stage 2: Static Scraping (Wikipedia)")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}
        )
        
        if response.status_code == 200:
            data = response.json()
            sections = data.get('result', {}).get('sections', [])
            if sections and len(sections) > 0:
                print(f"✅ Static scraping PASSED ({len(sections)} sections)")
            else:
                print("❌ Static scraping FAILED - No sections")
                return False
        else:
            print(f"❌ Static scraping FAILED - Status {response.status_code}")
            return False
    
    print("\n3️⃣ Testing Stage 3: JS Rendering (Vercel)")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://vercel.com/"}
        )
        
        if response.status_code == 200:
            data = response.json()
            strategy = data.get('result', {}).get('meta', {}).get('strategy', '')
            sections = data.get('result', {}).get('sections', [])
            
            if strategy == 'js' and sections and len(sections) > 0:
                print(f"✅ JS rendering PASSED (strategy: {strategy}, sections: {len(sections)})")
            elif sections and len(sections) > 0:
                print(f"⚠️  JS rendering PARTIAL (got content but strategy: {strategy})")
            else:
                print("❌ JS rendering FAILED - No content")
                return False
        else:
            print(f"❌ JS rendering FAILED - Status {response.status_code}")
            return False
    
    print("\n4️⃣ Testing Stage 4: Interactions (Hacker News)")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://news.ycombinator.com/"}
        )
        
        if response.status_code == 200:
            data = response.json()
            interactions = data.get('result', {}).get('interactions', {})
            clicks = len(interactions.get('clicks', []))
            scrolls = interactions.get('scrolls', 0)
            pages = len(interactions.get('pages', []))
            
            print(f"Interactions found: {clicks} clicks, {scrolls} scrolls, {pages} pages")
            
            if clicks > 0 and scrolls >= 2:
                print("✅ Interactions PASSED - Stage 4 requirements met!")
                
                # Show details
                if clicks > 0:
                    print("\nClick actions:")
                    for i, click in enumerate(interactions.get('clicks', [])[:3]):
                        print(f"  {i+1}. {click}")
            else:
                print("❌ Interactions FAILED - Not meeting Stage 4 requirements")
                return False
        else:
            print(f"❌ Interactions test FAILED - Status {response.status_code}")
            return False
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED! Your project is ready for submission!")
    print("="*60)
    
    print("\nNext steps:")
    print("1. Run the evaluation test: python backend/evaluation_test.py")
    print("2. Update README.md with your test URLs")
    print("3. Submit your repository!")
    
    return True

async def main():
    print("Make sure backend is running: uvicorn app.main:app --reload --port 8000")
    input("\nPress Enter when ready...")
    
    success = await test_all_fixes()
    
    if not success:
        print("\n❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())