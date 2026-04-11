import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def get_tool_downloads(title):
    session = Session()
    
    print(f"\n{'='*80}")
    print(f"🔍 FETCHING DOWNLOADS FOR: {title}")
    print(f"{'='*80}")
    
    # Search by title
    search = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    if not results.items:
        print(f"❌ Movie '{title}' not found")
        return
    
    # Get the first result
    movie = results.items[0]
    print(f"\n✅ Found: {movie.title}")
    print(f"   SubjectId: {movie.subjectId}")
    print(f"   Has download flag: {movie.hasResource}")
    
    # Try to get download URLs directly from moviebox_api
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            print(f"\n📥 DOWNLOAD URLS FROM MOVIEBOX_API TOOL:\n")
            for dl in download_data['downloads']:
                size_mb = round(int(dl.get('size', 0)) / 1024 / 1024, 2)
                print(f"Quality: {dl.get('resolution')}p")
                print(f"Size: {size_mb} MB")
                print(f"URL: {dl.get('url')}")
                print()
        else:
            print("\n❌ No downloads found in moviebox_api tool")
            
    except Exception as e:
        print(f"\n❌ Error getting downloads: {e}")

async def main():
    # Test with movies that should have downloads
    test_titles = [
        "War Machine",
        "Avatar",
        "Avatar: Fire and Ash",
        "Inception"
    ]
    
    for title in test_titles:
        await get_tool_downloads(title)

if __name__ == "__main__":
    asyncio.run(main())
