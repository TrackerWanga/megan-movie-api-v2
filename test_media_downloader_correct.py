import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

print("=" * 80)
print("🎯 FINDING CORRECT MediaFileDownloader USAGE")
print("=" * 80)

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v1 import MediaFileDownloader, MovieDetails

async def test_correct_usage():
    session = Session()
    
    # 1. Search for movie
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    movie_item = results.items[0]
    
    print(f"\n✅ Found: {movie_item.title}")
    print(f"   Type: {type(movie_item)}")
    print(f"   SubjectId: {movie_item.subjectId}")
    
    # 2. Get FULL movie details (MediaFileDownloader might need this)
    print(f"\n📋 Getting full movie details...")
    details = MovieDetails(session)
    full_details = await details.get_content(movie_item.detailPath)
    
    print(f"   Full details keys: {list(full_details.keys())}")
    
    # 3. Check what MediaFileDownloader expects
    print(f"\n🔍 MediaFileDownloader __init__ signature:")
    import inspect
    sig = inspect.signature(MediaFileDownloader.__init__)
    print(f"   {sig}")
    
    # 4. Try with full details
    print(f"\n🧪 Trying MediaFileDownloader with full details...")
    try:
        # Maybe it needs the subject from full_details?
        subject = full_details.get('subject', {})
        print(f"   Subject type: {type(subject)}")
        
        # Or maybe it needs a different item type?
        from moviebox_api.v2 import MovieDetails as V2MovieDetails
        v2_details = V2MovieDetails(session)
        v2_full = await v2_details.get_content(movie_item.detailPath)
        print(f"   V2 Full details keys: {list(v2_full.keys()) if v2_full else 'None'}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Check MediaFileDownloader.request_headers and cookies
    print(f"\n🍪 Checking request headers/cookies...")
    try:
        # Create a dummy instance to see what it needs
        # MediaFileDownloader might need specific initialization
        print(f"   MediaFileDownloader attributes:")
        for attr in dir(MediaFileDownloader):
            if 'request' in attr.lower() or 'cookie' in attr.lower():
                print(f"      - {attr}")
    except Exception as e:
        print(f"   Error: {e}")

asyncio.run(test_correct_usage())
