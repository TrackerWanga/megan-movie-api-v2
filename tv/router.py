from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx

from moviebox_api.v2 import Search, Session, TVSeriesDetails
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api", tags=["tv_series"])

# Configuration
WORKER_URL = "https://streamapi.megan.qzz.io"
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"

session = Session()

def generate_megan_id(subject_id: str = None) -> str:
    """Generate Megan ID"""
    if subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"

def extract_image(item) -> Optional[Dict]:
    """Extract cover image"""
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
# NEW RESTful ENDPOINTS (ID-based) - PREFERRED
# ============================================

@router.get("/tv/{subject_id}")
async def get_tv_by_id(subject_id: str):
    """Get complete TV series details by subject_id"""
    
    search = Search(session, query=subject_id, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    detail_path = series_item.detailPath
    
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(detail_path)
    subject = detail_data.get('subject', {})
    
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
    
    cover = subject.get('cover', {})
    poster = None
    if cover:
        poster = {
            "url": cover.get('url'),
            "width": cover.get('width'),
            "height": cover.get('height')
        }
    
    stills = subject.get('stills', {})
    backdrop = None
    if stills:
        backdrop = {
            "url": stills.get('url'),
            "width": stills.get('width'),
            "height": stills.get('height')
        }
    
    trailer = None
    trailer_data = subject.get('trailer', {})
    video_addr = trailer_data.get('videoAddress', {})
    if video_addr:
        trailer = {
            "url": video_addr.get('url'),
            "duration": video_addr.get('duration'),
            "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
        }
    
    cast = []
    stars = detail_data.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    subtitles = []
    if hasattr(series_item, 'subtitles') and series_item.subtitles:
        subs = series_item.subtitles.split(',') if isinstance(series_item.subtitles, str) else series_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "data": {
            "series": {
                "megan_id": generate_megan_id(subject_id),
                "subject_id": subject_id,
                "detail_path": detail_path,
                "title": series_item.title,
                "year": series_item.releaseDate.year if series_item.releaseDate else None,
                "genres": series_item.genre if isinstance(series_item.genre, list) else (series_item.genre.split(',') if series_item.genre else []),
                "rating": series_item.imdbRatingValue,
                "description": subject.get('description', ''),
                "poster": poster,
                "backdrop": backdrop,
                "trailer": trailer,
                "cast": cast,
                "subtitles": subtitles,
                "seasons": seasons,
                "total_seasons": len(seasons)
            }
        }
    }


@router.get("/tv/{subject_id}/seasons")
async def get_tv_seasons_by_id(subject_id: str):
    """Get seasons info for a TV series"""
    
    search = Search(session, query=subject_id, subject_type=SubjectType.TV_SERIES)
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
        seasons.append({
            "season": season.get('se', 0),
            "episodes": season.get('maxEp', 0),
            "available_qualities": [r.get('resolution') for r in season.get('resolutions', [])]
        })
    
    return {
        "success": True,
        "title": series_item.title,
        "subject_id": subject_id,
        "total_seasons": len(seasons),
        "seasons": seasons
    }


@router.get("/tv/{subject_id}/episode")
async def get_tv_episode_by_id(
    subject_id: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Get download/stream URLs for a specific episode"""
    
    resolution = quality.replace('p', '')
    
    # Get series title for response
    search = Search(session, query=subject_id, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    title = results.items[0].title if results.items else "Unknown"
    
    return {
        "success": True,
        "series": title,
        "subject_id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "download": {
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={subject_id}&se={season}&ep={episode}&resolution={resolution}"
        },
        "stream": {
            "url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={subject_id}&se={season}&ep={episode}&resolution={resolution}"
        }
    }


@router.get("/tv/{subject_id}/download")
async def download_tv_by_id(
    subject_id: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Download TV episode by subject_id"""
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "subject_id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={subject_id}&se={season}&ep={episode}&resolution={resolution}"
    }


