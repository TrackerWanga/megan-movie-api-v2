from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime
from urllib.parse import quote
import json

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/movies", tags=["movies"])

# Configuration
OMDB_API_KEY = "9b5d7e52"
OMDB_URL = "http://www.omdbapi.com/"
PRINCE_API = "https://movieapi.princetechn.com"
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"

# Cache
omdb_cache = {}
session = Session()

# ============================================
# HELPER FUNCTIONS
# ============================================

async def get_omdb_data(imdb_id: str = None, title: str = None, year: int = None):
    """Get OMDb metadata with caching"""
    cache_key = imdb_id or f"{title}_{year}"
    if cache_key in omdb_cache:
        return omdb_cache[cache_key]
    
    params = {"apikey": OMDB_API_KEY, "plot": "full"}
    if imdb_id:
        params["i"] = imdb_id
    elif title:
        params["t"] = title
        if year:
            params["y"] = year
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OMDB_URL, params=params)
            data = response.json()
            if data.get("Response") == "True":
                omdb_cache[cache_key] = data
                return data
        except Exception as e:
            print(f"OMDb error: {e}")
    
    omdb_cache[cache_key] = None
    return None

async def get_prince_downloads(subject_id: str):
    """Get download URLs from PRINCE API (hidden)"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{PRINCE_API}/api/sources/{subject_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"PRINCE API error: {e}")
    return None

def generate_megan_id(imdb_id: str = None, subject_id: str = None) -> str:
    if imdb_id:
        return f"megan-{imdb_id}"
    elif subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"

def extract_image(item) -> Optional[Dict]:
    if hasattr(item, 'cover') and item.cover:
        cover = item.cover
        return {
            "url": str(cover.url),
            "width": cover.width,
            "height": cover.height,
            "size_kb": round(cover.size / 1024, 2) if cover.size else 0
        }
    return None

# ============================================
# MAIN MOVIE ENDPOINT
# ============================================

@router.get("/{title}")
async def get_movie(
    title: str,
    year: Optional[int] = None
):
    """Get COMPLETE movie data: metadata + downloads (PRINCE-powered) + streams"""
    
    # 1. Search for movie in moviebox_api
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Find best match by year
    movie_item = None
    for item in results.items:
        if year and item.releaseDate and item.releaseDate.year == year:
            movie_item = item
            break
    if not movie_item:
        movie_item = results.items[0]
    
    subject_id = movie_item.subjectId
    
    # 2. Get full movie details (cast, trailer, backdrop)
    from moviebox_api.v2 import MovieDetails
    details_obj = MovieDetails(session)
    full_details = await details_obj.get_content(movie_item.detailPath)
    
    # 3. Get OMDb data for rich metadata
    omdb_data = await get_omdb_data(title=movie_item.title, year=movie_item.releaseDate.year if movie_item.releaseDate else None)
    imdb_id = omdb_data.get("imdbID") if omdb_data else None
    
    # 4. Get downloads from PRINCE API (worldwide working)
    prince_data = await get_prince_downloads(subject_id)
    
    downloads = []
    if prince_data:
        for source in prince_data.get("results", []):
            if source.get("type") == "direct" and "MovieBox" in source.get("provider", ""):
                original_url = source.get("download_url") or source.get("embed_url")
                downloads.append({
                    "quality": source.get("quality"),
                    "size_mb": round(int(source.get("size", 0)) / 1024 / 1024, 2) if source.get("size") else 0,
                    "url": original_url,
                    "proxied_url": f"{MEGAN_DOMAIN}/api/proxy/dl?url={quote(original_url, safe='')}&title={quote(movie_item.title)}&quality={source.get('quality')}"
                })
    
    # 5. Get streams from vidsrc
    streams = []
    if imdb_id:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"https://megan-vidsrc.vercel.app/api/streams/{imdb_id}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        streams = data.get("streams", [])
        except:
            pass
    
    # 6. Poster with dimensions
    poster = extract_image(movie_item)
    
    # 7. Backdrop/stills
    backdrop = None
    if movie_item and hasattr(movie_item, 'stills') and movie_item.stills:
        backdrop = {
            "url": str(movie_item.stills.url),
            "width": movie_item.stills.width,
            "height": movie_item.stills.height,
            "size_kb": round(movie_item.stills.size / 1024, 2) if movie_item.stills.size else 0
        }
    
    # 8. Trailer
    trailer = None
    if full_details and 'subject' in full_details:
        trailer_data = full_details.get('subject', {}).get('trailer', {})
        if trailer_data and 'videoAddress' in trailer_data:
            trailer = {
                "url": trailer_data['videoAddress'].get('url'),
                "duration": trailer_data['videoAddress'].get('duration'),
                "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
            }
    
    # 9. Cast
    cast = []
    if full_details and 'stars' in full_details:
        for star in full_details.get('stars', [])[:15]:
            cast.append({
                "name": star.get('name'),
                "character": star.get('character'),
                "avatar": star.get('avatarUrl')
            })
    
    # 10. Subtitles
    subtitles = []
    if movie_item and hasattr(movie_item, 'subtitles') and movie_item.subtitles:
        subs = movie_item.subtitles.split(',') if isinstance(movie_item.subtitles, str) else movie_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                lang = sub.strip()
                subtitles.append({"language": lang, "code": lang[:2].lower()})
    
    # 11. Build final response
    return {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "movie": {
                "megan_id": generate_megan_id(imdb_id, str(movie_item.subjectId)),
                "imdb_id": imdb_id,
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
                    "imdb": float(omdb_data.get("imdbRating", 0)) if omdb_data and omdb_data.get("imdbRating") != "N/A" else None,
                    "imdb_votes": omdb_data.get("imdbVotes") if omdb_data else None,
                    "rotten_tomatoes": None,
                    "metacritic": None
                },
                "subtitles": subtitles
            },
            "sources": {
                "downloads": downloads,
                "streams": streams
            }
        }
    }

# ============================================
# DOWNLOADS ONLY ENDPOINT
# ============================================

@router.get("/{title}/downloads")
async def get_movie_downloads(title: str, year: Optional[int] = None):
    """Get only download URLs (PRINCE-powered, worldwide working)"""
    
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_item = results.items[0]
    if year and movie_item.releaseDate and movie_item.releaseDate.year != year:
        for item in results.items:
            if item.releaseDate and item.releaseDate.year == year:
                movie_item = item
                break
    
    subject_id = movie_item.subjectId
    prince_data = await get_prince_downloads(subject_id)
    
    downloads = []
    if prince_data:
        for source in prince_data.get("results", []):
            if source.get("type") == "direct" and "MovieBox" in source.get("provider", ""):
                original_url = source.get("download_url") or source.get("embed_url")
                downloads.append({
                    "quality": source.get("quality"),
                    "size_mb": round(int(source.get("size", 0)) / 1024 / 1024, 2) if source.get("size") else 0,
                    "url": original_url,
                    "proxied_url": f"{MEGAN_DOMAIN}/api/proxy/dl?url={quote(original_url, safe='')}&title={quote(movie_item.title)}&quality={source.get('quality')}"
                })
    
    return {
        "success": True,
        "title": movie_item.title,
        "year": movie_item.releaseDate.year if movie_item.releaseDate else None,
        "downloads": downloads,
        "note": "These download URLs work worldwide. Use proxied_url for best compatibility."
    }
