"""
Test script to verify the scraper is working
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_static_scraper_direct():
    """Test static scraper directly"""
    print("\n=== Testing Static Scraper Directly ===")
    from app.scraper.static_scraper import StaticScraper
    
    scraper = StaticScraper()
    
    try:
        result = await scraper.scrape('https://en.wikipedia.org/wiki/Artificial_intelligence')
        print(f"✓ Static scraper SUCCESS!")
        print(f"  Sections found: {len(result.sections)}")
        print(f"  First section label: {result.sections[0].label if result.sections else 'None'}")
        print(f"  Has errors: {len(result.errors) > 0}")
        return True
    except Exception as e:
        print(f"✗ Static scraper FAILED: {e}")
        return False

async def test_fallback_strategy():
    """Test fallback strategy"""
    print("\n=== Testing Fallback Strategy ===")
    from app.scraper.fallback_strategy import FallbackStrategy
    
    strategy = FallbackStrategy()
    
    test_urls = [
        ("https://en.wikipedia.org/wiki/Artificial_intelligence", "static"),
        ("https://developer.mozilla.org/en-US/docs/Web/JavaScript", "static"),
        ("https://vercel.com/", "js")
    ]
    
    successes = 0
    for url, expected_type in test_urls:
        try:
            print(f"\nTesting: {url}")
            result_type, data = await strategy.scrape_with_fallback(url)
            print(f"  Result: {result_type} (expected: {expected_type})")
            print(f"  Sections: {len(data.get('sections', []))}")
            print(f"  Errors: {len(data.get('errors', []))}")
            
            if result_type == expected_type or (expected_type == "js" and result_type in ["js", "static"]):
                print(f"  ✓ PASS")
                successes += 1
            else:
                print(f"  ✗ FAIL - Wrong strategy")
                
        except Exception as e:
            print(f"  ✗ FAIL - Error: {e}")
    
    print(f"\nFallback strategy: {successes}/3 tests passed")
    return successes >= 2

async def test_api_endpoint():
    """Test API endpoint"""
    print("\n=== Testing API Endpoint ===")
    import httpx
    import json
    
    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            health_response = await client.get("http://localhost:8000/healthz")
            print(f"Health check: {health_response.status_code}")
            
            # Test scrape endpoint
            scrape_data = {
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
            }
            
            scrape_response = await client.post(
                "http://localhost:8000/scrape",
                json=scrape_data,
                timeout=35.0
            )
            
            print(f"Scrape response: {scrape_response.status_code}")
            
            if scrape_response.status_code == 200:
                response_json = scrape_response.json()
                print(f"  Status: {response_json.get('status')}")
                print(f"  Message: {response_json.get('message')}")
                print(f"  Strategy: {response_json.get('result', {}).get('meta', {}).get('strategy', 'N/A')}")
                print(f"  Sections: {len(response_json.get('result', {}).get('sections', []))}")
                
                if response_json.get('status') in ['success', 'partial']:
                    print("  ✓ API test PASSED")
                    return True
                else:
                    print("  ✗ API test FAILED - Bad status")
                    return False
            else:
                print(f"  ✗ API test FAILED - Status code {scrape_response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ✗ API test FAILED - Error: {e}")
        return False

async def test_interactive_site():
    """Test with a known interactive site"""
    print("\n=== Testing Interactive Site ===")
    
    # Try a site with tabs
    from app.scraper.fallback_strategy import FallbackStrategy
    
    strategy = FallbackStrategy()
    
    try:
        # MUI Tabs example (should use JS)
        result_type, data = await strategy.scrape_with_fallback('https://mui.com/material-ui/react-tabs/')
        print(f"Strategy used: {result_type}")
        print(f"Sections found: {len(data.get('sections', []))}")
        print(f"Interactions: {data.get('interactions', {})}")
        
        if result_type == "js" or len(data.get('sections', [])) > 0:
            print("✓ Interactive site test PASSED")
            return True
        else:
            print("✗ Interactive site test FAILED - No content")
            return False
            
    except Exception as e:
        print(f"✗ Interactive site test FAILED - Error: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("LYFTR AI SCRAPER - COMPREHENSIVE TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Direct static scraper
    results.append(await test_static_scraper_direct())
    
    # Test 2: Fallback strategy
    results.append(await test_fallback_strategy())
    
    # Test 3: API endpoint (requires server running)
    print("\n" + "=" * 60)
    print("IMPORTANT: Make sure backend is running on localhost:8000")
    print("Run this in another terminal: uvicorn app.main:app --reload --port 8000")
    print("=" * 60)
    
    server_running = input("\nIs the backend server running? (y/n): ").lower()
    if server_running == 'y':
        results.append(await test_api_endpoint())
    else:
        print("Skipping API test - server not running")
    
    # Test 4: Interactive site (optional)
    test_interactive = input("\nTest interactive site? (This may take 30+ seconds) (y/n): ").lower()
    if test_interactive == 'y':
        results.append(await test_interactive_site())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED! The scraper is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
    
    print("\nNEXT STEPS:")
    print("1. Update capabilities.json with your actual capabilities")
    print("2. Test the frontend at http://localhost:5173")
    print("3. Run through the 5 evaluation stages from the assignment")

if __name__ == "__main__":
    asyncio.run(main())