import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

async def simple_check():
    session = Session()
    
    # Test search for a movie that should exist
    print("=" * 60)
    print("SIMPLE API CHECK")
    print("=" * 60)
    
    # Try searching for "War Machine" (which we know exists)
    print("\n1. Searching for 'War Machine'...")
    search = Search(session, query="War Machine", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    print(f"   Found {len(results.items)} results")
    
    if results.items:
        first = results.items[0]
        print(f"\n   First result: {first.title}")
        print(f"   SubjectId: {first.subjectId}")
        print(f"   Has download: {first.hasResource}")
        print(f"   Rating: {first.imdbRatingValue}")
        
        # Check if there's a poster
        if first.cover:
            print(f"   Poster: {first.cover.url[:60]}...")
    
    print("\n" + "=" * 60)
    print("CHECK COMPLETE")
    print("=" * 60)

asyncio.run(simple_check())
