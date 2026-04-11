import enum
import sys
import asyncio
import json
import inspect

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

print("=" * 80)
print("🐍 PYTHON MOVIEBOX_API - COMPLETE EXPORTS")
print("=" * 80)

# ============================================
# PART 1: V1 MODULE EXPORTS
# ============================================
print("\n" + "=" * 80)
print("📦 V1 MODULE EXPORTS")
print("=" * 80)

try:
    from moviebox_api import v1
    print("\n✅ V1 Classes:")
    for attr in dir(v1):
        if not attr.startswith('_'):
            obj = getattr(v1, attr)
            if inspect.isclass(obj):
                print(f"   - {attr}")
except ImportError as e:
    print(f"   ❌ V1 not available: {e}")

# ============================================
# PART 2: V2 MODULE EXPORTS
# ============================================
print("\n" + "=" * 80)
print("📦 V2 MODULE EXPORTS")
print("=" * 80)

from moviebox_api import v2

print("\n✅ V2 Classes:")
for attr in dir(v2):
    if not attr.startswith('_'):
        try:
            obj = getattr(v2, attr)
            if inspect.isclass(obj):
                print(f"   - {attr}")
        except:
            pass

# ============================================
# PART 3: V2 CORE MODULE
# ============================================
print("\n" + "=" * 80)
print("📦 V2 CORE MODULE")
print("=" * 80)

from moviebox_api.v2 import core

print("\n✅ Core Classes & Functions:")
for attr in dir(core):
    if not attr.startswith('_'):
        obj = getattr(core, attr)
        if inspect.isclass(obj) or inspect.isfunction(obj):
            print(f"   - {attr}")

# ============================================
# PART 4: V2 DOWNLOAD MODULE
# ============================================
print("\n" + "=" * 80)
print("📦 V2 DOWNLOAD MODULE")
print("=" * 80)

from moviebox_api.v2 import download as v2_download

print("\n✅ Download Classes:")
for attr in dir(v2_download):
    if not attr.startswith('_'):
        obj = getattr(v2_download, attr)
        if inspect.isclass(obj):
            print(f"   - {attr}")

# ============================================
# PART 5: SUBJECT TYPES
# ============================================
print("\n" + "=" * 80)
print("📦 SUBJECT TYPES")
print("=" * 80)

from moviebox_api.v2.core import SubjectType

print("\n✅ SubjectType values:")
for attr in dir(SubjectType):
    if not attr.startswith('_'):
        val = getattr(SubjectType, attr)
        if not callable(val):
            print(f"   - {attr}: {val}")

# ============================================
# PART 6: ACTUAL DATA TEST
# ============================================
print("\n" + "=" * 80)
print("📦 ACTUAL DATA - SEARCH (Avatar)")
print("=" * 80)

async def test_search():
    from moviebox_api.v2 import Search, Session
    from moviebox_api.v2.core import SubjectType
    
    session = Session()
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    print(f"\n✅ Search results: {len(results.items)} items")
    
    if results.items:
        item = results.items[0]
        print(f"\n📀 First result: {item.title}")
        print(f"\n🔍 SearchResultItem ATTRIBUTES:")
        for attr in dir(item):
            if not attr.startswith('_') and not callable(getattr(item, attr)):
                val = getattr(item, attr)
                if val is not None and not isinstance(val, (dict, list)):
                    print(f"   - {attr}: {val}")
        
        # Show all attributes with their types
        print(f"\n📋 Full SearchResultItem data:")
        data = {
            "title": item.title,
            "subjectId": str(item.subjectId) if item.subjectId else None,
            "detailPath": item.detailPath,
            "subjectType": item.subjectType.value if hasattr(item.subjectType, 'value') else str(item.subjectType),
            "imdbRatingValue": item.imdbRatingValue,
            "releaseDate": str(item.releaseDate) if item.releaseDate else None,
            "genre": item.genre,
            "description": item.description[:100] + "..." if item.description else None,
            "hasResource": item.hasResource,
            "duration": item.duration,
        }
        print(json.dumps(data, indent=2, default=str))

