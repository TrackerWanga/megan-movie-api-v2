import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session, MovieDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def test_all_searches():
    print("=" * 80)
    print("🎬 TESTING MULTIPLE SEARCHES - FULL OUTPUT")
    print("=" * 80)
    
    session = Session()
    
    # Search terms to test
    searches = [
        ("Despicable Me 4", "movie"),
        ("One Piece", "anime/tv"),
        ("Inception", "movie"),
        ("Breaking Bad", "tv series"),
    ]
    
    for query, category in searches:
        print(f"\n{'=' * 80}")
        print(f"🔍 SEARCH: {query} ({category})")
        print("=" * 80)
        
        # 1. SEARCH RESULTS
        print(f"\n📋 SEARCH RESULTS:")
        print("-" * 50)
        
        search = Search(session, query=query)
        results = await search.get_content_model()
        
        print(f"Total found: {len(results.items)}")
        
        for i, item in enumerate(results.items[:3]):
            print(f"\n   [{i+1}] {item.title}")
            print(f"       Type: {item.subjectType}")
            print(f"       Year: {item.releaseDate.year if item.releaseDate else 'N/A'}")
            print(f"       Rating: {item.imdbRatingValue}")
            print(f"       DetailPath: {item.detailPath}")
            print(f"       Has Poster: {item.cover is not None}")
        
        # 2. DETAILS FOR FIRST RESULT
        if results.items:
            first = results.items[0]
            print(f"\n📽️ DETAILS FOR: {first.title}")
            print("-" * 50)
            
            try:
                details_obj = MovieDetails(session)
                detail_data = await details_obj.get_content(first.detailPath)
                
                subject = detail_data.get('subject', {})
                stars = detail_data.get('stars', [])
                trailer = subject.get('trailer', {}).get('videoAddress', {}).get('url')
                
                print(f"   Title: {subject.get('title')}")
                print(f"   Year: {subject.get('releaseDate', 'N/A')[:4]}")
                print(f"   Rating: {subject.get('imdbRatingValue', 'N/A')}")
                print(f"   Genres: {subject.get('genre', 'N/A')}")
                print(f"   Trailer: {trailer if trailer else 'No trailer'}")
                print(f"   Cast: {len(stars)} actors")
                if stars:
                    print(f"   Top Cast: {stars[0].get('name')} as {stars[0].get('character')}")
                
            except Exception as e:
                print(f"   ❌ Error getting details: {e}")
            
            # 3. DOWNLOAD URLS
            print(f"\n⬇️ DOWNLOAD URLS FOR: {first.title}")
            print("-" * 50)
            
            try:
                downloads_obj = DownloadableSingleFilesDetail(session, first)
                download_data = await downloads_obj.get_content()
                
                if download_data and 'downloads' in download_data:
                    print(f"   ✅ Found {len(download_data['downloads'])} qualities:")
                    for dl in download_data['downloads']:
                        size_mb = round(int(dl.get('size', 0)) / 1024 / 1024, 2)
                        print(f"      - {dl.get('resolution')}p: {size_mb} MB")
                        print(f"        URL: {dl.get('url', 'N/A')[:80]}...")
                else:
                    print("   ❌ No download links found")
                    
            except Exception as e:
                print(f"   ❌ Error getting downloads: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_searches())
