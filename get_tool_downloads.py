import enum
import sys
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def get_tool_downloads(subject_id, title):
    session = Session()
    
    print(f"\n{'='*80}")
    print(f"🔍 FETCHING DOWNLOADS FOR: {title}")
    print(f"SubjectId: {subject_id}")
    print(f"{'='*80}")
    
    # Create a search to get the movie item
    search = Search(session, query=subject_id, subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    if not results.items:
        print("❌ Movie not found")
        return
    
    movie = results.items[0]
    print(f"\n✅ Found: {movie.title}")
    
    # Try to get download URLs directly
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            print(f"\n📥 DOWNLOAD URLS FROM TOOL:\n")
            for dl in download_data['downloads']:
                size_mb = round(int(dl.get('size', 0)) / 1024 / 1024, 2)
                print(f"Quality: {dl.get('resolution')}p")
                print(f"Size: {size_mb} MB")
                print(f"URL: {dl.get('url')}")
                print()
        else:
            print("❌ No downloads found in tool")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    # Test with subjectIds that worked with PRINCE
    test_cases = [
        ("8035128247149024680", "War Machine"),
        ("8906247916759695608", "Avatar"),
        ("74738785354956752", "Avatar: Fire and Ash"),
    ]
    
    for subject_id, title in test_cases:
        await get_tool_downloads(subject_id, title)

if __name__ == "__main__":
    asyncio.run(main())
