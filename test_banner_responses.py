import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

print("=" * 80)
print("🎬 TESTING BANNER ROUTER - ACTUAL JSON RESPONSES")
print("=" * 80)

# ============================================
# TEST 1: MAIN BANNERS
# ============================================
print("\n" + "=" * 80)
print("1️⃣ GET /homepage/banners")
print("=" * 80)

async def test_banners():
    from moviebox_api.v2 import Homepage, Session
    
    session = Session()
    homepage = Homepage(session)
    home_data = await homepage.get_content_model()
    
    banners = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "BANNER":
                if hasattr(item, 'banner') and item.banner and hasattr(item.banner, 'items'):
                    for banner_item in item.banner.items:
                        banners.append({
                            "title": banner_item.title if hasattr(banner_item, 'title') else None,
                            "image": {
                                "url": str(banner_item.image.url) if hasattr(banner_item, 'image') and banner_item.image else None,
                                "width": banner_item.image.width if hasattr(banner_item, 'image') and banner_item.image else None,
                                "height": banner_item.image.height if hasattr(banner_item, 'image') and banner_item.image else None,
                            } if hasattr(banner_item, 'image') else None,
                            "subject_id": str(banner_item.subjectId) if hasattr(banner_item, 'subjectId') else None,
                            "detail_path": banner_item.detailPath if hasattr(banner_item, 'detailPath') else None
                        })
    
    print(f"\n✅ Found {len(banners)} banners")
    if banners:
        print("\n📋 Sample banner (first item):")
        print(json.dumps(banners[0], indent=2, default=str))

# ============================================
# TEST 2: TRENDING
# ============================================
print("\n" + "=" * 80)
print("2️⃣ GET /homepage/trending")
print("=" * 80)

async def test_trending():
    from moviebox_api.v2 import Homepage, Session
    
    session = Session()
    homepage = Homepage(session)
    home_data = await homepage.get_content_model()
    
    trending = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title in ["Popular Series", "Popular Movie"]:
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            trending.append({
                                "title": subject.title if hasattr(subject, 'title') else None,
                                "year": subject.releaseDate.year if hasattr(subject, 'releaseDate') and subject.releaseDate else None,
                                "rating": subject.imdbRatingValue if hasattr(subject, 'imdbRatingValue') else None,
                                "genres": subject.genre if isinstance(subject.genre, list) else [subject.genre] if subject.genre else [],
                                "poster": str(subject.cover.url) if hasattr(subject, 'cover') and subject.cover else None,
                                "subject_id": str(subject.subjectId) if hasattr(subject, 'subjectId') else None,
                                "detail_path": subject.detailPath if hasattr(subject, 'detailPath') else None
                            })
    
    print(f"\n✅ Found {len(trending)} trending items")
    if trending:
        print("\n📋 Sample trending item:")
        print(json.dumps(trending[0], indent=2, default=str))

# ============================================
# TEST 3: ALL SECTIONS SUMMARY
# ============================================
print("\n" + "=" * 80)
print("3️⃣ ALL AVAILABLE SECTIONS (Python)")
print("=" * 80)

async def test_all_sections():
    from moviebox_api.v2 import Homepage, Session
    
    session = Session()
    homepage = Homepage(session)
    home_data = await homepage.get_content_model()
    
    sections = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            section_info = {
                "type": item.type if hasattr(item, 'type') else None,
                "title": item.title if hasattr(item, 'title') else None,
                "count": len(item.subjects) if hasattr(item, 'subjects') and item.subjects else 0
            }
            sections.append(section_info)
    
    print(f"\n✅ Total sections: {len(sections)}")
    print("\n📋 All sections:")
    for s in sections:
        if s['title']:
            print(f"   - {s['title']} ({s['type']}): {s['count']} items")

# ============================================
# TEST 4: PLATFORMS
# ============================================
print("\n" + "=" * 80)
print("4️⃣ GET /platforms")
print("=" * 80)

async def test_platforms():
    from moviebox_api.v2 import Homepage, Session
    
    session = Session()
    homepage = Homepage(session)
    home_data = await homepage.get_content_model()
    
    platforms = []
    if hasattr(home_data, 'platformList'):
        for item in home_data.platformList:
            platforms.append({
                "name": item.name if hasattr(item, 'name') else None,
                "uploaded_by": item.uploadBy if hasattr(item, 'uploadBy') else None
            })
    
    print(f"\n✅ Found {len(platforms)} platforms")
    if platforms:
        print("\n📋 Platforms:")
        for p in platforms[:5]:
            print(f"   - {p['name']} (by {p['uploaded_by']})")

# ============================================
# RUN ALL TESTS
# ============================================

async def main():
    await test_banners()
    await test_trending()
    await test_all_sections()
    await test_platforms()
    print("\n" + "=" * 80)
    print("✅ BANNER TESTS COMPLETE")
    print("=" * 80)

asyncio.run(main())
