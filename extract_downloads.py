import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def extract_downloads():
    session = Session()
    
    print("=" * 60)
    print("EXTRACTING DOWNLOAD LINKS FROM MOVIEBOX_API")
    print("=" * 60)
    
    # Search for War Machine
    print("\n1. Searching for 'War Machine'...")
    search = Search(session, query="War Machine", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    if not results.items:
        print("No results found")
        return
    
    movie = results.items[0]
    print(f"\n✅ Movie: {movie.title}")
    print(f"   SubjectId: {movie.subjectId}")
    
    # Get download URLs directly
    print("\n2. Fetching download URLs...")
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            print(f"\n✅ Found {len(download_data['downloads'])} download qualities:\n")
            for i, dl in enumerate(download_data['downloads'], 1):
                size_mb = round(int(dl.get('size', 0)) / 1024 / 1024, 2)
                print(f"{i}. Quality: {dl.get('resolution')}p")
                print(f"   Size: {size_mb} MB")
                print(f"   URL: {dl.get('url')}")
                print()
        else:
            print("❌ No downloads found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(extract_downloads())
