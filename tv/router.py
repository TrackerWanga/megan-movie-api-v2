from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime
from urllib.parse import quote

from moviebox_api.v2 import Search, Session, TVSeriesDetails
from moviebox_api.v2.download import DownloadableTVSeriesFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/tv", tags=["tv_series"])

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

async def get_prince_sources(subject_id: str, season: int = None, episode: int = None):
    """Get sources from PRINCE API (hidden)"""
    url = f"{PRINCE_API}/api/sources/{subject_id}"
    if season and episode:
        url += f"?season={season}&episode={episode}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
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
# SEARCH TV SERIES
# ============================================

@router.get("/search")
async def search_tv(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Results limit")
):
    """Search for TV series only"""
    search = Search(session, query=q, subject_type=SubjectType.TV_SERIES)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e), "query": q}
    
    items = []
    for item in results.items[:limit]:
        year = item.releaseDate.year if item.releaseDate else None
        items.append({
            "title": item.title,
            "year": year,
            "rating": item.imdbRatingValue,
            "poster": item.cover.url if item.cover else None,
            "detailPath": item.detailPath,
            "subjectId": str(item.subjectId) if item.subjectId else None
        })
    
    return {
        "success": True,
        "query": q,
        "total": len(items),
        "results": items
    }

# ============================================
# TV SERIES DETAILS
# ============================================

@router.get("/{title}")
async def get_tv_series(
    title: str,
    year: Optional[int] = None
):
    """Get complete TV series data: metadata + seasons + episode downloads"""
    
    # 1. Search for TV series
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    # Find best match by year
    series_item = None
    for item in results.items:
        if year and item.releaseDate and item.releaseDate.year == year:
            series_item = item
            break
    if not series_item:
        series_item = results.items[0]
    
    subject_id = series_item.subjectId
    
    # 2. Get series details
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(series_item.detailPath)
    
    # 3. Get OMDb data
    omdb_data = await get_omdb_data(title=series_item.title, year=series_item.releaseDate.year if series_item.releaseDate else None)
    imdb_id = omdb_data.get("imdbID") if omdb_data else None
    
    # 4. Extract seasons info
    resource = detail_data.get('resource', {})
    seasons_data = resource.get('seasons', [])
    
    seasons = []
    for season in seasons_data:
        se = season.get('se', 0)
        max_ep = season.get('maxEp', 0)
        resolutions = season.get('resolutions', [])
        seasons.append({
            "season": se,
            "max_episodes": max_ep,
            "available_qualities": [r.get('resolution') for r in resolutions]
        })
    
    # 5. Get first episode download from PRINCE (as example)
    episode_download_example = None
    prince_data = await get_prince_sources(subject_id, season=1, episode=1)
    
    if prince_data:
        for source in prince_data.get("results", []):
            if source.get("type") == "direct":
                original_url = source.get("download_url") or source.get("embed_url")
                episode_download_example = {
                    "season": 1,
                    "episode": 1,
                    "downloads": [{
                        "quality": source.get("quality"),
                        "size_mb": round(int(source.get("size", 0)) / 1024 / 1024, 2) if source.get("size") else 0,
                        "url": original_url,
                        "proxied_url": f"{MEGAN_DOMAIN}/api/proxy/dl?url={quote(original_url, safe='')}&title={quote(series_item.title)}_S1E1&quality={source.get('quality')}"
                    }]
                }
                break
    
    # 6. Extract poster
    subject = detail_data.get('subject', {})
    cover = subject.get('cover', {})
    poster = None
    if cover:
        poster = {
            "url": cover.get('url'),
            "width": cover.get('width'),
            "height": cover.get('height'),
            "size_kb": round(cover.get('size', 0) / 1024, 2) if cover.get('size') else 0
        }
    
    # 7. Extract backdrop
    stills = subject.get('stills', {})
    backdrop = None
    if stills:
        backdrop = {
            "url": stills.get('url'),
            "width": stills.get('width'),
            "height": stills.get('height'),
            "size_kb": round(stills.get('size', 0) / 1024, 2) if stills.get('size') else 0
        }
    
    # 8. Extract trailer
    trailer = None
    trailer_data = subject.get('trailer', {})
    video_addr = trailer_data.get('videoAddress', {})
    if video_addr:
        trailer = {
            "url": video_addr.get('url'),
            "duration": video_addr.get('duration'),
            "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
        }
    
    # 9. Extract cast
    cast = []
    stars = detail_data.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # 10. Subtitles
    subtitles = []
    if series_item and hasattr(series_item, 'subtitles') and series_item.subtitles:
        subs = series_item.subtitles.split(',') if isinstance(series_item.subtitles, str) else series_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    # 11. Build response
    return {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "series": {
                "megan_id": generate_megan_id(imdb_id, str(series_item.subjectId)),
                "imdb_id": imdb_id,
                "title": series_item.title,
                "year": omdb_data.get("Year") if omdb_data else (series_item.releaseDate.year if series_item.releaseDate else None),
                "rated": omdb_data.get("Rated") if omdb_data else None,
                "runtime": omdb_data.get("Runtime") if omdb_data else None,
                "genres": series_item.genre if isinstance(series_item.genre, list) else (series_item.genre.split(',') if series_item.genre else []),
                "director": omdb_data.get("Director") if omdb_data else None,
                "cast": cast,
                "plot": omdb_data.get("Plot") if omdb_data else subject.get('description'),
                "poster": poster,
                "backdrop": backdrop,
                "trailer": trailer,
                "ratings": {
                    "imdb": float(omdb_data.get("imdbRating", 0)) if omdb_data and omdb_data.get("imdbRating") != "N/A" else series_item.imdbRatingValue,
                    "imdb_votes": omdb_data.get("imdbVotes") if omdb_data else None
                },
                "subtitles": subtitles,
                "seasons": seasons,
                "total_seasons": len(seasons)
            },
            "sources": {
                "episode_example": episode_download_example,
                "note": "Use /api/tv/{title}/episode?season=X&episode=Y to get specific episode downloads"
            }
        }
    }

