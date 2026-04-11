#!/usr/bin/env python3
"""
Movie Download Proxifier - Gets raw CDN URLs from MovieBox API
and wraps them through your proxy endpoint exactly like Prince does.
"""

import enum
import sys
import asyncio
import json
from urllib.parse import quote
from datetime import datetime

# StrEnum polyfill for compatibility
if not hasattr(enum, 'StrEnum'):
    try:
        from strenum import StrEnum
        enum.StrEnum = StrEnum
    except ImportError:
        class StrEnum(str, enum.Enum):
            pass
        enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType
from moviebox_api.v2.download import DownloadableSingleFilesDetail

# ============================================
# CONFIGURATION
# ============================================

# Your API domain
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"

# Whether to use your proxy or Prince's proxy (for testing)
USE_MEGAN_PROXY = True  # Set to False to use Prince's proxy for comparison

PRINCE_DOMAIN = "https://movieapi.princetechn.com"

# ============================================
# PROXY URL GENERATOR (Prince-Style)
# ============================================

def create_proxied_url(raw_url: str, title: str, quality: str, use_megan: bool = True) -> dict:
    """
    Create a proxied download URL exactly like Prince does.
    
    Prince format:
    https://movieapi.princetechn.com/api/dl?url={ENCODED_URL}&title={TITLE}&quality={QUALITY}
    
    Your format (identical pattern):
    https://movieapi.megan.qzz.io/api/dl?url={ENCODED_URL}&title={TITLE}&quality={QUALITY}
    """
    
    # URL encode the raw CDN URL (same as Prince)
    encoded_url = quote(raw_url, safe='')
    
    # URL encode the title for the query parameter
    encoded_title = quote(title, safe='')
    
    # Choose domain
    domain = MEGAN_DOMAIN if use_megan else PRINCE_DOMAIN
    
    # Build the proxied URL
    proxied_url = f"{domain}/api/dl?url={encoded_url}&title={encoded_title}&quality={quality}"
    
    return {
        "raw_cdn_url": raw_url,
        "encoded_url": encoded_url,
        "proxied_url": proxied_url,
        "domain": domain,
        "title": title,
        "quality": quality
    }

def create_stream_url(raw_url: str, use_megan: bool = True) -> str:
    """Create a streaming URL (for video players)"""
    encoded_url = quote(raw_url, safe='')
    domain = MEGAN_DOMAIN if use_megan else PRINCE_DOMAIN
    return f"{domain}/api/stream?url={encoded_url}"

# ============================================
# MOVIE DOWNLOAD FETCHER
# ============================================

