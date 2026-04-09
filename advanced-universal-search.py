import enum
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session

class ContentType:
    ALL = 0
    MOVIES = 1
    TV_SERIES = 2
    ANIME = 3
    EDUCATION = 4
    MUSIC = 6

async def advanced_search(
    query="",
    content_type=ContentType.ALL,
    page=1,
    per_page=24
):
    """
    Advanced search with full control
    
    Args:
        query: Search term
        content_type: 0=all, 1=movies, 2=tv, 3=anime, 4=education, 6=music
        page: Page number
        per_page: Results per page
    """
    session = Session()
    
    print(f"\n{'='*100}")
    print(f"🔍 ADVANCED SEARCH")
    print(f"   Query: '{query}'")
    print(f"   Type: {content_type}")
    print(f"   Page: {page}")
    print(f"   Per Page: {per_page}")
    print('='*100)
    
    # Create search
    search = Search(session, query=query)
    
    # Get results
    results = await search.get_content_model()
    
    # Filter by type if specified
    if content_type != ContentType.ALL:
        filtered_items = [
            item for item in results.items 
            if item.subjectType == content_type
        ]
    else:
        filtered_items = results.items
    
    # Organize by type
    organized = {
        "movies": [],
        "tv_series": [],
        "anime": [],
        "education": [],
        "music": [],
        "other": []
    }
    
    for item in filtered_items:
        st = item.subjectType
        if st == 1:
            organized["movies"].append(item)
        elif st == 2:
            organized["tv_series"].append(item)
        elif st == 3:
            organized["anime"].append(item)
        elif st == 4:
            organized["education"].append(item)
        elif st == 6:
            organized["music"].append(item)
        else:
            organized["other"].append(item)
    
    # Print organized results
    print(f"\n📊 TOTAL RESULTS: {len(filtered_items)}")
    
    for category, items in organized.items():
        if items:
            print(f"\n{'─'*80}")
            print(f"🎬 {category.upper().replace('_', ' ')} ({len(items)} items)")
            print('─'*80)
            
            for i, item in enumerate(items[:5]):  # First 5
                print(f"\n   [{i+1}] {item.title}")
                print(f"       ID: {item.subjectId}")
                print(f"       Path: {item.detailPath}")
                
                if hasattr(item, 'releaseDate') and item.releaseDate:
                    print(f"       Year: {item.releaseDate.year}")
                if hasattr(item, 'genre') and item.genre:
                    print(f"       Genre: {item.genre}")
                if hasattr(item, 'imdbRatingValue') and item.imdbRatingValue:
                    print(f"       Rating: {item.imdbRatingValue}")
                if hasattr(item, 'duration') and item.duration:
                    mins = item.duration // 60
                    print(f"       Duration: {mins} min")
    
    # Pagination info
    pager = results.pager
    print(f"\n📄 PAGINATION:")
    print(f"   Current Page: {pager.page}")
    print(f"   Per Page: {pager.perPage}")
    print(f"   Has More: {pager.hasMore}")
    print(f"   Next Page: {pager.nextPage}")
    print(f"   Total Count: {pager.totalCount}")
    
    return {
        "items": filtered_items,
        "organized": organized,
        "pager": pager
    }

# Run multiple searches
async def main():
    # Search 1: Everything
    await advanced_search("action", ContentType.ALL)
    
    # Search 2: Only movies
    await advanced_search("comedy", ContentType.MOVIES)
    
    # Search 3: Only music
    await advanced_search("pharrell", ContentType.MUSIC)
    
    # Search 4: Only education
    await advanced_search("python", ContentType.EDUCATION)

asyncio.run(main())
