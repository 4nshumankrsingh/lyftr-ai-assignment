"""
FINAL VERIFICATION TEST - GUARANTEES STAGE 4 PASSES
"""
import asyncio
import httpx
import json
import sys

async def test_stage4_guarantee():
    print("="*60)
    print("FINAL STAGE 4 GUARANTEE TEST - HACKER NEWS")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Hacker News (MUST PASS STAGE 4)
        print("\n🚀 TEST 1: Hacker News (Stage 4 Critical)")
        print("-"*40)
        
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://news.ycombinator.com/"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            interactions = result.get('interactions', {})
            
            print(f"Response Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            print(f"Strategy: {result.get('meta', {}).get('strategy', 'N/A')}")
            
            print(f"\n📊 INTERACTIONS:")
            print(f"  • Clicks: {len(interactions.get('clicks', []))}")
            print(f"  • Scrolls: {interactions.get('scrolls', 0)}")
            print(f"  • Pages: {len(interactions.get('pages', []))}")
            print(f"  • Total Depth: {interactions.get('totalDepth', 0)}")
            
            # Show click details
            clicks = interactions.get('clicks', [])
            if clicks:
                print(f"\n🔍 Click Details:")
                for i, click in enumerate(clicks[:3]):
                    print(f"  {i+1}. {click}")
            
            # Check Stage 4 requirements
            total_interactions = len(clicks) + interactions.get('scrolls', 0)
            print(f"\n✅ STAGE 4 REQUIREMENTS:")
            print(f"  • Total interactions ≥ 3: {total_interactions} {'✓' if total_interactions >= 3 else '✗'}")
            print(f"  • Has clicks: {'✓' if len(clicks) > 0 else '✗'}")
            print(f"  • Has scrolls: {'✓' if interactions.get('scrolls', 0) > 0 else '✗'}")
            print(f"  • Multiple pages: {'✓' if len(interactions.get('pages', [])) > 1 else '✗'}")
            
            if total_interactions >= 3:
                print(f"\n🎉 STAGE 4 GUARANTEE SUCCESSFUL!")
                print(f"Total interactions: {total_interactions} (meets ≥ 3 requirement)")
                return True
            else:
                print(f"\n❌ STAGE 4 REQUIREMENTS NOT MET!")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    
async def test_static_site():
    print("\n" + "="*60)
    print("TEST 2: Static Site (Wikipedia)")
    print("-"*40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            print(f"Response Status: {data.get('status')}")
            print(f"Strategy: {result.get('meta', {}).get('strategy', 'N/A')}")
            print(f"Sections: {len(result.get('sections', []))}")
            
            # Check if static scraping still works
            if result.get('sections') and len(result.get('sections', [])) > 0:
                print("✅ Static scraping works correctly")
                return True
            else:
                print("❌ Static scraping failed")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False

async def test_js_site():
    print("\n" + "="*60)
    print("TEST 3: JS Site (Vercel)")
    print("-"*40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://vercel.com/"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            print(f"Response Status: {data.get('status')}")
            print(f"Strategy: {result.get('meta', {}).get('strategy', 'N/A')}")
            print(f"Sections: {len(result.get('sections', []))}")
            
            # Check if we got content
            if result.get('sections') and len(result.get('sections', [])) > 0:
                print("✅ JS scraping got content")
                return True
            else:
                print("⚠️ JS scraping got no sections")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False

async def test_health_check():
    print("\n" + "="*60)
    print("TEST 4: Health Check")
    print("-"*40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("http://localhost:8000/healthz")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status', 'N/A')}")
            print(f"Playwright: {data.get('services', {}).get('playwright', 'N/A')}")
            
            if data.get('status') == 'ok':
                print("✅ Health check passed")
                return True
            else:
                print("❌ Health check failed")
                return False
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

async def run_comprehensive_test():
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST - ALL FIXES APPLIED")
    print("="*60)
    
    print("\n📋 Checking if services are running...")
    
    # Test 1: Health Check
    health_ok = await test_health_check()
    if not health_ok:
        print("\n❌ Health check failed. Make sure backend is running:")
        print("  cd backend && uvicorn app.main:app --reload --port 8000")
        return
    
    # Test 2: Stage 4 Guarantee (MOST IMPORTANT)
    stage4_ok = await test_stage4_guarantee()
    
    # Test 3: Static site
    static_ok = await test_static_site()
    
    # Test 4: JS site
    js_ok = await test_js_site()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    tests = [
        ("Health Check", health_ok),
        ("Stage 4 Guarantee (Hacker News)", stage4_ok),
        ("Static Site (Wikipedia)", static_ok),
        ("JS Site (Vercel)", js_ok)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_result in tests:
        status = "✅ PASS" if test_result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if test_result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if stage4_ok:
        print("\n🎉 CRITICAL SUCCESS: Stage 4 guarantee works!")
        print("Hacker News will now always return interactions.")
        print("\nYou can now run the full evaluation test.")
    else:
        print("\n❌ CRITICAL FAILURE: Stage 4 guarantee failed!")
        print("Check the logs and fix the issue.")
    
    # Provide next steps
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    
    if passed == total:
        print("1. Run the full evaluation: python evaluation_test.py")
        print("2. Update capabilities.json with 'true' for all implemented features")
        print("3. Update README.md with your test URLs")
        print("4. Submit your repository!")
    elif stage4_ok:
        print("1. Stage 4 is fixed! Run: python evaluation_test.py")
        print("2. Check why other tests failed")
    else:
        print("1. Fix Stage 4 first - check backend logs")
        print("2. Ensure Playwright is installed: playwright install")
        print("3. Run debug_hackernews_now.py for detailed logs")

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Make sure both services are running!")
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print("\nStarting comprehensive test in 3 seconds...")
    
    import time
    time.sleep(3)
    
    asyncio.run(run_comprehensive_test())