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
    if subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"


# ============================================
# TV SERIES METADATA BY detail_path
# ============================================

@router.get("/tv/{subject_id}")
async def get_tv_metadata(subject_id: str, detail_path: str = Query(None)):
    """Get complete TV series metadata using detail_path"""
    
    # If detail_path is provided, use it directly
    if detail_path:
        try:
            tv_details = TVSeriesDetails(session)
            detail_data = await tv_details.get_content(detail_path)
            subject = detail_data.get('subject', {})
            resource = detail_data.get('resource', {})
            
            # Get series title for the response
            title = subject.get('title', 'Unknown')
            
            return await build_tv_response(subject_id, detail_path, None, subject, resource, detail_data)
        except Exception as e:
            print(f"Error with detail_path: {e}")
    
    # Fallback: Try to get title from Worker
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{WORKER_URL}/api/stream/{subject_id}",
                params={"detail_path": subject_id}
            )
            if resp.status_code == 200:
                data = resp.json()
                title = data.get('title')
                if title:
                    # Search by title
                    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
                    results = await search.get_content_model()
                    if results.items:
                        series_item = results.items[0]
                        detail_path = series_item.detailPath
                        
                        tv_details = TVSeriesDetails(session)
                        detail_data = await tv_details.get_content(detail_path)
                        subject = detail_data.get('subject', {})
                        resource = detail_data.get('resource', {})
                        
                        return await build_tv_response(subject_id, detail_path, series_item, subject, resource, detail_data)
    except Exception as e:
        print(f"Worker fallback error: {e}")
    
    raise HTTPException(status_code=404, detail="TV series not found")


async def build_tv_response(subject_id: str, detail_path: str, series_item, subject: dict, resource: dict, detail_data: dict):
    """Build the complete TV series response"""
    
    # Extract seasons
    seasons_data = resource.get('seasons', [])
    seasons = []
    for season in seasons_data:
        se = season.get('se', 0)
        max_ep = season.get('maxEp', 0)
        resolutions = season.get('resolutions', [])
        
        # Generate episode URLs
        episodes = []
        for ep in range(1, min(max_ep + 1, 6)):
            episodes.append({
                "episode": ep,
                "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={se}&ep={ep}&resolution=720",
                "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={se}&ep={ep}&resolution=720"
            })
        
        seasons.append({
            "season": se,
            "max_episodes": max_ep,
            "available_qualities": [r.get('resolution') for r in resolutions],
            "episodes": episodes
        })
    
    # Extract poster
    cover = subject.get('cover', {})
    poster = None
    if cover:
        poster = {
            "url": cover.get('url'),
            "width": cover.get('width'),
            "height": cover.get('height')
        }
    
    # Extract backdrop
    stills = subject.get('stills', {})
    backdrop = None
    if stills:
        backdrop = {
            "url": stills.get('url'),
            "width": stills.get('width'),
            "height": stills.get('height')
        }
    
    # Extract trailer
    trailer = None
    trailer_data = subject.get('trailer', {})
    video_addr = trailer_data.get('videoAddress', {})
    if video_addr:
        trailer = {
            "url": video_addr.get('url'),
            "duration": video_addr.get('duration'),
            "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
        }
    
    # Extract cast
    cast = []
    stars = detail_data.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # Extract subtitles
    subtitles = []
    if series_item and hasattr(series_item, 'subtitles') and series_item.subtitles:
        subs = series_item.subtitles.split(',') if isinstance(series_item.subtitles, str) else series_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    title = series_item.title if series_item else subject.get('title', 'Unknown')
    year = series_item.releaseDate.year if series_item and series_item.releaseDate else None
    rating = series_item.imdbRatingValue if series_item else None
    genres = series_item.genre if isinstance(series_item.genre, list) else (series_item.genre.split(',') if series_item and series_item.genre else []) if series_item else []
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "data": {
            "id": subject_id,
            "megan_id": generate_megan_id(subject_id),
            "detail_path": detail_path,
            "title": title,
            "year": year,
            "genres": genres,
            "rating": rating,
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


# ============================================
# TV SEASONS
# ============================================

@router.get("/tv/{subject_id}/seasons")
async def get_tv_seasons(subject_id: str, detail_path: str = Query(...)):
    """Get seasons info - requires detail_path"""
    
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(detail_path)
    
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
        "id": subject_id,
        "total_seasons": len(seasons),
        "seasons": seasons
    }


# ============================================
# TV EPISODE
# ============================================

@router.get("/tv/{subject_id}/episode")
async def get_tv_episode(
    subject_id: str,
    detail_path: str = Query(...),
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Get download/stream URLs - requires detail_path"""
    
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "download": {
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
        },
        "stream": {
            "url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
        }
    }


# ============================================
# TV DOWNLOAD
# ============================================

@router.get("/tv/{subject_id}/download")
async def download_tv(
    subject_id: str,
    detail_path: str = Query(...),
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Download TV episode - requires detail_path"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
    }


@router.get("/tv/{subject_id}/stream")
async def stream_tv(
    subject_id: str,
    detail_path: str = Query(...),
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Stream TV episode - requires detail_path"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
    }


# ============================================
# LEGACY ENDPOINTS
# ============================================

@router.get("/tv/{title}")
async def get_tv_legacy(title: str, year: Optional[int] = None):
    """[DEPRECATED] Use search then /api/tv/{id}?detail_path={path}"""
    
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    subject_id = str(series_item.subjectId)
    detail_path = series_item.detailPath
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use search then /api/tv/{id}?detail_path={path}",
        "id": subject_id,
        "detail_path": detail_path,
        "url": f"{MEGAN_DOMAIN}/api/tv/{subject_id}?detail_path={detail_path}"
    }

