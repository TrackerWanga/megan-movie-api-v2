import enum
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Homepage, Session

async def get_all_banners():
    session = Session()
    
    print("=" * 100)
    print("🏠 HOMEPAGE / BANNER DATA")
    print("=" * 100)
    
    # Get homepage
    homepage = Homepage(session)
    
    # Method 1: Raw dict
    raw_data = await homepage.get_content()
    print("\n📄 RAW DATA (dict):")
    print(json.dumps(raw_data, indent=2, default=str)[:2000])
    
    # Method 2: Typed model (better)
    model = await homepage.get_content_model()
    print("\n🏗️  MODEL DATA:")
    print(f"   Type: {type(model)}")
    print(f"   Fields: {model.__dict__.keys()}")
    
    # Extract banner lists
    print("\n" + "=" * 100)
    print("📊 BANNER SECTIONS")
    print("=" * 100)
    
    # platformList = Main banners/sliders
    if hasattr(model, 'platformList'):
        banners = model.platformList
        print(f"\n🎯 PLATFORM LIST / MAIN BANNERS ({len(banners)} items):")
        
        for i, banner in enumerate(banners[:5]):  # First 5
            print(f"\n   [{i+1}] {banner.title}")
            print(f"       ID: {banner.subjectId}")
            print(f"       Type: {banner.subjectType} (1=Movie, 2=TV, etc.)")
            print(f"       Path: {banner.detailPath}")
            
            # Cover image
            if hasattr(banner, 'cover') and banner.cover:
                cover = banner.cover
                print(f"       Image: {cover.url}")
                print(f"       Size: {cover.width}x{cover.height}")
            
            # Trailer
            if hasattr(banner, 'trailer') and banner.trailer:
                print(f"       Has Trailer: ✅")
            
            # Genre
            if hasattr(banner, 'genre') and banner.genre:
                print(f"       Genre: {banner.genre}")
    
    # operatingList = Featured/operating content
    if hasattr(model, 'operatingList'):
        operating = model.operatingList
        print(f"\n⚙️  OPERATING LIST / FEATURED ({len(operating)} items):")
        
        for i, item in enumerate(operating[:3]):
            print(f"\n   [{i+1}] {item.title}")
            print(f"       ID: {item.subjectId}")
            if hasattr(item, 'cover') and item.cover:
                print(f"       Image: {item.cover.url}")
    
    # trending (if exists in raw)
    if 'trending' in raw_data:
        trending = raw_data['trending']
        print(f"\n🔥 TRENDING ({len(trending)} items):")
        for i, item in enumerate(trending[:3]):
            print(f"   [{i+1}] {item.get('title', 'N/A')}")
    
    return model

asyncio.run(get_all_banners())
