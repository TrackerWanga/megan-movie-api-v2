import asyncio
import json
import enum
import sys
import httpx

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.download import DownloadableSingleFilesDetail

# OMDb API Key (free, 1000 requests/day)
# Get your own at https://www.omdbapi.com/apikey.aspx
OMDB_API_KEY = "9b5d7e52"  # From your WhatsApp bot code
OMDB_URL = "http://www.omdbapi.com/"

async def search_omdb(title: str, year: int = None) -> dict:
    """Get IMDb ID and rich metadata from OMDb"""
    params = {"apikey": OMDB_API_KEY, "t": title, "plot": "short"}
    if year:
        params["y"] = year
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OMDB_URL, params=params)
            data = response.json()
            if data.get("Response") == "True":
                return data
        except Exception as e:
            print(f"   OMDb error: {e}")
    return None

async def search_moviebox(query: str):
    """Search movies using moviebox_api"""
    session = Session()
    search = Search(session, query=query)
    results = await search.get_content_model()
    return results.items[:5] if results.items else []

async def get_moviebox_downloads(item):
    """Get MP4 download URLs from moviebox_api"""
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, item)
        data = await downloads_obj.get_content()
        return data.get('downloads', [])
    except:
        return []

async def test_unified():
    print("=" * 80)
    print("🎬 UNIFIED MOVIE TEST - moviebox_api + OMDb + TMDB")
    print("=" * 80)
    
    query = input("\n📝 Enter movie name: ").strip()
    if not query:
        query = "Inception"
        print(f"   Using default: {query}")
    
    print("\n" + "=" * 80)
    print(f"🔍 SEARCHING FOR: {query}")
    print("=" * 80)
    
    # 1. Search using moviebox_api
    print("\n📀 1. moviebox_api SEARCH...")
    moviebox_results = await search_moviebox(query)
    
    if not moviebox_results:
        print("   ❌ No results from moviebox_api")
        return
    
    print(f"   ✅ Found {len(moviebox_results)} results\n")
    
    # Process each result
    for idx, item in enumerate(moviebox_results[:3], 1):
        print(f"\n{'='*60}")
        print(f"📌 RESULT {idx}: {item.title}")
        print(f"{'='*60}")
        
        # moviebox_api data
        print(f"\n📀 MOVIEBOX DATA:")
        print(f"   Title: {item.title}")
        print(f"   Year: {item.releaseDate.year if item.releaseDate else 'N/A'}")
        print(f"   Rating: {item.imdbRatingValue}")
        print(f"   Genres: {item.genre}")
        print(f"   DetailPath: {item.detailPath}")
        print(f"   SubjectId: {item.subjectId}")
        
        # 2. Get OMDb data
        print(f"\n🎬 OMDb DATA (for IMDb ID):")
        omdb_data = await search_omdb(item.title, item.releaseDate.year if item.releaseDate else None)
        
        if omdb_data:
            print(f"   ✅ Found on OMDb")
            print(f"   IMDb ID: {omdb_data.get('imdbID')}")
            print(f"   OMDb Rating: {omdb_data.get('imdbRating')}")
            print(f"   Director: {omdb_data.get('Director', 'N/A')[:50]}")
            print(f"   Plot: {omdb_data.get('Plot', 'N/A')[:100]}...")
            imdb_id = omdb_data.get('imdbID')
        else:
            print(f"   ❌ Not found on OMDb")
            imdb_id = None
        
        # 3. Get moviebox download URLs
        print(f"\n⬇️ MOVIEBOX DOWNLOAD URLs:")
        downloads = await get_moviebox_downloads(item)
        if downloads:
            for dl in downloads[:3]:
                size_mb = round(int(dl.get('size', 0)) / 1024 / 1024, 2)
                print(f"   ✅ {dl.get('resolution')}p: {size_mb} MB")
                print(f"      URL: {dl.get('url', 'N/A')[:80]}...")
        else:
            print(f"   ❌ No download URLs found")
        
        # 4. For vidsrc-api (would need imdb_id)
        if imdb_id:
            print(f"\n🎥 VIDSRC-API (would use IMDb ID: {imdb_id})")
            print(f"   Stream URL would be: https://vidsrc-api.onrender.com/vidsrc/{imdb_id}")
        else:
            print(f"\n🎥 VIDSRC-API: ❌ Cannot use - no IMDb ID")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_unified())