async def get_movie_downloads_proxified(
    movie_title: str, 
    year: int = None,
    use_megan_proxy: bool = True
) -> dict:
    """
    Search for a movie, get all download qualities from MovieBox API,
    and create proxified URLs for each quality.
    """
    
    session = Session()
    
    print(f"\n{'='*80}")
    print(f"🎬 FETCHING & PROXIFYING: {movie_title}" + (f" ({year})" if year else ""))
    print(f"{'='*80}")
    
    # 1. Search for the movie
    print(f"\n🔍 Searching MovieBox API...")
    search = Search(session, query=movie_title, subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    if not results.items:
        print(f"❌ Movie not found: {movie_title}")
        return {"success": False, "error": "Movie not found"}
    
    # 2. Find best match (by year if provided)
    movie_item = None
    for item in results.items:
        if year and item.releaseDate and item.releaseDate.year == year:
            movie_item = item
            break
    
    if not movie_item:
        movie_item = results.items[0]
    
    print(f"✅ Found: {movie_item.title}")
    print(f"   SubjectId: {movie_item.subjectId}")
    print(f"   Year: {movie_item.releaseDate.year if movie_item.releaseDate else 'N/A'}")
    print(f"   Rating: {movie_item.imdbRatingValue}/10")
    
    # 3. Get download URLs from MovieBox API
    print(f"\n📥 Fetching download URLs from MovieBox API...")
    
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie_item)
        download_data = await downloads_obj.get_content()
        
        if not download_data or 'downloads' not in download_data:
            print(f"❌ No downloads available from MovieBox API")
            return {"success": False, "error": "No downloads available"}
        
        print(f"✅ Found {len(download_data['downloads'])} quality options")
        
    except Exception as e:
        print(f"❌ Error fetching downloads: {e}")
        return {"success": False, "error": str(e)}
    
    # 4. Process and proxify each download
    proxified_downloads = []
    
    print(f"\n{'─'*80}")
    print(f"📦 PROXIFIED DOWNLOAD URLS")
    print(f"{'─'*80}")
    
    for dl in download_data['downloads']:
        raw_url = dl.get('url')
        if not raw_url:
            continue
            
        quality = f"{dl.get('resolution', 'unknown')}p"
        size_bytes = dl.get('size', 0)
        size_mb = round(size_bytes / 1024 / 1024, 2) if size_bytes else 0
        
        # Create proxified URL
        proxied = create_proxied_url(
            raw_url=raw_url,
            title=movie_item.title,
            quality=quality,
            use_megan=use_megan_proxy
        )
        
        # Create stream URL
        stream_url = create_stream_url(raw_url, use_megan=use_megan_proxy)
        
        # Build download object
        download_info = {
            "quality": quality,
            "size_mb": size_mb,
            "size_bytes": size_bytes,
            "format": dl.get('format', 'mp4'),
            "codec": dl.get('codec', 'h264'),
            "raw_cdn_url": proxied["raw_cdn_url"],
            "proxied_download_url": proxied["proxied_url"],
            "proxied_stream_url": stream_url,
            "domain_used": proxied["domain"]
        }
        
        proxified_downloads.append(download_info)
        
        # Print details
        print(f"\n🎬 QUALITY: {quality}")
        print(f"   Size: {size_mb} MB")
        print(f"   Format: {dl.get('format', 'mp4')} | Codec: {dl.get('codec', 'h264')}")
        print(f"   Raw CDN: {raw_url[:80]}...")
        print(f"   Proxied Download: {proxied['proxied_url'][:100]}...")
        print(f"   Proxied Stream: {stream_url[:100]}...")
    
    # 5. Get subtitles if available
    subtitles = []
    if 'captions' in download_data and download_data['captions']:
        print(f"\n{'─'*80}")
        print(f"📝 SUBTITLES AVAILABLE")
        print(f"{'─'*80}")
        for cap in download_data['captions'][:10]:  # Show first 10
            sub_info = {
                "language": cap.get('lanName', 'Unknown'),
                "code": cap.get('lan', 'unknown'),
                "url": cap.get('url'),
                "format": cap.get('format', 'srt')
            }
            subtitles.append(sub_info)
            print(f"   • {sub_info['language']} ({sub_info['code']})")
    
    # 6. Build complete response (Prince-style)
    response = {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "timestamp": datetime.now().isoformat(),
        "proxy_domain": MEGAN_DOMAIN if use_megan_proxy else PRINCE_DOMAIN,
        "data": {
            "movie": {
                "megan_id": f"megan-{movie_item.subjectId}",
                "subject_id": str(movie_item.subjectId),
                "title": movie_item.title,
                "year": movie_item.releaseDate.year if movie_item.releaseDate else None,
                "rating": movie_item.imdbRatingValue,
                "genres": movie_item.genre if isinstance(movie_item.genre, list) else [movie_item.genre] if movie_item.genre else [],
                "detail_path": movie_item.detailPath,
                "poster": str(movie_item.cover.url) if movie_item.cover else None
            },
            "downloads": proxified_downloads,
            "subtitles": subtitles,
            "total_qualities": len(proxified_downloads),
            "note": "All download URLs are proxified through Megan API. Use proxied_download_url for direct downloads."
        }
    }
    
    return response

# ============================================
# BATCH PROCESSING
# ============================================

