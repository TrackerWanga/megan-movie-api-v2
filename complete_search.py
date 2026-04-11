import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

async def complete_search(query, search_type="movie", limit=10):
    """
    Complete search with Megan IDs
    search_type: "movie", "tv", "anime", "music", "education", "all"
    """
    session = Session()
    
    # Map search types to SubjectType
    type_map = {
        "movie": SubjectType.MOVIES,
        "tv": SubjectType.TV_SERIES,
        "anime": SubjectType.ANIME,
        "music": SubjectType.MUSIC,
        "education": SubjectType.EDUCATION,
        "all": SubjectType.MOVIES  # Will combine later
    }
    
    subject_type = type_map.get(search_type, SubjectType.MOVIES)
    
    print(f"\n{'='*80}")
    print(f"🔍 MEGAN SEARCH: '{query}' (Type: {search_type})")
    print(f"{'='*80}")
    
    try:
        search = Search(session, query=query, subject_type=subject_type)
        results = await search.get_content_model()
        
        print(f"\n📊 Total results: {len(results.items)}")
        
        # Build response with Megan IDs
        search_results = []
        
        for idx, item in enumerate(results.items[:limit], 1):
            # Generate Megan ID
            megan_id = f"megan-{item.subjectId}"
            
            # Determine content type
            content_type = "unknown"
            if item.subjectType == SubjectType.MOVIES:
                content_type = "movie"
            elif item.subjectType == SubjectType.TV_SERIES:
                content_type = "tv_series"
            elif item.subjectType == SubjectType.ANIME:
                content_type = "anime"
            elif item.subjectType == SubjectType.MUSIC:
                content_type = "music"
            elif item.subjectType == SubjectType.EDUCATION:
                content_type = "education"
            
            # Get year
            year = item.releaseDate.year if item.releaseDate else None
            
            # Get poster URL
            poster_url = str(item.cover.url) if item.cover else None
            
            result = {
                "rank": idx,
                "megan_id": megan_id,
                "title": item.title,
                "year": year,
                "type": content_type,
                "type_id": item.subjectType.value if hasattr(item.subjectType, 'value') else item.subjectType,
                "rating": item.imdbRatingValue,
                "genres": item.genre if isinstance(item.genre, list) else [item.genre] if item.genre else [],
                "poster": poster_url,
                "detail_path": item.detailPath,
                "subject_id": str(item.subjectId),
                "has_download": item.hasResource,
                "duration_minutes": item.duration // 60 if item.duration else None,
                "country": item.countryName if hasattr(item, 'countryName') else None
            }
            
            search_results.append(result)
            
            # Print nicely
            print(f"\n{idx}. [{content_type.upper()}] {item.title} ({year})")
            print(f"   Megan ID: {megan_id}")
            print(f"   Rating: {item.imdbRatingValue}")
            print(f"   Genres: {item.genre}")
            print(f"   Download available: {item.hasResource}")
            print(f"   Poster: {poster_url[:80]}..." if poster_url else "   Poster: None")
        
        # Return as JSON
        return {
            "success": True,
            "query": query,
            "type": search_type,
            "total": len(search_results),
            "results": search_results
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

async def main():
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("Enter search term: ").strip()
        if not query:
            query = "inception"
    
    # Search all types
    result = await complete_search(query, "movie", 10)
    
    # Print as JSON
    print("\n" + "="*80)
    print("📋 JSON OUTPUT:")
    print("="*80)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
