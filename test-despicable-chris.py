import enum
import sys
import asyncio
import json
from datetime import datetime

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session, MovieDetails, TVSeriesDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail, DownloadableTVSeriesFilesDetail
from moviebox_api.v2.core import Homepage

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    if not size_bytes:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def print_json(data, title="JSON Data"):
    """Pretty print JSON data"""
    print(f"\n📄 {title}:")
    print(json.dumps(data, indent=2, default=str)[:2000] + "..." if len(json.dumps(data, default=str)) > 2000 else json.dumps(data, indent=2, default=str))

async def test_movie_search():
    """Search for Despicable Me 4"""
    print("=" * 80)
    print("🎬 TEST 1: SEARCHING MOVIE - 'Despicable Me 4'")
    print("=" * 80)
    
    session = Session()
    search = Search(session, query="despicable me 4")
    results = await search.get_content_model()
    
    print(f"\n✅ Found {len(results.items)} total results")
    
    # Filter for movies only (subjectType = 1)
    movies = [r for r in results.items if r.subjectType == 1]
    print(f"🎥 Movies: {len(movies)}")
    
    if not movies:
        print("❌ No movies found!")
        return None
    
    # Get first movie result
    movie = movies[0]
    print(f"\n📌 FIRST MOVIE RESULT:")
    print(f"   Title: {movie.title}")
    print(f"   Subject ID: {movie.subjectId}")
    print(f"   Detail Path: {movie.detailPath}")
    print(f"   Subject Type: {movie.subjectType}")
    print(f"   Genre: {movie.genre}")
    print(f"   Rating: {movie.imdbRatingValue}")
    print(f"   Year: {movie.releaseDate.year if movie.releaseDate else 'N/A'}")
    print(f"   Poster URL: {movie.cover[:60]}..." if movie.cover else "   Poster: N/A")
    
    return movie

async def test_movie_details(movie_item):
    """Get full details for Despicable Me 4"""
    print("\n" + "=" * 80)
    print("📽️ TEST 2: MOVIE DETAILS - 'Despicable Me 4'")
    print("=" * 80)
    
    session = Session()
    details = MovieDetails(session)
    detail_data = await details.get_content(movie_item.detailPath)
    
    subject = detail_data.get('subject', {})
    stars = detail_data.get('stars', [])
    resource = detail_data.get('resource', {})
    trailer = subject.get('trailer', {}).get('videoAddress', {}).get('url')
    
    print(f"\n🎬 Movie Information:")
    print(f"   Title: {subject.get('title')}")
    print(f"   Original Title: {subject.get('titleOriginal', 'N/A')}")
    print(f"   Year: {subject.get('year', 'N/A')}")
    print(f"   Rating: {subject.get('imdbRating', 'N/A')}")
    print(f"   Duration: {subject.get('duration', 'N/A')} minutes")
    print(f"   Description: {subject.get('description', 'N/A')[:150]}...")
    
    print(f"\n🎭 Cast ({len(stars)} actors):")
    for star in stars[:5]:
        print(f"   • {star.get('name')} as {star.get('characterName', 'N/A')}")
    if len(stars) > 5:
        print(f"   ... and {len(stars) - 5} more")
    
    print(f"\n🎞️ Trailer: {trailer if trailer else 'N/A'}")
    
    print(f"\n📦 Resource Info:")
    print(f"   Seasons: {len(resource.get('seasons', []))}")
    print(f"   Episodes: {resource.get('episodeCount', 'N/A')}")
    
    return detail_data

async def test_movie_downloads(movie_item):
    """Get download links for Despicable Me 4"""
    print("\n" + "=" * 80)
    print("⬇️ TEST 3: MOVIE DOWNLOAD LINKS - 'Despicable Me 4'")
    print("=" * 80)
    
    session = Session()
    download_obj = DownloadableSingleFilesDetail(session, movie_item)
    download_data = await download_obj.get_content()
    
    if not download_data:
        print("❌ No download data returned!")
        return None
    
    downloads = download_data.get('downloads', [])
    captions = download_data.get('captions', [])
    limited = download_data.get('limited', False)
    
    print(f"\n💾 Download Links ({len(downloads)} qualities):")
    print("-" * 50)
    
    for i, dl in enumerate(downloads, 1):
        size_str = format_size(dl.get('size', 0))
        print(f"\n   [{i}] Quality: {dl.get('resolution')}p")
        print(f"       Size: {size_str}")
        print(f"       URL: {dl.get('url', 'N/A')[:80]}...")
        print(f"       Format: {dl.get('format', 'N/A')}")
        print(f"       Codec: {dl.get('codec', 'N/A')}")
    
    print(f"\n📝 Subtitles ({len(captions)} languages):")
    print("-" * 50)
    
    for cap in captions:
        print(f"   • {cap.get('lanName')} ({cap.get('lan')}) - {cap.get('url', 'N/A')[:60]}...")
    
    if limited:
        print("\n⚠️  WARNING: Download is limited/restricted!")
    
    return download_data