async def process_multiple_movies(movies: list, use_megan_proxy: bool = True):
    """Process multiple movies and save results"""
    
    all_results = []
    
    for movie in movies:
        title = movie.get('title')
        year = movie.get('year')
        
        result = await get_movie_downloads_proxified(title, year, use_megan_proxy)
        all_results.append(result)
        
        # Save individual result
        filename = f"{title.replace(' ', '_').replace(':', '')}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Saved to: {filename}")
    
    # Save combined results
    combined_filename = f"all_movies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(combined_filename, 'w') as f:
        json.dump({
            "total_movies": len(all_results),
            "timestamp": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ All results saved to: {combined_filename}")
    print(f"{'='*80}")
    
    return all_results

# ============================================
# COMPARISON TEST (Megan vs Prince Proxy)
# ============================================

async def compare_proxies(movie_title: str, year: int = None):
    """Compare Megan's proxy with Prince's proxy"""
    
    print(f"\n{'='*80}")
    print(f"🔬 COMPARISON TEST: Megan Proxy vs Prince Proxy")
    print(f"{'='*80}")
    
    # Get with Megan proxy
    print(f"\n📀 TESTING WITH MEGAN PROXY")
    megan_result = await get_movie_downloads_proxified(movie_title, year, use_megan_proxy=True)
    
    # Get with Prince proxy
    print(f"\n📀 TESTING WITH PRINCE PROXY")
    prince_result = await get_movie_downloads_proxified(movie_title, year, use_megan_proxy=False)
    
    # Compare
    print(f"\n{'='*80}")
    print(f"📊 COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    if megan_result['success'] and prince_result['success']:
        megan_count = len(megan_result['data']['downloads'])
        prince_count = len(prince_result['data']['downloads'])
        
        print(f"\n✅ Both proxies successful")
        print(f"   Megan proxy URLs: {megan_count}")
        print(f"   Prince proxy URLs: {prince_count}")
        
        # Show first URL from each for comparison
        if megan_count > 0:
            print(f"\n📀 Megan Proxy Example:")
            print(f"   {megan_result['data']['downloads'][0]['proxied_download_url'][:120]}...")
        
        if prince_count > 0:
            print(f"\n📀 Prince Proxy Example:")
            print(f"   {prince_result['data']['downloads'][0]['proxied_download_url'][:120]}...")
    
    return {
        "megan_proxy": megan_result,
        "prince_proxy": prince_result
    }

# ============================================
# MAIN
# ============================================

async def main():
    """Main function - process test movies"""
    
    print("="*80)
    print("🎬 MOVIE DOWNLOAD PROXIFIER")
    print("="*80)
    print(f"Proxy Domain: {MEGAN_DOMAIN}")
    print(f"Pattern: {MEGAN_DOMAIN}/api/dl?url={{ENCODED_CDN_URL}}&title={{TITLE}}&quality={{QUALITY}}")
    print("="*80)
    
    # Test movies (from your earlier tests)
    test_movies = [
        {"title": "Avatar", "year": 2009},
        {"title": "War Machine", "year": None},
        {"title": "Avatar: Fire and Ash", "year": None},
    ]
    
    # Choose mode
    print("\n📋 Select mode:")
    print("   1. Test Megan proxy only")
    print("   2. Compare Megan vs Prince proxy")
    print("   3. Batch process all test movies")
    
    mode = input("\nEnter choice (1/2/3): ").strip()
    
    if mode == "1":
        # Single test with Megan proxy
        result = await get_movie_downloads_proxified("Avatar", 2009, use_megan_proxy=True)
        
        # Save result
        filename = f"avatar_proxified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Saved to: {filename}")
        
    elif mode == "2":
        # Comparison test
        await compare_proxies("Avatar", 2009)
        
    elif mode == "3":
        # Batch process
        await process_multiple_movies(test_movies, use_megan_proxy=True)
    
    else:
        print("Invalid choice, running single test...")
        result = await get_movie_downloads_proxified("Avatar", 2009, use_megan_proxy=True)
    
    print("\n" + "="*80)
    print("✅ DONE!")
    print("="*80)

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    asyncio.run(main())
