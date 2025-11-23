"""
Test for MapAPI.generate_place_photo_url function
Get photo reference from place details API and generate URLs
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from integration.map_api import MapAPI
from schemas.map_schema import SearchLocationRequest


async def test_photo_url_with_maxwidth():
    """
    Test hàm generate_place_photo_url với parameter maxwidth
    """
    map_api = MapAPI()
    
    print("\n" + "="*80)
    print("TEST: Photo URL Generation with maxwidth parameter")
    print("="*80)
    
    search_queries = [
        "Hoan Kiem Lake",
        "Lotte World",
        "BreadTalk"
    ]
    
    all_urls = []
    
    try:
        for query in search_queries:
            print(f"\n[*] Searching for: {query}")
            print("-" * 80)
            
            search_request = SearchLocationRequest(
                query=query,
                language="vi"
            )
            
            try:
                autocomplete_response = await map_api.autocomplete_place(search_request)
                
                if not autocomplete_response.predictions:
                    print(f"[!] No results found for {query}")
                    continue
                
                place_id = autocomplete_response.predictions[0].place_id
                print(f"[+] Found place_id: {place_id}")
                
                # Get place details
                place_details = await map_api.get_place_details_from_autocomplete(place_id)
                
                print(f"[+] Place name: {place_details.name}")
                print(f"[+] Address: {place_details.formatted_address}")
                
                if not place_details.photos:
                    print(f"[!] No photos available for this place")
                    continue
                
                print(f"[+] Found {len(place_details.photos)} photos")
                
                # Generate URLs
                print(f"\n[*] Generated Photo URLs:")
                print("-" * 80)
                
                for idx, photo_info in enumerate(place_details.photos[:3], 1):
                    # Extract photo reference from the URL we generated earlier
                    # (In the fixed version, it's stored in photo_info.photo_url with maxwidth)
                    print(f"\n[{idx}] Photo:")
                    print(f"    URL: {photo_info.photo_url[:150]}...")
                    
                    all_urls.append({
                        "place": query,
                        "url": photo_info.photo_url
                    })
                    
                    # Verify URL is accessible
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as verify_client:
                            head_response = await verify_client.head(photo_info.photo_url, follow_redirects=True)
                            
                            if head_response.status_code == 200:
                                print(f"    [+] URL valid (Status: {head_response.status_code})")
                                content_type = head_response.headers.get("content-type", "")
                                if "image" in content_type:
                                    print(f"    [+] Content-Type: {content_type}")
                            else:
                                print(f"    [!] Status Code: {head_response.status_code}")
                    except Exception as e:
                        print(f"    [!] Error: {str(e)[:80]}")
                
            except Exception as e:
                print(f"[!] Error: {str(e)[:100]}")
                continue
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"[+] Total URLs generated: {len(all_urls)}\n")
        
        if all_urls:
            print("All URLs (copy to browser to view):\n")
            for item in all_urls:
                print(f"Place: {item['place']}")
                print(f"URL: {item['url']}\n")
        
    finally:
        await map_api.client.aclose()
        print("[+] Test completed and client closed")


if __name__ == "__main__":
    print("\n[*] Starting Photo URL Generation Test\n")
    asyncio.run(test_photo_url_with_maxwidth())
    print("\n[+] All tests completed!")
