"""
Quick test for Vercel fix
"""
import asyncio
import httpx
import json

async def test_vercel():
    print("="*60)
    print("TESTING VERCEl FIX")
    print("="*60)
    
    print("Make sure backend is running on http://localhost:8000")
    print("Testing Vercel (https://vercel.com/)")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8000/scrape",
            json={"url": "https://vercel.com/"}
        )
        
        print(f"\nStatus code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            
            result = data.get('result', {})
            strategy = result.get('meta', {}).get('strategy', 'N/A')
            sections = result.get('sections', [])
            
            print(f"\nStrategy used: {strategy}")
            print(f"Sections found: {len(sections)}")
            
            if sections:
                print("\nFirst 3 sections:")
                for i, section in enumerate(sections[:3]):
                    print(f"  {i+1}. {section.get('type', 'N/A')}: {section.get('label', 'N/A')[:50]}...")
                    if section.get('content', {}).get('text'):
                        print(f"     Text: {len(section['content']['text'])} chars")
            
            interactions = result.get('interactions', {})
            print(f"\nInteractions: {len(interactions.get('clicks', []))} clicks, {interactions.get('scrolls', 0)} scrolls")
            
            errors = result.get('errors', [])
            if errors:
                print(f"\nErrors: {len(errors)}")
                for error in errors[:3]:
                    print(f"  - {error.get('message', 'N/A')}")
            
            if len(sections) > 0:
                print("\n✅ VERCEl TEST PASSED - Got content!")
                return True
            else:
                print("\n❌ VERCEl TEST FAILED - No content")
                return False
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(response.text[:500])
            return False

async def main():
    print("\nTesting Vercel JS rendering...")
    await asyncio.sleep(2)
    
    success = await test_vercel()
    
    if success:
        print("\n" + "="*60)
        print("✅ VERCEl FIX WORKING! Now run the full test.")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ VERCEl still needs work")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())