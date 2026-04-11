import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

print("=" * 80)
print("🎬 TESTING TRAILERS - PYTHON V1 & V2")
print("=" * 80)

# ============================================
# PART 1: V2 MOVIE DETAILS - TRAILER
# ============================================
print("\n" + "=" * 80)
print("📀 V2 MOVIE DETAILS - Avatar")
print("=" * 80)

async def test_v2_trailer():
    from moviebox_api.v2 import Search, Session, MovieDetails
    from moviebox_api.v2.core import SubjectType
    
    session = Session()
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    movie = results.items[0]
    
    details = MovieDetails(session)
    detail_data = await details.get_content(movie.detailPath)
    
    subject = detail_data.get('subject', {})
    
    print(f"\n✅ Movie: {subject.get('title')}")
    
    # Check for trailer
    if 'trailer' in subject:
        trailer = subject['trailer']
        print(f"\n🎥 TRAILER FOUND!")
        print(f"   Type: {type(trailer)}")
        
        if isinstance(trailer, dict):
            print(f"\n   Trailer keys: {list(trailer.keys())}")
            
            if 'videoAddress' in trailer:
                vid = trailer['videoAddress']
                print(f"\n   📹 Video Address:")
                if isinstance(vid, dict):
                    for k, v in vid.items():
                        print(f"      {k}: {v}")
                else:
                    print(f"      {vid}")
            
            if 'cover' in trailer:
                cover = trailer['cover']
                print(f"\n   🖼️ Trailer Thumbnail:")
                if hasattr(cover, 'url'):
                    print(f"      {cover.url}")
                elif isinstance(cover, dict):
                    print(f"      {cover.get('url')}")
            
            # Show full trailer object
            print(f"\n   📋 Full trailer data:")
            print(json.dumps(trailer, indent=2, default=str)[:1000])
    else:
        print("\n   ❌ No trailer found in subject")
    
    # Also check resource for trailer
    resource = detail_data.get('resource', {})
    if 'trailer' in resource:
        print(f"\n   ✅ Trailer also in resource!")

asyncio.run(test_v2_trailer())

# ============================================
# PART 2: V1 MOVIE DETAILS - TRAILER
# ============================================
print("\n" + "=" * 80)
print("📀 V1 MOVIE DETAILS - Avatar")
print("=" * 80)

async def test_v1_trailer():
    from moviebox_api.v1 import Search, Session, MovieDetails
    from moviebox_api.v1 import SubjectType
    
    session = Session()
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    movie = results.items[0]
    
    details = MovieDetails(session)
    detail_data = await details.get_content(movie.detailPath)
    
    subject = detail_data.get('subject', {})
    
    print(f"\n✅ Movie: {subject.get('title')}")
    
    if 'trailer' in subject:
        trailer = subject['trailer']
        print(f"\n🎥 TRAILER FOUND!")
        print(json.dumps(trailer, indent=2, default=str)[:1500])
    else:
        print("\n   ❌ No trailer found")

asyncio.run(test_v1_trailer())

# ============================================
# PART 3: TEST OTHER MOVIES FOR TRAILERS
# ============================================
print("\n" + "=" * 80)
print("📀 TESTING MULTIPLE MOVIES FOR TRAILERS")
print("=" * 80)

async def test_multiple_trailers():
    from moviebox_api.v2 import Search, Session, MovieDetails
    from moviebox_api.v2.core import SubjectType
    
    session = Session()
    
    test_movies = ["Avatar", "Inception", "War Machine", "Pretty Lethal"]
    
    for movie_name in test_movies:
        print(f"\n🎬 {movie_name}:")
        try:
            search = Search(session, query=movie_name, subject_type=SubjectType.MOVIES)
            results = await search.get_content_model()
            if results.items:
                movie = results.items[0]
                details = MovieDetails(session)
                detail_data = await details.get_content(movie.detailPath)
                subject = detail_data.get('subject', {})
                
                if 'trailer' in subject and subject['trailer']:
                    trailer = subject['trailer']
                    if isinstance(trailer, dict) and 'videoAddress' in trailer:
                        vid = trailer['videoAddress']
                        url = vid.get('url') if isinstance(vid, dict) else str(vid)
                        print(f"   ✅ Has trailer: {url[:80]}...")
                    else:
                        print(f"   ✅ Has trailer (format: {type(trailer)})")
                else:
                    print(f"   ❌ No trailer")
            else:
                print(f"   ❌ Not found")
        except Exception as e:
            print(f"   ⚠️ Error: {e}")

asyncio.run(test_multiple_trailers())

# ============================================
# PART 4: CHECK WORKER FOR TRAILERS
# ============================================
print("\n" + "=" * 80)
print("🌐 WORKER - CHECKING FOR TRAILERS")
print("=" * 80)

import httpx

async def test_worker_trailer():
    WORKER_URL = "https://movieapi2.trackerwanga254.workers.dev"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check detail endpoint for trailer
        resp = await client.get(f"{WORKER_URL}/detail/avatar-WLDIi21IUBa")
        data = resp.json()
        
        print(f"\n✅ Worker Detail Keys: {list(data.keys())}")
        
        metadata = data.get('metadata', {})
        print(f"\n📋 Metadata keys: {list(metadata.keys())}")
        
        # Look for trailer in any field
        if 'trailer' in metadata:
            print(f"\n🎥 TRAILER FOUND in metadata!")
            print(json.dumps(metadata['trailer'], indent=2)[:500])
        else:
            print(f"\n❌ No 'trailer' field in metadata")
        
        # Check if there's any other field with trailer
        for key in data.keys():
            if 'trailer' in key.lower():
                print(f"\n   Found '{key}' field!")
                print(json.dumps(data[key], indent=2)[:300])

asyncio.run(test_worker_trailer())

print("\n" + "=" * 80)
print("✅ TRAILER TEST COMPLETE")
print("=" * 80)
