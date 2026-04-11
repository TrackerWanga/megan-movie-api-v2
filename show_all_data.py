import enum
import sys
import asyncio
import json

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session, MovieDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import SubjectType

async def show_all_data(subject_id):
    session = Session()
    
    print(f"\n{'='*70}")
    print(f"📀 COMPLETE DATA FOR SUBJECT ID: {subject_id}")
    print(f"{'='*70}")
    
    # First, search to get the item
    search = Search(session, query=subject_id, subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    if not results.items:
        print("No item found")
        return
    
    item = results.items[0]
    
    print(f"\n📌 BASIC INFO:")
    print(f"   Title: {item.title}")
    print(f"   SubjectId: {item.subjectId}")
    print(f"   DetailPath: {item.detailPath}")
    print(f"   Year: {item.releaseDate.year if item.releaseDate else 'N/A'}")
    print(f"   Rating: {item.imdbRatingValue}")
    print(f"   Genres: {item.genre}")
    print(f"   Has Resource: {item.hasResource}")
    
    # Get full details
    print(f"\n📌 FULL DETAILS (cast, trailer, etc.):")
    details = MovieDetails(session)
    full_data = await details.get_content(item.detailPath)
    
    subject = full_data.get('subject', {})
    print(f"   Description: {subject.get('description', 'N/A')[:100]}...")
    print(f"   Country: {subject.get('countryName', 'N/A')}")
    print(f"   Duration: {subject.get('duration', 0)} seconds")
    
    # Cast
    stars = full_data.get('stars', [])
    print(f"\n   CAST ({len(stars)} actors):")
    for star in stars[:5]:
        print(f"      - {star.get('name')} as {star.get('character')}")
    
    # Trailer
    trailer = subject.get('trailer', {})
    video = trailer.get('videoAddress', {})
    if video:
        print(f"\n   TRAILER: {video.get('url', 'N/A')}")
    
    # Poster
    cover = subject.get('cover', {})
    if cover:
        print(f"\n   POSTER: {cover.get('url', 'N/A')}")
        print(f"      Dimensions: {cover.get('width')}x{cover.get('height')}")
    
    # Get download URLs
    print(f"\n📌 DOWNLOAD URLS:")
    try:
        downloads = DownloadableSingleFilesDetail(session, item)
        download_data = await downloads.get_content()
        
        if download_data and 'downloads' in download_data:
            for dl in download_data['downloads']:
                size_mb = round(int(dl.get('size', 0)) / 1024 / 1024, 2)
                print(f"   {dl.get('resolution')}p: {size_mb} MB")
                print(f"      URL: {dl.get('url', 'N/A')[:80]}...")
        else:
            print("   No download URLs available")
    except Exception as e:
        print(f"   Error getting downloads: {e}")
    
    # Check PRINCE API for comparison
    print(f"\n📌 PRINCE API SOURCES (for comparison):")
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://movieapi.princetechn.com/api/sources/{subject_id}")
            if response.status_code == 200:
                prince_data = response.json()
                prince_downloads = [s for s in prince_data.get('results', []) if s.get('type') == 'direct']
                print(f"   PRINCE direct downloads: {len(prince_downloads)}")
                for dl in prince_downloads[:2]:
                    print(f"      {dl.get('quality')}: available")
            else:
                print(f"   PRINCE API returned: {response.status_code}")
    except Exception as e:
        print(f"   PRINCE error: {e}")

async def main():
    if len(sys.argv) > 1:
        subject_id = sys.argv[1]
    else:
        subject_id = input("Enter Subject ID: ").strip()
        if not subject_id:
            # Use a known subjectId from your search
            subject_id = "8035128247149024680"  # War Machine
    
    await show_all_data(subject_id)

if __name__ == "__main__":
    asyncio.run(main())
