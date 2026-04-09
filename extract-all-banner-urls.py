import enum
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Homepage, Session

async def extract_banner_urls():
    session = Session()
    homepage = Homepage(session)
    
    model = await homepage.get_content_model()
    
    all_urls = []
    
    print("=" * 100)
    print("🌐 EXTRACTING ALL BANNER URLS")
    print("=" * 100)
    
    # Process platformList (main banners)
    if hasattr(model, 'platformList'):
        print(f"\n🎯 PLATFORM LIST ({len(model.platformList)} banners):")
        
        for banner in model.platformList:
            urls = extract_urls_from_item(banner, "PLATFORM")
            all_urls.extend(urls)
    
    # Process operatingList (featured)
    if hasattr(model, 'operatingList'):
        print(f"\n⚙️  OPERATING LIST ({len(model.operatingList)} items):")
        
        for item in model.operatingList:
            urls = extract_urls_from_item(item, "OPERATING")
            all_urls.extend(urls)
    
    # Summary
    print("\n" + "=" * 100)
    print(f"📊 TOTAL URLS FOUND: {len(all_urls)}")
    print("=" * 100)
    
    # Group by type
    by_type = {}
    for url_info in all_urls:
        t = url_info['type']
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(url_info)
    
    for type_name, urls in by_type.items():
        print(f"\n{type_name} ({len(urls)}):")
        for u in urls[:3]:  # First 3
            print(f"   • {u['url'][:70]}...")
            print(f"     Context: {u['context']}")
    
    return all_urls

def extract_urls_from_item(item, list_type):
    """Extract all URLs from a banner/item"""
    urls = []
    
    # Main cover/poster
    if hasattr(item, 'cover') and item.cover:
        cover = item.cover
        if hasattr(cover, 'url'):
            urls.append({
                'type': 'BANNER_COVER',
                'url': str(cover.url),
                'context': f"{list_type}: {item.title}",
                'size': f"{cover.width}x{cover.height}"
            })
    
    # Trailer video
    if hasattr(item, 'trailer') and item.trailer:
        trailer = item.trailer
        if hasattr(trailer, 'videoAddress') and trailer.videoAddress:
            vid = trailer.videoAddress
            if hasattr(vid, 'url'):
                urls.append({
                    'type': 'BANNER_TRAILER',
                    'url': vid.url,
                    'context': f"{list_type}: {item.title} trailer",
                    'duration': vid.duration
                })
        
        # Trailer cover
        if hasattr(trailer, 'cover') and trailer.cover:
            if hasattr(trailer.cover, 'url'):
                urls.append({
                    'type': 'BANNER_TRAILER_THUMB',
                    'url': str(trailer.cover.url),
                    'context': f"{list_type}: {item.title} trailer thumb"
                })
    
    # Stills/backdrops
    if hasattr(item, 'stills') and item.stills:
        stills = item.stills
        if hasattr(stills, 'url'):
            urls.append({
                'type': 'BANNER_BACKDROP',
                'url': str(stills.url),
                'context': f"{list_type}: {item.title} backdrop"
            })
    
    return urls

asyncio.run(extract_banner_urls())
