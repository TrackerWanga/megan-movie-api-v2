from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
import httpx
import asyncio

from moviebox_api.v2 import Search, Session, MovieDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api", tags=["movies"])

# Configuration
WORKER_URL = "https://streamapi.megan.qzz.io"
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"

session = Session()

def generate_megan_id(subject_id: str = None) -> str:
    if subject_id:
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

async def fetch_worker_sources(subject_id: str, detail_path: str) -> Optional[dict]:
    """Fetch from Worker Sources API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{WORKER_URL}/api/stream/{subject_id}",
                params={"detail_path": detail_path}
            )
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    return None


# ============================================
# UNIFIED MOVIE ENDPOINT (Combines Python + Worker)
# ============================================

@router.get("/movie/{subject_id}")
async def get_movie_unified(subject_id: str):
    """Get complete movie details - combines Python metadata + Worker sources"""
    
    # First, try to get basic info from Worker Sources to get the title
    worker_sources = await fetch_worker_sources(subject_id, subject_id)
    
    if not worker_sources:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    title = worker_sources.get('title', 'Unknown')
    
    # Get rich metadata from Python MovieBox
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        # Fallback to basic response
        return {
            "success": True,
            "api": "Megan Movie API",
            "creator": "Megan / Wanga",
            "data": {
                "movie": {
                    "id": subject_id,
                    "title": title,
                    "poster": None,
                    "qualities": [s.get('resolution') for s in worker_sources.get('sources', [])],
                    "downloads": [],
                    "streams": []
                }
            }
        }
    
    movie_item = results.items[0]
    detail_path = movie_item.detailPath
    
    # Get Python full details
    details_obj = MovieDetails(session)
    full_details = await details_obj.get_content(detail_path)
    subject = full_details.get('subject', {})
    
    # Get Worker Detail for dubs
    worker_detail = await fetch_worker_detail(detail_path)
    
    # Get qualities from Worker Sources
    qualities = []
    downloads = []
    streams = []
    
    for source in worker_sources.get('sources', []):
        resolution = source.get('resolution', 'unknown')
        quality = resolution if 'p' in resolution else f"{resolution}p"
        url = source.get('url', '')
        size_bytes = source.get('size_bytes', '0')
        
        try:
            size_mb = round(int(size_bytes) / 1024 / 1024, 2)
        except:
            size_mb = 0
        
        qualities.append(quality)
        downloads.append({
            "quality": quality,
            "size_mb": size_mb,
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&resolution={resolution.replace('p', '')}"
        })
        streams.append({
            "quality": quality,
            "url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&resolution={resolution.replace('p', '')}"
        })
    
    # Extract poster and backdrop
    poster = extract_image(movie_item)
    
    backdrop = None
    if hasattr(movie_item, 'stills') and movie_item.stills:
        backdrop = {
            "url": str(movie_item.stills.url),
            "width": movie_item.stills.width,
            "height": movie_item.stills.height
        }
    
    # Extract trailer
    trailer = None
    if 'trailer' in subject and subject['trailer']:
        trailer_data = subject['trailer']
        if 'videoAddress' in trailer_data:
            trailer = {
                "url": trailer_data['videoAddress'].get('url'),
                "duration": trailer_data['videoAddress'].get('duration'),
                "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
            }
    
    # Extract cast
    cast = []
    stars = full_details.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # Extract subtitles
    subtitles = []
    if hasattr(movie_item, 'subtitles') and movie_item.subtitles:
        subs = movie_item.subtitles.split(',') if isinstance(movie_item.subtitles, str) else movie_item.subtitles
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
            "movie": {
                "id": subject_id,
                "megan_id": generate_megan_id(subject_id),
                "detail_path": detail_path,
                "title": movie_item.title,
                "year": movie_item.releaseDate.year if movie_item.releaseDate else None,
                "release_date": movie_item.releaseDate.isoformat() if movie_item.releaseDate else None,
                "duration": movie_item.duration,
                "duration_minutes": movie_item.duration // 60 if movie_item.duration else None,
                "genres": movie_item.genre if isinstance(movie_item.genre, list) else (movie_item.genre.split(',') if movie_item.genre else []),
                "rating": movie_item.imdbRatingValue,
                "description": subject.get('description', movie_item.description),
                "country": subject.get('countryName'),
                "poster": poster,
                "backdrop": backdrop,
                "trailer": trailer,
                "cast": cast,
                "subtitles": subtitles,
                "dubs": dubs
            },
            "qualities": qualities,
            "downloads": downloads,
            "streams": streams
        }
    }


@router.get("/movie/{subject_id}/download")
async def download_movie(
    subject_id: str,
    quality: str = Query("1080p", description="360p, 480p, 720p, 1080p")
):
    """Download movie by ID"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "id": subject_id,
        "quality": quality,
        "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={subject_id}&resolution={resolution}"
    }


@router.get("/movie/{subject_id}/stream")
async def stream_movie(
    subject_id: str,
    quality: str = Query("1080p", description="360p, 480p, 720p, 1080p")
):
    """Stream movie by ID"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "id": subject_id,
        "quality": quality,
        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={subject_id}&resolution={resolution}"
    }


@router.get("/movie/{subject_id}/sources")
async def get_movie_sources(subject_id: str):
    """Get all available qualities"""
    worker_sources = await fetch_worker_sources(subject_id, subject_id)
    
    if worker_sources:
        return {
            "success": True,
            "id": subject_id,
            "sources": worker_sources.get('sources', []),
            "count": worker_sources.get('count', 0)
        }
    
    return {"success": False, "error": "Failed to fetch sources", "sources": []}


# ============================================
# LEGACY ENDPOINTS (Deprecated)
# ============================================

@router.get("/movies/{title}")
async def get_movie_legacy(title: str, year: Optional[int] = None):
    """[DEPRECATED] Use /movie/{id} instead"""
    
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_item = None
    for item in results.items:
        if year and item.releaseDate and item.releaseDate.year == year:
            movie_item = item
            break
    if not movie_item:
        movie_item = results.items[0]
    
    subject_id = str(movie_item.subjectId)
    
    # Redirect to new endpoint
    return {
        "success": True,
        "deprecated": True,
        "message": "Use /api/movie/{id} instead",
        "id": subject_id,
        "url": f"{MEGAN_DOMAIN}/api/movie/{subject_id}"
    }

