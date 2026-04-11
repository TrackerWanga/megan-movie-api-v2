import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

print("=" * 80)
print("🎯 GETTING ACTUAL WORKING DOWNLOAD URL FROM TOOL")
print("=" * 80)

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def get_working_url():
    session = Session()
    
    # 1. Search for Avatar
    print("\n🔍 Searching for Avatar...")
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    movie = results.items[0]
    
    print(f"✅ Found: {movie.title}")
    print(f"   SubjectId: {movie.subjectId}")
    print(f"   DetailPath: {movie.detailPath}")
    
    # 2. Get download info using DownloadableSingleFilesDetail
    print("\n📥 Getting download info...")
    dl = DownloadableSingleFilesDetail(session, movie)
    dl_data = await dl.get_content()
    
    print(f"✅ Got download data")
    print(f"   Available qualities: {len(dl_data.get('downloads', []))}")
    
    # 3. Show ALL download URLs with their parameters
    print("\n" + "=" * 80)
    print("📎 COMPLETE DOWNLOAD URLS FROM TOOL:")
    print("=" * 80)
    
    for i, download in enumerate(dl_data.get('downloads', []), 1):
        print(f"\n{i}. QUALITY: {download.get('resolution')}p")
        print(f"   Size: {download.get('size')} bytes")
        print(f"   Format: {download.get('format')}")
        print(f"   URL: {download.get('url')}")
        
    # 4. Check if there's any other URL format
    print("\n" + "=" * 80)
    print("🔍 CHECKING FOR ALTERNATIVE URL FORMATS:")
    print("=" * 80)
    
    # Check all keys in download data
    print(f"\nAll keys in download data: {list(dl_data.keys())}")
    
    # Check if there's a stream URL
    if 'stream_url' in dl_data:
        print(f"\n✅ Found stream_url: {dl_data.get('stream_url')}")
    
    # Check each download for additional URL fields
    for download in dl_data.get('downloads', []):
        for key in download.keys():
            if 'url' in key.lower():
                print(f"   {key}: {download.get(key)[:100]}...")
    
    # 5. Try to get the session cookies/headers that might make it work
    print("\n" + "=" * 80)
    print("🍪 SESSION COOKIES/HEADERS (What makes it work):")
    print("=" * 80)
    
    if hasattr(session, 'cookies'):
        print(f"\nCookies: {session.cookies}")
    
    if hasattr(session, 'headers'):
        print(f"\nHeaders:")
        for key, value in session.headers.items():
            print(f"   {key}: {value}")
    
    # 6. Try direct request with session
    print("\n" + "=" * 80)
    print("🧪 TESTING DIRECT REQUEST WITH SESSION:")
    print("=" * 80)
    
    import httpx
    
    first_url = dl_data['downloads'][0]['url']
    print(f"\nTesting URL: {first_url[:100]}...")
    
    # Try with session's client
    if hasattr(session, '_client'):
        print("✅ Session has internal HTTP client")
        try:
            response = await session._client.head(first_url)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ URL WORKS with session client!")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {response.headers.get('content-length')}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # 7. Try to construct a working URL
    print("\n" + "=" * 80)
    print("🔧 CONSTRUCTING WORKING URL:")
    print("=" * 80)
    
    # The pattern from Prince that works
    prince_pattern = f"https://movieapi.princetechn.com/api/dl?url={first_url.replace('?', '%3F').replace('=', '%3D').replace('&', '%26')}"
    print(f"\nPrince-style URL:")
    print(f"   {prince_pattern[:150]}...")
    
    # Your pattern
    your_pattern = f"https://movieapi.megan.qzz.io/api/dl?url={first_url.replace('?', '%3F').replace('=', '%3D').replace('&', '%26')}&title=Avatar&quality={dl_data['downloads'][0].get('resolution')}p"
    print(f"\nYour-style URL:")
    print(f"   {your_pattern[:150]}...")

asyncio.run(get_working_url())