async def test_tv_search():
    """Search for Everybody Hates Chris"""
    print("\n" + "=" * 80)
    print("📺 TEST 4: SEARCHING TV SERIES - 'Everybody Hates Chris'")
    print("=" * 80)
    
    session = Session()
    search = Search(session, query="everybody hates chris")
    results = await search.get_content_model()
    
    print(f"\n✅ Found {len(results.items)} total results")
    
    # Filter for TV series (subjectType = 2)
    tv_shows = [r for r in results.items if r.subjectType == 2]
    print(f"📺 TV Series: {len(tv_shows)}")
    
    if not tv_shows:
        print("❌ No TV series found! Trying all results...")
        tv_shows = results.items
    
    if not tv_shows:
        return None
    
    # Get first TV result
    show = tv_shows[0]
    print(f"\n📌 FIRST TV RESULT:")
    print(f"   Title: {show.title}")
    print(f"   Subject ID: {show.subjectId}")
    print(f"   Detail Path: {show.detailPath}")
    print(f"   Subject Type: {show.subjectType}")
    print(f"   Genre: {show.genre}")
    print(f"   Rating: {show.imdbRatingValue}")
    print(f"   Year: {show.releaseDate.year if show.releaseDate else 'N/A'}")
    
    return show

async def test_tv_details(tv_item):
    """Get full details for Everybody Hates Chris"""
    print("\n" + "=" * 80)
    print("📺 TEST 5: TV SERIES DETAILS - 'Everybody Hates Chris'")
    print("=" * 80)
    
    session = Session()
    details = TVSeriesDetails(session)
    detail_data = await details.get_content(tv_item.detailPath)
    
    subject = detail_data.get('subject', {})
    stars = detail_data.get('stars', [])
    resource = detail_data.get('resource', {})
    seasons = resource.get('seasons', [])
    
    print(f"\n📺 Series Information:")
    print(f"   Title: {subject.get('title')}")
    print(f"   Original Title: {subject.get('titleOriginal', 'N/A')}")
    print(f"   Year: {subject.get('year', 'N/A')}")
    print(f"   Rating: {subject.get('imdbRating', 'N/A')}")
    print(f"   Description: {subject.get('description', 'N/A')[:150]}...")
    
    print(f"\n🎭 Cast ({len(stars)} actors):")
    for star in stars[:5]:
        print(f"   • {star.get('name')} as {star.get('characterName', 'N/A')}")
    
    print(f"\n📂 Seasons ({len(seasons)}):")
    for season in seasons:
        print(f"   • Season {season.get('seasonNumber')}: {season.get('episodeCount')} episodes")
        # Show first few episodes
        episodes = season.get('episodes', [])
        for ep in episodes[:3]:
            print(f"       - Ep {ep.get('episodeNumber')}: {ep.get('title', 'N/A')}")
        if len(episodes) > 3:
            print(f"       ... and {len(episodes) - 3} more episodes")
    
    return detail_data

async def test_tv_downloads(tv_item):
    """Get download links for Everybody Hates Chris episodes"""
    print("\n" + "=" * 80)
    print("⬇️ TEST 6: TV SERIES DOWNLOAD LINKS - 'Everybody Hates Chris'")
    print("=" * 80)
    
    session = Session()
    download_obj = DownloadableTVSeriesFilesDetail(session, tv_item)
    download_data = await download_obj.get_content()
    
    if not download_data:
        print("❌ No download data returned!")
        return None
    
    downloads = download_data.get('downloads', [])
    captions = download_data.get('captions', [])
    
    print(f"\n💾 Download Links ({len(downloads)} items):")
    print("-" * 50)
    
    # Group by season/episode if possible
    for i, dl in enumerate(downloads[:5], 1):  # Show first 5 only
        size_str = format_size(dl.get('size', 0))
        print(f"\n   [{i}] {dl.get('title', 'Unknown')}")
        print(f"       Quality: {dl.get('resolution')}p")
        print(f"       Size: {size_str}")
        print(f"       URL: {dl.get('url', 'N/A')[:80]}...")
    
    if len(downloads) > 5:
        print(f"\n   ... and {len(downloads) - 5} more download items")
    
    print(f"\n📝 Subtitles ({len(captions)} languages):")
    for cap in captions[:5]:
        print(f"   • {cap.get('lanName')} ({cap.get('lan')})")
    
    return download_data

async def test_homepage():
    """Test homepage content"""
    print("\n" + "=" * 80)
    print("🏠 TEST 7: HOMEPAGE CONTENT")
    print("=" * 80)
    
    session = Session()
    homepage = Homepage(session)
    home_data = await homepage.get_content()
    
    # Try to get model version
    try:
        home_model = await homepage.get_content_model()
        print(f"\n✅ Homepage model retrieved")
        print(f"   Type: {type(home_model)}")
        
        if hasattr(home_model, 'platformList'):
            print(f"   Platforms: {len(home_model.platformList)}")
        if hasattr(home_model, 'operatingList'):
            print(f"   Operating items: {len(home_model.operatingList)}")
    except Exception as e:
        print(f"\n⚠️  Model error: {e}")
        print(f"   Raw data keys: {list(home_data.keys())}")

async def main():
    """Run all tests"""
    print("\n" + "🎬" * 40)
    print("🎬 MOVIEBOX-API V2 - COMPREHENSIVE CONTENT TEST")
    print("🎬" * 40)
    print(f"\n⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test Movie: Despicable Me 4
        movie_item = await test_movie_search()
        if movie_item:
            await test_movie_details(movie_item)
            await test_movie_downloads(movie_item)
        
        # Test TV Series: Everybody Hates Chris
        tv_item = await test_tv_search()
        if tv_item:
            await test_tv_details(tv_item)
            await test_tv_downloads(tv_item)
        
        # Test Homepage
        await test_homepage()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\n⏰ Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
