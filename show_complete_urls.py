import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def show_all_urls():
    session = Session()
    
    print("=" * 100)
    print("🔗 COMPLETE DOWNLOAD URLS FOR AVATAR (2009)")
    print("=" * 100)
    
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    movie = results.items[0]
    
    print(f"\n📀 Movie: {movie.title}")
    print(f"   SubjectId: {movie.subjectId}")
    print(f"   DetailPath: {movie.detailPath}")
    
    # Get absolute URL
    from moviebox_api.v2.core import get_absolute_url
    absolute_url = get_absolute_url(movie.detailPath)
    print(f"\n🌐 get_absolute_url():")
    print(f"   {absolute_url}")
    
    # Get all download URLs
    single_dl = DownloadableSingleFilesDetail(session, movie)
    single_data = await single_dl.get_content()
    
    print(f"\n📥 DOWNLOAD URLS (with full parameters):")
    print("=" * 100)
    
    for i, dl in enumerate(single_data['downloads'], 1):
        quality = dl.get('resolution')
        size_bytes = dl.get('size', 0)
        size_mb = round(int(size_bytes) / 1024 / 1024, 2)
        url = dl.get('url', '')
        
        print(f"\n{i}. QUALITY: {quality}p")
        print(f"   Size: {size_mb} MB ({size_bytes} bytes)")
        print(f"   Format: {dl.get('format', 'mp4')}")
        print(f"   Codec: {dl.get('codec', 'h264')}")
        print(f"\n   📎 FULL URL:")
        print(f"   {url}")
        print(f"\n   🔍 URL COMPONENTS:")
        if '?' in url:
            base, params = url.split('?', 1)
            print(f"      Base: {base}")
            for param in params.split('&'):
                key, value = param.split('=', 1)
                print(f"      {key}: {value}")
    
    print("\n" + "=" * 100)
    print("📝 SUBTITLE URLS:")
    print("=" * 100)
    
    for cap in single_data.get('captions', [])[:5]:
        print(f"\n   Language: {cap.get('lanName')} ({cap.get('lan')})")
        print(f"   URL: {cap.get('url')}")

asyncio.run(show_all_urls())