# ============================================
# EPISODE DOWNLOAD (PRINCE-POWERED)
# ============================================

@router.get("/{title}/episode")
async def get_tv_episode(
    title: str,
    season: int = Query(..., ge=1, description="Season number"),
    episode: int = Query(..., ge=1, description="Episode number"),
    year: Optional[int] = None
):
    """Get download URLs for a specific episode (PRINCE-powered, worldwide working)"""
    
    # Search for the series
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    if year and series_item.releaseDate and series_item.releaseDate.year != year:
        for item in results.items:
            if item.releaseDate and item.releaseDate.year == year:
                series_item = item
                break
    
    subject_id = series_item.subjectId
    
    # Get from PRINCE API
    prince_data = await get_prince_sources(subject_id, season=season, episode=episode)
    
    downloads = []
    if prince_data:
        for source in prince_data.get("results", []):
            if source.get("type") == "direct":
                original_url = source.get("download_url") or source.get("embed_url")
                downloads.append({
                    "quality": source.get("quality"),
                    "size_mb": round(int(source.get("size", 0)) / 1024 / 1024, 2) if source.get("size") else 0,
                    "url": original_url,
                    "proxied_url": f"{MEGAN_DOMAIN}/api/proxy/dl?url={quote(original_url, safe='')}&title={quote(series_item.title)}_S{season}E{episode}&quality={source.get('quality')}"
                })
    
    return {
        "success": True,
        "series": series_item.title,
        "season": season,
        "episode": episode,
        "downloads": downloads,
        "note": "These download URLs work worldwide. Use proxied_url for best compatibility."
    }

# ============================================
# SEASONS INFO
# ============================================

@router.get("/{title}/seasons")
async def get_tv_seasons(title: str, year: Optional[int] = None):
    """Get all seasons and episodes info for a TV series"""
    
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(series_item.detailPath)
    
    resource = detail_data.get('resource', {})
    seasons_data = resource.get('seasons', [])
    
    seasons = []
    for season in seasons_data:
        se = season.get('se', 0)
        max_ep = season.get('maxEp', 0)
        resolutions = season.get('resolutions', [])
        seasons.append({
            "season": se,
            "max_episodes": max_ep,
            "available_qualities": [r.get('resolution') for r in resolutions],
            "episodes_available": max_ep > 0
        })
    
    return {
        "success": True,
        "title": series_item.title,
        "total_seasons": len(seasons),
        "seasons": seasons,
        "example": f"/api/tv/{title}/episode?season=1&episode=1"
    }
