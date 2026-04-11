import enum
import sys
import asyncio
import signal

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

async def search_movie(query):
    session = Session()
    
    print(f"\n{'='*60}")
    print(f"🔍 SEARCHING: '{query}'")
    print(f"{'='*60}")
    
    try:
        # Set timeout for the entire operation
        search = Search(session, query=query, subject_type=SubjectType.MOVIES)
        
        # Try with timeout
        results = await asyncio.wait_for(search.get_content_model(), timeout=30.0)
        
        print(f"\n✅ Found {len(results.items)} results\n")
        
        for i, item in enumerate(results.items[:5], 1):
            year = item.releaseDate.year if item.releaseDate else "N/A"
            print(f"{i}. {item.title} ({year})")
            print(f"   SubjectId: {item.subjectId}")
            print(f"   Rating: {item.imdbRatingValue}")
            print(f"   Has download: {item.hasResource}")
            print()
        
        # Show raw data for first result
        if results.items:
            first = results.items[0]
            print(f"\n📋 RAW DATA for '{first.title}':")
            print(f"   subjectId: {first.subjectId}")
            print(f"   detailPath: {first.detailPath}")
            print(f"   hasResource: {first.hasResource}")
            print(f"   cover: {first.cover.url if first.cover else 'None'}")
            
    except asyncio.TimeoutError:
        print(f"\n❌ Timeout: Search for '{query}' took too long")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "War Machine"
    asyncio.run(search_movie(query))
