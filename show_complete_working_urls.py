import enum
import sys
import asyncio
from urllib.parse import quote

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

print("=" * 100)
print("🎯 COMPLETE WORKING DOWNLOAD URLS (WITH SESSION CONTEXT)")
print("=" * 100)

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def show_working_urls():
    session = Session()
    
    # Search and get movie
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    movie = results.items[0]
    
    # Get downloads
    dl = DownloadableSingleFilesDetail(session, movie)
    dl_data = await dl.get_content()
    
    print(f"\n📀 Movie: {movie.title}")
    print(f"   SubjectId: {movie.subjectId}")
    print(f"\n🍪 Session has internal client: {hasattr(session, '_client')}")
    
    # Show all download URLs
    print("\n" + "=" * 100)
    print("📥 COMPLETE DOWNLOAD URLS (WORKING WITH SESSION):")
    print("=" * 100)
    
    for i, download in enumerate(dl_data['downloads'], 1):
        quality = download.get('resolution')
        size_bytes = download.get('size', 0)
        size_mb = round(int(size_bytes) / 1024 / 1024, 2)
        raw_url = download.get('url')
        
        print(f"\n{i}. QUALITY: {quality}p")
        print(f"   Size: {size_mb} MB ({size_bytes} bytes)")
        print(f"   Format: {download.get('format')}")
        print(f"\n   📎 RAW URL (works with session):")
        print(f"   {raw_url}")
        
        # Show encoded version for proxy
        encoded = quote(raw_url, safe='')
        print(f"\n   🔗 PROXIED URL (should work if session is maintained):")
        print(f"   https://movieapi.megan.qzz.io/api/dl?url={encoded}&title=Avatar&quality={quality}p")
        
        # Test if the raw URL works with curl (it won't - needs session)
        print(f"\n   ⚠️ Note: This URL only works with the MovieBox session context!")
    
    # Show session headers that make it work
    print("\n" + "=" * 100)
    print("🔐 SESSION CONTEXT (What makes the URLs work):")
    print("=" * 100)
    
    if hasattr(session, '_client'):
        client = session._client
        if hasattr(client, 'headers'):
            print("\n📋 Headers from session client:")
            for key, value in client.headers.items():
                print(f"   {key}: {value}")
        
        if hasattr(client, 'cookies'):
            print("\n🍪 Cookies from session client:")
            for key, value in client.cookies.items():
                print(f"   {key}: {value[:50]}..." if len(str(value)) > 50 else f"   {key}: {value}")

asyncio.run(show_working_urls())
