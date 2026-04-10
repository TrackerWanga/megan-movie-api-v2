from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from urllib.parse import quote
import httpx

from moviebox_api.v2 import Search, Session
from moviebox_api.v2 import MovieDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/movies", tags=["movies"])

# Configuration
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"
OMDB_API_KEY = "9b5d7e52"
VIDSRC_API = "https://megan-vidsrc.vercel.app"

session = Session()

def generate_megan_id(imdb_id: str = None, subject_id: str = None) -> str:
    if imdb_id:
        return f"megan-{imdb_id}"
    elif subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"

def extract_image(item):
    if hasattr(item, 'cover') and item.cover:
        cover = item.cover
        return {
            "url": str(cover.url),
            "width": cover.width,
            "height": cover.height,
            "size_kb": round(cover.size / 1024, 2) if cover.size else 0
        }
    return None

def create_proxied_url(raw_url: str, title: str, quality: str) -> str:
    """Create a proxied download URL exactly like Prince does"""
    encoded_url = quote(raw_url, safe='')
    encoded_title = quote(title, safe='')
    return f"{MEGAN_DOMAIN}/api/dl?url={encoded_url}&title={encoded_title}&quality={quality}"

def create_proxied_stream(raw_url: str) -> str:
    """Create a proxied stream URL"""
    encoded_url = quote(raw_url, safe='')
    return f"{MEGAN_DOMAIN}/api/stream?url={encoded_url}"

@router.get("/{title}")
async def get_movie(title: str, year: Optional[int] = None):
    # 1. Search for movie
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Find best match
    movie_item = None
    for item in results.items:
        if year and item.releaseDate and item.releaseDate.year == year:
            movie_item = item
            break
    if not movie_item:
        movie_item = results.items[0]
    
    subject_id = movie_item.subjectId
    
    # 2. Get full movie details
    details_obj = MovieDetails(session)
    full_details = await details_obj.get_content(movie_item.detailPath)
    
    # 3. Get OMDb data (for ratings, director, etc.)
    omdb_data = None
    imdb_id = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"http://www.omdbapi.com/",
                params={"apikey": OMDB_API_KEY, "t": movie_item.title, "plot": "full"}
            )
            if response.status_code == 200:
                omdb_data = response.json()
                if omdb_data.get("Response") == "True":
                    imdb_id = omdb_data.get("imdbID")
    except Exception as e:
        print(f"OMDb error: {e}")
    
    # 4. Get downloads DIRECTLY from moviebox_api and PROXIFY them
    downloads = []
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie_item)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            for dl in download_data['downloads']:
                raw_url = dl.get('url')
                if not raw_url:
                    continue
                    
                quality = f"{dl.get('resolution', 'unknown')}p"
                
                # Calculate size
                size_val = dl.get('size', '0')
                try:
                    size_mb = round(int(size_val) / 1024 / 1024, 2)
                except:
                    size_mb = 0
                
                # Create proxified URLs (like Prince does)
                proxied_download = create_proxied_url(raw_url, movie_item.title, quality)
                proxied_stream = create_proxied_stream(raw_url)
                
                downloads.append({
                    "quality": quality,
                    "size_mb": size_mb,
                    "size_bytes": size_val,
                    "format": dl.get('format', 'mp4'),
                    "raw_cdn_url": raw_url,  # For debugging
                    "url": proxied_download,  # Proxified download URL
                    "stream_url": proxied_stream,  # Proxified stream URL
                    "note": "Download through Megan proxy for worldwide access"
                })
                
    except Exception as e:
        print(f"Downloads error: {e}")
    
    # 5. Get streams from vidsrc (fallback)
    streams = []
    if imdb_id:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{VIDSRC_API}/api/streams/{imdb_id}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        streams = data.get("streams", [])
        except Exception as e:
            print(f"Vidsrc error: {e}")
    
    # 6. Build response
    poster = extract_image(movie_item)
    
    backdrop = None
    if movie_item and hasattr(movie_item, 'stills') and movie_item.stills:
        backdrop = {
            "url": str(movie_item.stills.url),
            "width": movie_item.stills.width,
            "height": movie_item.stills.height,
            "size_kb": round(movie_item.stills.size / 1024, 2) if movie_item.stills.size else 0
        }
    
    trailer = None
    if full_details and 'subject' in full_details:
        trailer_data = full_details.get('subject', {}).get('trailer', {})
        if trailer_data and 'videoAddress' in trailer_data:
            trailer = {
                "url": trailer_data['videoAddress'].get('url'),
                "duration": trailer_data['videoAddress'].get('duration'),
                "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
            }
    
    cast = []
    if full_details and 'stars' in full_details:
        for star in full_details.get('stars', [])[:15]:
            cast.append({
                "name": star.get('name'),
                "character": star.get('character'),
                "avatar": star.get('avatarUrl')
            })
    
    subtitles = []
    if movie_item and hasattr(movie_item, 'subtitles') and movie_item.subtitles:
        subs = movie_item.subtitles.split(',') if isinstance(movie_item.subtitles, str) else movie_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "data": {
            "movie": {
                "megan_id": generate_megan_id(imdb_id, str(movie_item.subjectId)),
                "imdb_id": imdb_id,
                "subject_id": str(subject_id),
                "title": movie_item.title,
                "year": movie_item.releaseDate.year if movie_item.releaseDate else None,
                "runtime": omdb_data.get("Runtime") if omdb_data else None,
                "release_date": movie_item.releaseDate.isoformat() if movie_item.releaseDate else None,
                "genres": movie_item.genre if isinstance(movie_item.genre, list) else (movie_item.genre.split(',') if movie_item.genre else []),
                "director": omdb_data.get("Director") if omdb_data else None,
                "cast": cast,
                "plot": omdb_data.get("Plot") if omdb_data else movie_item.description,
                "poster": poster,
                "backdrop": backdrop,
                "trailer": trailer,
                "ratings": {
                    "imdb": float(omdb_data.get("imdbRating", 0)) if omdb_data and omdb_data.get("imdbRating") != "N/A" else movie_item.imdbRatingValue,
                    "imdb_votes": omdb_data.get("imdbVotes") if omdb_data else None
                },
                "subtitles": subtitles,
                "detail_path": movie_item.detailPath
            },
            "sources": {
                "downloads": downloads,
                "streams": streams,
                "total_downloads": len(downloads),
                "note": "All download URLs are proxified through Megan API for worldwide access. Use 'url' for direct download."
            }
        }
    }
