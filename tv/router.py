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

async def fetch_worker_detail(slug: str) -> Optional[dict]:
    """Fetch from Worker Detail API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WORKER_URL}/detail/{slug}")
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    return None

async def fetch_worker_episodes(slug: str) -> Optional[dict]:
    """Fetch from Worker Episodes API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WORKER_URL}/episodes/{slug}")
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    return None


# ============================================
# UNIFIED TV ENDPOINT (Combines Python + Worker)
# ============================================

@router.get("/tv/{subject_id}")
async def get_tv_unified(subject_id: str):
    """Get complete TV series details - combines Python metadata + Worker episodes"""
    
    # We need the slug/detail_path to fetch from Worker
    # First try to search by ID
    search = Search(session, query=subject_id, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    detail_path = series_item.detailPath
    title = series_item.title
    
    # Fetch from all sources in parallel
    python_details = TVSeriesDetails(session)
    worker_detail = await fetch_worker_detail(detail_path)
    worker_episodes = await fetch_worker_episodes(detail_path)
    
    # Get Python full details
    detail_data = await python_details.get_content(detail_path)
    subject = detail_data.get('subject', {})
    resource = detail_data.get('resource', {})
    
    # Get the correct ID from Worker
    correct_id = subject_id
    if worker_detail and worker_detail.get('metadata', {}).get('id'):
        correct_id = worker_detail['metadata']['id']
    
    # Build seasons with episode URLs from Worker
    seasons = []
    python_seasons = resource.get('seasons', [])
    worker_seasons = worker_episodes.get('seasons', []) if worker_episodes else []
    
    for py_season in python_seasons:
        se = py_season.get('se', 0)
        max_ep = py_season.get('maxEp', 0)
        resolutions = py_season.get('resolutions', [])
        
        # Find matching worker season
        worker_season = next((s for s in worker_seasons if s.get('season') == se), None)
        
        episodes = []
        if worker_season:
            for ep in worker_season.get('episodes', [])[:10]:  # First 10 episodes
                episodes.append({
                    "episode": ep.get('ep'),
                    "name": ep.get('name', f'Episode {ep.get("ep")}'),
                    "download_url": f"{MEGAN_DOMAIN}{ep.get('download_url', '')}" if ep.get('download_url') else None,
                    "stream_url": f"{MEGAN_DOMAIN}{ep.get('watch_url', '')}" if ep.get('watch_url') else None
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
    if hasattr(series_item, 'subtitles') and series_item.subtitles:
        subs = series_item.subtitles.split(',') if isinstance(series_item.subtitles, str) else series_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    # Extract dubs from Worker
    dubs = []
    if worker_detail and worker_detail.get('metadata', {}).get('dubs'):
        for dub in worker_detail['metadata']['dubs']:
            dubs.append({
                "language": dub.get('lanName'),
                "code": dub.get('lanCode'),
                "subject_id": dub.get('subjectId'),
                "detail_path": dub.get('detailPath')
            })
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "data": {
            "series": {
                "id": correct_id,
                "megan_id": generate_megan_id(correct_id),
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
                "dubs": dubs,
                "seasons": seasons,
                "total_seasons": len(seasons)
            }
        }
    }


@router.get("/tv/{subject_id}/seasons")
async def get_tv_seasons(subject_id: str):
    """Get seasons info for a TV series"""
    
    search = Search(session, query=subject_id, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    detail_path = series_item.detailPath
    
    # Get episodes from Worker
    worker_episodes = await fetch_worker_episodes(detail_path)
    
    if worker_episodes:
        return {
            "success": True,
            "id": worker_episodes.get('subject_id', subject_id),
            "title": series_item.title,
            "total_seasons": worker_episodes.get('total_seasons', 0),
            "seasons": worker_episodes.get('seasons', [])
        }
    
    # Fallback to Python
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
        "title": series_item.title,
        "total_seasons": len(seasons),
        "seasons": seasons
    }


@router.get("/tv/{subject_id}/episode")
async def get_tv_episode(
    subject_id: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Get download/stream URLs for a specific episode"""
    
    resolution = quality.replace('p', '')
    
    # Search for series to get title
    search = Search(session, query=subject_id, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    title = results.items[0].title if results.items else "Unknown"
    
    return {
        "success": True,
        "id": subject_id,
        "series": title,
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
async def download_tv(
    subject_id: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Download TV episode by ID"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={subject_id}&se={season}&ep={episode}&resolution={resolution}"
    }


@router.get("/tv/{subject_id}/stream")
async def stream_tv(
    subject_id: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Stream TV episode by ID"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "id": subject_id,
        "season": season,
        "episode": episode,
        "quality": quality,
        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={subject_id}&se={season}&ep={episode}&resolution={resolution}"
    }


# ============================================
# LEGACY ENDPOINTS (Deprecated)
# ============================================

@router.get("/tv/{title}")
async def get_tv_legacy(title: str, year: Optional[int] = None):
    """[DEPRECATED] Use /tv/{id} instead"""
    
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    subject_id = str(series_item.subjectId)
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use /api/tv/{id} instead",
        "id": subject_id,
        "url": f"{MEGAN_DOMAIN}/api/tv/{subject_id}"
    }

