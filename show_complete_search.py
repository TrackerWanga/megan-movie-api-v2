import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

async def show_complete_search(query):
    session = Session()
    
    print(f"\n{'='*80}")
    print(f"🔍 COMPLETE SEARCH DATA FOR: '{query}'")
    print(f"{'='*80}")
    
    search = Search(session, query=query, subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    print(f"\n📊 Total results: {len(results.items)}")
    
    for idx, item in enumerate(results.items[:3], 1):  # Show first 3 results in detail
        print(f"\n{'─'*80}")
        print(f"📌 RESULT #{idx}: {item.title}")
        print(f"{'─'*80}")
        
        # Get ALL attributes of the item
        print("\n🔧 ALL ATTRIBUTES:")
        for attr in dir(item):
            if not attr.startswith('_') and not callable(getattr(item, attr)):
                try:
                    value = getattr(item, attr)
                    if value is not None:
                        # Truncate long values
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        print(f"   {attr}: {value_str}")
                except:
                    pass
        
        # Specifically show important fields
        print("\n📋 IMPORTANT FIELDS:")
        print(f"   subjectId: {item.subjectId}")
        print(f"   title: {item.title}")
        print(f"   releaseDate: {item.releaseDate}")
        print(f"   imdbRatingValue: {item.imdbRatingValue}")
        print(f"   genre: {item.genre}")
        print(f"   hasResource: {item.hasResource}")
        print(f"   detailPath: {item.detailPath}")
        if item.cover:
            print(f"   cover.url: {item.cover.url}")
            print(f"   cover.width: {item.cover.width}")
            print(f"   cover.height: {item.cover.height}")
        
        # Check if there's a trailer
        if hasattr(item, 'trailer') and item.trailer:
            print(f"   trailer: {item.trailer}")

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Inception"
    asyncio.run(show_complete_search(query))
