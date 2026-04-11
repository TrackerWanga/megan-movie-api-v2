import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def check_downloads():
    session = Session()
    
    print("=" * 60)
    print("CHECKING DOWNLOAD AVAILABILITY")
    print("=" * 60)
    
    # Search for War Machine
    print("\n1. Searching for 'War Machine'...")
    search = Search(session, query="War Machine", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    if not results.items:
        print("No results found")
        return
    
    first = results.items[0]
    print(f"\n📌 Movie: {first.title}")
    print(f"   SubjectId: {first.subjectId}")
    print(f"   Has download flag: {first.hasResource}")
    
    # Try to get actual download URLs
    print("\n2. Fetching download URLs from moviebox_api...")
    try:
        downloads = DownloadableSingleFilesDetail(session, first)
        download_data = await downloads.get_content()
        
        if download_data and 'downloads' in download_data:
            print(f"   ✅ Found {len(download_data['downloads'])} downloads:")
            for dl in download_data['downloads']:
                size_mb = round(int(dl.get('size', 0)) / 1024 / 1024, 2)
                print(f"      - {dl.get('resolution')}p: {size_mb} MB")
        else:
            print("   ❌ No downloads found from moviebox_api")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check PRINCE API for downloads
    print("\n3. Checking PRINCE API for downloads...")
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://movieapi.princetechn.com/api/sources/{first.subjectId}")
            if response.status_code == 200:
                data = response.json()
                prince_downloads = [s for s in data.get('results', []) if s.get('type') == 'direct']
                print(f"   ✅ PRINCE has {len(prince_downloads)} direct downloads:")
                for dl in prince_downloads[:3]:
                    print(f"      - {dl.get('quality')}: {dl.get('provider')}")
            else:
                print(f"   ❌ PRINCE returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ PRINCE error: {e}")
    
    print("\n" + "=" * 60)

asyncio.run(check_downloads())
