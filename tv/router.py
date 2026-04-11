from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from moviebox_api.v2 import Search, Session, TVSeriesDetails
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/tv", tags=["tv_series"])

# Configuration
WORKER_URL = "https://movieapi2.trackerwanga254.workers.dev"
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
# TV SEARCH
# ============================================

@router.get("/search")
async def search_tv(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50)
):
    """Search for TV series"""
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
        "query": q,
        "total": len(items),
        "results": items
    }

# ============================================
# TV SERIES DETAILS
# ============================================

@router.get("/{title}")
async def get_tv_series(title: str, year: Optional[int] = None):
    """Get complete TV series data"""
    
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
    
    subject_id = str(series_item.subjectId)
    detail_path = series_item.detailPath
    
    # 2. Get series details
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(detail_path)
    subject = detail_data.get('subject', {})
    
    # 3. Extract seasons info
    resource = detail_data.get('resource', {})
    seasons_data = resource.get('seasons', [])
    
    seasons = []
    for season in seasons_data:
        se = season.get('se', 0)
        max_ep = season.get('maxEp', 0)
        resolutions = season.get('resolutions', [])
        
        # Build episode download URLs for this season
        episodes = []
        for ep in range(1, max_ep + 1):
            episodes.append({
                "episode": ep,
                "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={se}&ep={ep}&resolution=720",
                "watch_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={se}&ep={ep}&resolution=720"
            })
        
        seasons.append({
            "season": se,
            "max_episodes": max_ep,
            "available_qualities": [r.get('resolution') for r in resolutions],
            "episodes": episodes[:5]  # First 5 episodes as preview
        })
    
    # 4. Extract poster
    cover = subject.get('cover', {})
    poster = None
    if cover:
        poster = {
            "url": cover.get('url'),
            "width": cover.get('width'),
            "height": cover.get('height')
        }
    
    # 5. Extract backdrop
    stills = subject.get('stills', {})
    backdrop = None
    if stills:
        backdrop = {
            "url": stills.get('url'),
            "width": stills.get('width'),
            "height": stills.get('height')
        }
    
    # 6. Extract trailer
    trailer = None
    trailer_data = subject.get('trailer', {})
    video_addr = trailer_data.get('videoAddress', {})
    if video_addr:
        trailer = {
            "url": video_addr.get('url'),
            "duration": video_addr.get('duration'),
            "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
        }
    
    # 7. Extract cast
    cast = []
    stars = detail_data.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # 8. Extract subtitles
    subtitles = []
    if hasattr(series_item, 'subtitles') and series_item.subtitles:
        subs = series_item.subtitles.split(',') if isinstance(series_item.subtitles, str) else series_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    # 9. Build response
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
            },
            "download_note": "Use /api/tv/{title}/episode?season=X&episode=Y&quality=720 for specific episodes"
        }
    }

# ============================================
# EPISODE DOWNLOAD
# ============================================

@router.get("/{title}/episode")
async def get_tv_episode(
    title: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p"),
    year: Optional[int] = None
):
    """Get download/stream URLs for a specific episode"""
    
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
    
    subject_id = str(series_item.subjectId)
    detail_path = series_item.detailPath
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "series": series_item.title,
        "season": season,
        "episode": episode,
        "quality": quality,
        "download": {
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
        },
        "stream": {
            "url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
        },
        "note": "URLs proxy through Megan Stream Engine - works worldwide!"
    }

# ============================================
# SEASONS INFO
# ============================================

@router.get("/{title}/seasons")
async def get_tv_seasons(title: str, year: Optional[int] = None):
    """Get all seasons info for a TV series"""
    
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
            "episodes": max_ep,
            "available_qualities": [r.get('resolution') for r in resolutions]
        })
    
    return {
        "success": True,
        "title": series_item.title,
        "subject_id": str(series_item.subjectId),
        "detail_path": series_item.detailPath,
        "total_seasons": len(seasons),
        "seasons": seasons
    }

# ============================================
# CATALOG (from Worker)
# ============================================

@router.get("/catalog/all")
async def get_tv_catalog():
    """Get all TV series catalog from Worker"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{WORKER_URL}/tv-series")
            if resp.status_code == 200:
                return {"success": True, "source": "worker", "data": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False, "error": "Failed to fetch catalog"}