asyncio.run(test_search())

# ============================================
# PART 7: MOVIE DETAILS
# ============================================
print("\n" + "=" * 80)
print("📦 ACTUAL DATA - MOVIE DETAILS")
print("=" * 80)

async def test_details():
    from moviebox_api.v2 import Search, Session, MovieDetails
    from moviebox_api.v2.core import SubjectType
    
    session = Session()
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    item = results.items[0]
    
    details = MovieDetails(session)
    detail_data = await details.get_content(item.detailPath)
    
    print(f"\n✅ MovieDetails keys: {list(detail_data.keys())}")
    
    if 'subject' in detail_data:
        subject = detail_data['subject']
        print(f"\n📋 Subject keys: {list(subject.keys())}")
        
    if 'resource' in detail_data:
        resource = detail_data['resource']
        print(f"\n📋 Resource keys: {list(resource.keys())}")
        
    if 'stars' in detail_data:
        print(f"\n📋 Stars: {len(detail_data['stars'])} cast members")

asyncio.run(test_details())

# ============================================
# PART 8: DOWNLOAD DATA
# ============================================
print("\n" + "=" * 80)
print("📦 ACTUAL DATA - DOWNLOADS")
print("=" * 80)

async def test_downloads():
    from moviebox_api.v2 import Search, Session
    from moviebox_api.v2.core import SubjectType
    from moviebox_api.v2.download import DownloadableSingleFilesDetail
    
    session = Session()
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    item = results.items[0]
    
    dl = DownloadableSingleFilesDetail(session, item)
    dl_data = await dl.get_content()
    
    print(f"\n✅ Download data keys: {list(dl_data.keys())}")
    
    if 'downloads' in dl_data:
        print(f"\n📥 Downloads: {len(dl_data['downloads'])} qualities")
        for d in dl_data['downloads'][:2]:
            print(f"\n   Quality: {d.get('resolution')}p")
            print(f"   Format: {d.get('format')}")
            print(f"   Size: {d.get('size')} bytes")
            print(f"   Has URL: {bool(d.get('url'))}")
    
    if 'captions' in dl_data:
        print(f"\n📝 Captions: {len(dl_data['captions'])} languages")
        for c in dl_data['captions'][:3]:
            print(f"   - {c.get('lanName')} ({c.get('lan')})")

asyncio.run(test_downloads())

# ============================================
# PART 9: HOMEPAGE
# ============================================
print("\n" + "=" * 80)
print("📦 ACTUAL DATA - HOMEPAGE")
print("=" * 80)

async def test_homepage():
    from moviebox_api.v2 import Homepage, Session
    
    session = Session()
    homepage = Homepage(session)
    home_data = await homepage.get_content()
    
    print(f"\n✅ Homepage keys: {list(home_data.keys())}")
    
    if 'operatingList' in home_data:
        print(f"\n📋 Operating List: {len(home_data['operatingList'])} sections")

asyncio.run(test_homepage())

# ============================================
# PART 10: TV SERIES
# ============================================
print("\n" + "=" * 80)
print("📦 ACTUAL DATA - TV SERIES")
print("=" * 80)

async def test_tv():
    from moviebox_api.v2 import Search, Session, TVSeriesDetails
    from moviebox_api.v2.core import SubjectType
    
    session = Session()
    search = Search(session, query="Game of Thrones", subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if results.items:
        item = results.items[0]
        print(f"\n✅ Found: {item.title}")
        
        tv = TVSeriesDetails(session)
        tv_data = await tv.get_content(item.detailPath)
        
        if 'resource' in tv_data:
            resource = tv_data['resource']
            if 'seasons' in resource:
                print(f"\n📺 Seasons: {len(resource['seasons'])}")
                for s in resource['seasons'][:2]:
                    print(f"   Season {s.get('se')}: {s.get('maxEp')} episodes")

asyncio.run(test_tv())

print("\n" + "=" * 80)
print("✅ PYTHON EXPORTS COMPLETE")
print("=" * 80)
