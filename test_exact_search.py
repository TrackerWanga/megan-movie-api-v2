import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

async def search_exact(query):
    session = Session()
    search = Search(session, query=query, subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    print(f"\n{'='*60}")
    print(f"🔍 SEARCH RESULTS FOR: '{query}'")
    print(f"{'='*60}")
    
    # Find exact matches first
    exact_matches = []
    other_matches = []
    
    for item in results.items:
        if item.title.lower() == query.lower():
            exact_matches.append(item)
        else:
            other_matches.append(item)
    
    print(f"\n📌 EXACT MATCHES ({len(exact_matches)}):")
    for item in exact_matches:
        year = item.releaseDate.year if item.releaseDate else "N/A"
        print(f"   ✅ {item.title} ({year}) - SubjectId: {item.subjectId}")
    
    print(f"\n📌 OTHER RESULTS ({len(other_matches)}):")
    for item in other_matches[:5]:
        year = item.releaseDate.year if item.releaseDate else "N/A"
        print(f"   📹 {item.title} ({year}) - SubjectId: {item.subjectId}")
    
    # Return the best match (exact if exists, otherwise first)
    best_match = exact_matches[0] if exact_matches else results.items[0]
    print(f"\n🎯 BEST MATCH: {best_match.title} (SubjectId: {best_match.subjectId})")
    
    return best_match

async def main():
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("Enter movie name: ").strip()
        if not query:
            query = "inception"
    
    await search_exact(query)

if __name__ == "__main__":
    asyncio.run(main())
