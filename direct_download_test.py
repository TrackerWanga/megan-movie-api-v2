import enum
import asyncio

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Session
from moviebox_api.v2.download import DownloadableSingleFilesDetail

async def test_downloads():
    session = Session()
    
    # Create a mock item with just the subjectId
    # This bypasses the search that's timing out
    class MockItem:
        def __init__(self, subject_id):
            self.subjectId = subject_id
            self.title = "War Machine"
    
    movie = MockItem("8035128247149024680")
    
    print("=" * 60)
    print("TESTING DIRECT DOWNLOAD FETCH")
    print("=" * 60)
    
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            print(f"\n✅ Found {len(download_data['downloads'])} downloads:\n")
            for dl in download_data['downloads']:
                size_mb = round(int(dl.get('size', 0)) / 1024 / 1024, 2)
                print(f"   Quality: {dl.get('resolution')}p")
                print(f"   Size: {size_mb} MB")
                print(f"   URL: {dl.get('url')[:100]}...")
                print()
        else:
            print("❌ No downloads found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(test_downloads())
