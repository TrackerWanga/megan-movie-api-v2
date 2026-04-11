import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import (
    DownloadableSingleFilesDetail,
    DownloadableMovieFilesDetail,
    MediaFileDownloader,
    DownloadableFilesMetadata,
    CaptionFileDownloader
)

async def test_all_methods():
    session = Session()
    
    print("=" * 80)
    print("🔍 TESTING ALL DOWNLOAD METHODS - AVATAR (2009)")
    print("=" * 80)
    
    # 1. Search for Avatar
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    if not results.items:
        print("❌ Movie not found")
        return
    
    movie = results.items[0]
    print(f"\n✅ Found: {movie.title}")
    print(f"   SubjectId: {movie.subjectId}")
    print(f"   DetailPath: {movie.detailPath}")
    
    # 2. Test get_absolute_url (from core)
    print("\n" + "=" * 80)
    print("📌 METHOD 1: get_absolute_url (from core)")
    print("=" * 80)
    try:
        from moviebox_api.v2.core import get_absolute_url
        absolute_url = get_absolute_url(movie.detailPath)
        print(f"✅ get_absolute_url: {absolute_url}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 3. Test DownloadableSingleFilesDetail
    print("\n" + "=" * 80)
    print("📌 METHOD 2: DownloadableSingleFilesDetail")
    print("=" * 80)
    try:
        single_dl = DownloadableSingleFilesDetail(session, movie)
        single_data = await single_dl.get_content()
        
        print(f"✅ Got data with keys: {list(single_data.keys()) if single_data else 'None'}")
        if single_data and 'downloads' in single_data:
            print(f"   Downloads found: {len(single_data['downloads'])}")
            for dl in single_data['downloads'][:2]:
                print(f"   - Quality: {dl.get('resolution')}p")
                print(f"     URL: {dl.get('url', 'N/A')[:80]}...")
                print(f"     Size: {dl.get('size', 'N/A')}")
        if single_data and 'captions' in single_data:
            print(f"   Captions found: {len(single_data['captions'])}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 4. Test DownloadableMovieFilesDetail
    print("\n" + "=" * 80)
    print("📌 METHOD 3: DownloadableMovieFilesDetail")
    print("=" * 80)
    try:
        movie_dl = DownloadableMovieFilesDetail(session, movie)
        movie_data = await movie_dl.get_content()
        
        print(f"✅ Got data with keys: {list(movie_data.keys()) if movie_data else 'None'}")
        if movie_data and 'downloads' in movie_data:
            print(f"   Downloads found: {len(movie_data['downloads'])}")
            for dl in movie_data['downloads'][:2]:
                print(f"   - Quality: {dl.get('resolution')}p")
                print(f"     URL: {dl.get('url', 'N/A')[:80]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 5. Test MediaFileDownloader
    print("\n" + "=" * 80)
    print("📌 METHOD 4: MediaFileDownloader")
    print("=" * 80)
    try:
        media_dl = MediaFileDownloader(session, movie, quality="1080p")
        print(f"✅ Created MediaFileDownloader")
        print(f"   Methods available: {[m for m in dir(media_dl) if not m.startswith('_')]}")
        
        # Check if it has a get_url or similar method
        if hasattr(media_dl, 'get_url'):
            url = await media_dl.get_url()
            print(f"   get_url(): {url[:100] if url else 'None'}...")
        if hasattr(media_dl, 'get_download_url'):
            url = media_dl.get_download_url()
            print(f"   get_download_url(): {url[:100] if url else 'None'}...")
        if hasattr(media_dl, 'url'):
            print(f"   url property: {media_dl.url[:100] if media_dl.url else 'None'}...")
            
        # Try to get content
        if hasattr(media_dl, 'get_content'):
            content = await media_dl.get_content()
            print(f"   get_content() returned: {type(content)}")
            if isinstance(content, dict):
                print(f"   Keys: {list(content.keys())}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 6. Test DownloadableFilesMetadata
    print("\n" + "=" * 80)
    print("📌 METHOD 5: DownloadableFilesMetadata")
    print("=" * 80)
    try:
        metadata = DownloadableFilesMetadata(session, movie)
        meta_data = await metadata.get_content()
        print(f"✅ Got metadata: {list(meta_data.keys()) if meta_data else 'None'}")
        if meta_data:
            print(json.dumps(meta_data, indent=2, default=str)[:500])
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 7. Test CaptionFileDownloader
    print("\n" + "=" * 80)
    print("📌 METHOD 6: CaptionFileDownloader")
    print("=" * 80)
    try:
        caption_dl = CaptionFileDownloader(session, movie)
        caption_data = await caption_dl.get_content()
        print(f"✅ Got captions: {len(caption_data) if caption_data else 0}")
        if caption_data:
            for cap in caption_data[:3]:
                print(f"   - {cap.get('lanName', 'Unknown')}: {cap.get('url', 'N/A')[:60]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 8. Test direct CDN URL with session headers
    print("\n" + "=" * 80)
    print("📌 METHOD 7: Direct CDN with Session Headers")
    print("=" * 80)
    try:
        # Get a raw URL first
        single_dl = DownloadableSingleFilesDetail(session, movie)
        single_data = await single_dl.get_content()
        if single_data and 'downloads' in single_data:
            raw_url = single_data['downloads'][0]['url']
            print(f"   Raw URL: {raw_url[:100]}...")
            
            # Try with session's client
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.head(raw_url)
                print(f"   Direct HEAD request: {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ URL works directly!")
                    print(f"   Content-Type: {response.headers.get('content-type')}")
                    print(f"   Content-Length: {response.headers.get('content-length')}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

asyncio.run(test_all_methods())
