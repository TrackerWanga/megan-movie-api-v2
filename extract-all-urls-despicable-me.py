import enum
import sys
import asyncio
import json
from datetime import datetime

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session, MovieDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import Homepage

print("=" * 100)
print("🔍 EXTRACTING EVERY SINGLE URL FOR DESPICABLE ME 4")
print("=" * 100)
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

all_urls_found = []

def log_url(url_type, url, extra_info=""):
    """Log every URL found"""
    if url and isinstance(url, str) and url.startswith('http'):
        all_urls_found.append({
            'type': url_type,
            'url': url,
            'info': extra_info
        })
        print(f"\n🌐 [{url_type}]")
        print(f"   URL: {url}")
        if extra_info:
            print(f"   INFO: {extra_info}")
        return True
    return False

async def extract_everything():
    session = Session()
    
    # 1. SEARCH
    print("\n" + "=" * 100)
    print("STEP 1: SEARCH RESULTS")
    print("=" * 100)
    
    search = Search(session, query="despicable me 4")
    search_results = await search.get_content()
    search_model = await search.get_content_model()
    
    print(f"\n📊 Raw Search Results:")
    print(json.dumps(search_results, indent=2, default=str))
    
    # Find the movie
    movies = [item for item in search_model.items if item.subjectType == 1]
    if not movies:
        print("❌ No movies found!")
        return
    
    movie = movies[0]
    print(f"\n🎬 Found Movie: {movie.title}")
    print(f"   Subject ID: {movie.subjectId}")
    print(f"   Detail Path: {movie.detailPath}")
    
    # Extract all URLs from search result
    print("\n" + "-" * 80)
    print("URLS FROM SEARCH RESULT:")
    print("-" * 80)
    
    # Cover/poster URL
    if hasattr(movie, 'cover') and movie.cover:
        cover_data = movie.cover
        if hasattr(cover_data, 'url'):
            log_url("POSTER/COVER", str(cover_data.url), f"Resolution: {cover_data.width}x{cover_data.height}, Format: {cover_data.format}")
        if hasattr(cover_data, 'thumbnail') and cover_data.thumbnail:
            log_url("POSTER THUMBNAIL", cover_data.thumbnail, "Thumbnail version")
    
    # Stills/backdrops
    if hasattr(movie, 'stills') and movie.stills:
        stills_data = movie.stills
        if hasattr(stills_data, 'url'):
            log_url("BACKDROP/STILL", str(stills_data.url), f"Resolution: {stills_data.width}x{stills_data.height}")
    
    # Trailer from search
    if hasattr(movie, 'trailer') and movie.trailer:
        trailer_data = movie.trailer
        if isinstance(trailer_data, dict):
            if 'url' in trailer_data:
                log_url("TRAILER (from search)", trailer_data['url'], "Direct URL")
            if 'videoAddress' in trailer_data and isinstance(trailer_data['videoAddress'], dict):
                vid_addr = trailer_data['videoAddress']
                if 'url' in vid_addr:
                    log_url("TRAILER VIDEO", vid_addr['url'], f"Duration: {vid_addr.get('duration', 'N/A')}s, Quality: {vid_addr.get('definition', 'N/A')}")
    
    # 2. MOVIE DETAILS
    print("\n" + "=" * 100)
    print("STEP 2: FULL MOVIE DETAILS")
    print("=" * 100)
    
    details = MovieDetails(session)
    detail_data = await details.get_content(movie.detailPath)
    
    print(f"\n📋 Full Detail Data Structure:")
    print(json.dumps(detail_data, indent=2, default=str))
    
    # Extract subject info
    subject = detail_data.get('subject', {})
    resource = detail_data.get('resource', {})
    stars = detail_data.get('stars', [])
    
    print("\n" + "-" * 80)
    print("URLS FROM MOVIE DETAILS:")
    print("-" * 80)
    
    # Subject cover/poster
    if 'cover' in subject and subject['cover']:
        cover = subject['cover']
        if isinstance(cover, dict):
            if 'url' in cover:
                log_url("SUBJECT COVER", cover['url'], f"Size: {cover.get('size', 'N/A')} bytes, {cover.get('width')}x{cover.get('height')}")
            if 'thumbnail' in cover and cover['thumbnail']:
                log_url("SUBJECT COVER THUMBNAIL", cover['thumbnail'], "Thumbnail")
    
    # Trailer details
    if 'trailer' in subject and subject['trailer']:
        trailer = subject['trailer']
        print(f"\n📹 Trailer Data: {json.dumps(trailer, indent=2, default=str)}")
        
        if isinstance(trailer, dict):
            # Cover image for trailer
            if 'cover' in trailer and trailer['cover']:
                tr_cover = trailer['cover']
                if isinstance(tr_cover, dict) and 'url' in tr_cover:
                    log_url("TRAILER COVER/THUMBNAIL", tr_cover['url'], f"Trailer preview image {tr_cover.get('width')}x{tr_cover.get('height')}")
            
            # Video address
            if 'videoAddress' in trailer and trailer['videoAddress']:
                vid_addr = trailer['videoAddress']
                if isinstance(vid_addr, dict):
                    if 'url' in vid_addr:
                        info = f"Duration: {vid_addr.get('duration', 'N/A')}s, {vid_addr.get('width')}x{vid_addr.get('height')}"
                        log_url("TRAILER VIDEO FILE", vid_addr['url'], info)
                    if 'videoId' in vid_addr:
                        print(f"\n   Video ID: {vid_addr['videoId']}")
    
    # Stars/actors images
    if stars:
        print(f"\n🎭 Processing {len(stars)} cast members...")
        for i, star in enumerate(stars[:10]):  # First 10 actors
            if isinstance(star, dict):
                if 'avatarUrl' in star and star['avatarUrl']:
                    log_url(f"ACTOR PHOTO [{star.get('name', 'Unknown')}]", star['avatarUrl'], f"Character: {star.get('character', 'N/A')}")
                if 'detailPath' in star:
                    print(f"   Actor detail path: {star['detailPath']}")
    
    # 3. DOWNLOAD URLS
    print("\n" + "=" * 100)
    print("STEP 3: DOWNLOAD URLS")
    print("=" * 100)
    
    download_obj = DownloadableSingleFilesDetail(session, movie)
    download_data = await download_obj.get_content()
    
    print(f"\n📥 Full Download Data:")
    print(json.dumps(download_data, indent=2, default=str))
    
    print("\n" + "-" * 80)
    print("DOWNLOAD & STREAM URLS:")
    print("-" * 80)
    
    if isinstance(download_data, dict):
        # Direct downloads
        if 'downloads' in download_data and download_data['downloads']:
            print(f"\n⬇️ Found {len(download_data['downloads'])} download qualities:")
            for i, dl in enumerate(download_data['downloads']):
                if isinstance(dl, dict):
                    quality = dl.get('resolution', 'unknown')
                    size_bytes = dl.get('size', 0)
                    size_mb = round(size_bytes / 1024 / 1024, 2) if size_bytes else 0
                    url = dl.get('url', '')
                    
                    info = f"Quality: {quality}p, Size: {size_mb} MB, Format: {dl.get('format', 'N/A')}, Codec: {dl.get('codec', 'N/A')}"
                    log_url(f"VIDEO DOWNLOAD [{quality}p]", url, info)
                    
                    # Print all available fields
                    print(f"\n   Download {i+1} full data:")
                    for key, value in dl.items():
                        print(f"      {key}: {value}")
        
        # Subtitles/Captions
        if 'captions' in download_data and download_data['captions']:
            print(f"\n📝 Found {len(download_data['captions'])} subtitle tracks:")
            for i, cap in enumerate(download_data['captions']):
                if isinstance(cap, dict):
                    lang_name = cap.get('lanName', 'Unknown')
                    lang_code = cap.get('lan', 'unknown')
                    url = cap.get('url', '')
                    
                    info = f"Language: {lang_name} ({lang_code}), Format: {cap.get('format', 'N/A')}"
                    log_url(f"SUBTITLE [{lang_name}]", url, info)
        
        # Check for any other URL fields
        print("\n🔍 Scanning for any other URL fields in download data...")
        def scan_for_urls(data, prefix=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith('http'):
                        log_url(f"OTHER [{prefix}{key}]", value, "Auto-discovered")
                    elif isinstance(value, dict):
                        scan_for_urls(value, f"{prefix}{key}.")
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                scan_for_urls(item, f"{prefix}{key}[{i}].")
        
        scan_for_urls(download_data)
    
    # 4. SUMMARY
    print("\n" + "=" * 100)
    print("COMPLETE URL SUMMARY")
    print("=" * 100)
    
    print(f"\n📊 Total URLs Found: {len(all_urls_found)}")
    print("\n📋 Categorized List:")
    
    categories = {}
    for item in all_urls_found:
        cat = item['type'].split('[')[0].strip()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    for cat, items in sorted(categories.items()):
        print(f"\n{cat} ({len(items)} URLs):")
        for item in items:
            print(f"   • {item['url'][:80]}...")
            if item['info']:
                print(f"     ({item['info']})")
    
    # Save to file
    output_file = "despicable_me_4_all_urls.json"
    with open(output_file, 'w') as f:
        json.dump({
            'movie_title': 'Despicable Me 4',
            'subject_id': movie.subjectId,
            'detail_path': movie.detailPath,
            'extraction_time': datetime.now().isoformat(),
            'total_urls': len(all_urls_found),
            'urls': all_urls_found
        }, f, indent=2)
    
    print(f"\n💾 All URLs saved to: {output_file}")
    
    print("\n" + "=" * 100)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 100)

asyncio.run(extract_everything())
