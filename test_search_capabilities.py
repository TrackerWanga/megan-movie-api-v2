import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

print("=" * 80)
print("🔍 TESTING SEARCH CAPABILITIES - PYTHON & WORKER")
print("=" * 80)

# ============================================
# PART 1: PYTHON SEARCH CAPABILITIES
# ============================================
print("\n" + "=" * 80)
print("🐍 PYTHON SEARCH CAPABILITIES")
print("=" * 80)

async def test_python_search():
    from moviebox_api.v2 import Search, Session
    from moviebox_api.v2.core import SubjectType
    
    session = Session()
    
    # Test different subject types
    test_queries = [
        ("Avatar", SubjectType.MOVIES, "Movies"),
        ("Game of Thrones", SubjectType.TV_SERIES, "TV Series"),
        ("Naruto", SubjectType.ANIME, "Anime"),
        ("Imagine Dragons", SubjectType.MUSIC, "Music"),
        ("Documentary", SubjectType.EDUCATION, "Education"),
    ]
    
    print("\n📋 Subject Types Available:")
    for attr in dir(SubjectType):
        if not attr.startswith('_'):
            val = getattr(SubjectType, attr)
            if not callable(val):
                print(f"   - {attr}: {val}")
    
    print("\n🔍 Search by Type:")
    for query, subject_type, type_name in test_queries[:3]:
        try:
            search = Search(session, query=query, subject_type=subject_type)
            results = await search.get_content_model()
            print(f"\n   {type_name} ('{query}'): {len(results.items)} results")
            if results.items:
                item = results.items[0]
                print(f"      First: {item.title} ({item.subjectId})")
        except Exception as e:
            print(f"   {type_name}: Error - {e}")

asyncio.run(test_python_search())

# ============================================
# PART 2: WORKER SEARCH CAPABILITIES
# ============================================
print("\n" + "=" * 80)
print("🌐 WORKER SEARCH CAPABILITIES")
print("=" * 80)

import httpx

async def test_worker_search():
    WORKER_URL = "https://movieapi2.trackerwanga254.workers.dev"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test search
        print("\n🔍 Worker Search:")
        resp = await client.get(f"{WORKER_URL}/search?q=Avatar")
        data = resp.json()
        print(f"   Results: {data.get('count')}")
        if data.get('movies'):
            m = data['movies'][0]
            print(f"   First: {m['name']} (ID: {m.get('subject_id')})")
        
        # Test search suggest
        print("\n💡 Search Suggestions:")
        resp = await client.get(f"{WORKER_URL}/search/suggest?q=Avat")
        data = resp.json()
        print(f"   Query: {data.get('query')}")
        print(f"   Suggestions: {len(data.get('suggestions', []))}")
        for s in data.get('suggestions', [])[:5]:
            print(f"      - {s}")
        
        # Test category searches
        print("\n📂 Category Endpoints:")
        categories = ['movies', 'tv-series', 'animation']
        for cat in categories:
            resp = await client.get(f"{WORKER_URL}/{cat}")
            if resp.status_code == 200:
                data = resp.json()
                sections = data.get('sections', [])
                if sections:
                    print(f"   /{cat}: {sections[0].get('count', 0)} items")

asyncio.run(test_worker_search())

print("\n" + "=" * 80)
print("✅ SEARCH TEST COMPLETE")
print("=" * 80)
