import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

async def search_movie(query):
    """Search using moviebox_api directly"""
    session = Session()
    
    print(f"\n{'='*60}")
    print(f"🔍 SEARCHING FOR: '{query}'")
    print(f"{'='*60}")
    
    # Search in MOVIES only
    search = Search(session, query=query, subject_type=SubjectType.MOVIES)
    
    try:
        results = await search.get_content_model()
        
        print(f"\n📊 Found {len(results.items)} results\n")
        
        for i, item in enumerate(results.items[:10], 1):
            year = item.releaseDate.year if item.releaseDate else "N/A"
            print(f"{i}. {item.title} ({year})")
            print(f"   SubjectId: {item.subjectId}")
            print(f"   DetailPath: {item.detailPath}")
            print(f"   Rating: {item.imdbRatingValue}")
            print(f"   Genres: {item.genre}")
            print(f"   Poster: {item.cover.url if item.cover else 'N/A'}")
            print()
        
        # Show raw data for first result
        if results.items:
            print(f"\n{'='*60}")
            print(f"📋 RAW DATA FOR FIRST RESULT")
            print(f"{'='*60}")
            first = results.items[0]
            print(f"All attributes: {[a for a in dir(first) if not a.startswith('_') and not callable(getattr(first, a))][:20]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Get search query from user
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("Enter movie name to search: ").strip()
        if not query:
            query = "inception"
    
    asyncio.run(search_movie(query))