@router.get("/tv/{subject_id}/stream")
async def stream_tv_by_id(
    subject_id: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Stream TV episode by subject_id"""
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "subject_id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={subject_id}&se={season}&ep={episode}&resolution={resolution}"
    }


# ============================================
# LEGACY ENDPOINTS (Title-based) - DEPRECATED
# ============================================

@router.get("/tv/search")
async def search_tv_legacy(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50)
):
    """[DEPRECATED] Search for TV series - use /api/search?q={query}&type=tv instead"""
    search = Search(session, query=q, subject_type=SubjectType.TV_SERIES)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e), "query": q}
    
    items = []
    for item in results.items[:limit]:
        year = item.releaseDate.year if item.releaseDate else None
        items.append({
            "megan_id": generate_megan_id(str(item.subjectId)),
            "title": item.title,
            "year": year,
            "rating": item.imdbRatingValue,
            "poster": str(item.cover.url) if item.cover else None,
            "detail_path": item.detailPath,
            "subject_id": str(item.subjectId) if item.subjectId else None
        })
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use /api/search?q={query}&type=tv instead",
        "query": q,
        "total": len(items),
        "results": items
    }


@router.get("/tv/{title}")
async def get_tv_series_legacy(title: str, year: Optional[int] = None):
    """[DEPRECATED] Use /tv/{id} instead"""
    
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = None
    for item in results.items:
        if year and item.releaseDate and item.releaseDate.year == year:
            series_item = item
            break
    if not series_item:
        series_item = results.items[0]
    
    subject_id = str(series_item.subjectId)
    detail_path = series_item.detailPath
    
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(detail_path)
    subject = detail_data.get('subject', {})
    
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
    
    cover = subject.get('cover', {})
    poster = None
    if cover:
        poster = {
            "url": cover.get('url'),
            "width": cover.get('width'),
            "height": cover.get('height')
        }
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "deprecated": True,
        "message": "Use /api/tv/{id} instead",
        "data": {
            "series": {
                "megan_id": generate_megan_id(subject_id),
                "subject_id": subject_id,
                "detail_path": detail_path,
                "title": series_item.title,
                "year": series_item.releaseDate.year if series_item.releaseDate else None,
                "genres": series_item.genre if isinstance(series_item.genre, list) else (series_item.genre.split(',') if series_item.genre else []),
                "rating": series_item.imdbRatingValue,
                "description": subject.get('description', ''),
                "poster": poster,
                "seasons": seasons,
                "total_seasons": len(seasons)
            }
        }
    }


@router.get("/tv/{title}/episode")
async def get_tv_episode_legacy(
    title: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p"),
    year: Optional[int] = None
):
    """[DEPRECATED] Use /tv/{id}/episode instead"""
    
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    subject_id = str(series_item.subjectId)
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use /api/tv/{id}/episode instead",
        "series": series_item.title,
        "subject_id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "download": {
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={subject_id}&se={season}&ep={episode}&resolution={resolution}"
        },
        "stream": {
            "url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={subject_id}&se={season}&ep={episode}&resolution={resolution}"
        }
    }


@router.get("/tv/{title}/seasons")
async def get_tv_seasons_legacy(title: str, year: Optional[int] = None):
    """[DEPRECATED] Use /tv/{id}/seasons instead"""
    
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    subject_id = str(series_item.subjectId)
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(series_item.detailPath)
    
    resource = detail_data.get('resource', {})
    seasons_data = resource.get('seasons', [])
    
    seasons = []
    for season in seasons_data:
        seasons.append({
            "season": season.get('se', 0),
            "episodes": season.get('maxEp', 0),
            "available_qualities": [r.get('resolution') for r in season.get('resolutions', [])]
        })
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use /api/tv/{id}/seasons instead",
        "title": series_item.title,
        "subject_id": subject_id,
        "total_seasons": len(seasons),
        "seasons": seasons
    }


@router.get("/tv/catalog/all")
async def get_tv_catalog():
    """Get all TV series catalog from Worker"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{WORKER_URL}/tv-series")
            if resp.status_code == 200:
                return {"success": True, "source": "worker", "data": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False, "error": "Failed to fetch catalog"}

