from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
import httpx

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


# ============================================
# MOVIE METADATA BY detail_path (The Correct Pattern!)
# ============================================

@router.get("/movie/{subject_id}")
async def get_movie_metadata(subject_id: str, detail_path: str = Query(None)):
    """
    Get complete movie metadata using detail_path.
    If detail_path not provided, tries to fetch from Worker first.
    """
    
    # If detail_path is provided, use it directly
    if detail_path:
        try:
            details_obj = MovieDetails(session)
            full_details = await details_obj.get_content(detail_path)
            subject = full_details.get('subject', {})
            movie_item = None
            
            # We still need movie_item for qualities - search by title
            title = subject.get('title')
            if title:
                search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
                results = await search_obj.get_content_model()
                if results.items:
                    movie_item = results.items[0]
            
            return await build_movie_response(subject_id, detail_path, movie_item, subject, full_details)
        except Exception as e:
            print(f"Error with detail_path: {e}")
    
    # Fallback: Try to get title from Worker Sources
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
                    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
                    results = await search_obj.get_content_model()
                    if results.items:
                        movie_item = results.items[0]
                        detail_path = movie_item.detailPath
                        
                        details_obj = MovieDetails(session)
                        full_details = await details_obj.get_content(detail_path)
                        subject = full_details.get('subject', {})
                        
                        return await build_movie_response(subject_id, detail_path, movie_item, subject, full_details)
    except Exception as e:
        print(f"Worker fallback error: {e}")
    
    raise HTTPException(status_code=404, detail="Movie not found")


async def build_movie_response(subject_id: str, detail_path: str, movie_item, subject: dict, full_details: dict):
    """Build the complete movie response"""
    
    # Get available qualities
    available_qualities = []
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie_item)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            for dl in download_data['downloads']:
                quality = f"{dl.get('resolution', 'unknown')}p"
                size_val = dl.get('size', '0')
                try:
                    size_mb = round(int(size_val) / 1024 / 1024, 2)
                except:
                    size_mb = 0
                
                available_qualities.append({
                    "quality": quality,
                    "size_mb": size_mb,
                    "format": dl.get('format', 'mp4')
                })
    except Exception as e:
        print(f"Downloads error: {e}")
    
    # Build download/stream URLs
    downloads = []
    streams = []
    for q in available_qualities:
        quality = q['quality']
        resolution = quality.replace('p', '')
        downloads.append({
            "quality": quality,
            "size_mb": q['size_mb'],
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&resolution={resolution}"
        })
        streams.append({
            "quality": quality,
            "url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&resolution={resolution}"
        })
    
    # Extract poster and backdrop
    poster = extract_image(movie_item) if movie_item else None
    
    backdrop = None
    if movie_item and hasattr(movie_item, 'stills') and movie_item.stills:
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
    if movie_item and hasattr(movie_item, 'subtitles') and movie_item.subtitles:
        subs = movie_item.subtitles.split(',') if isinstance(movie_item.subtitles, str) else movie_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    title = movie_item.title if movie_item else subject.get('title', 'Unknown')
    year = movie_item.releaseDate.year if movie_item and movie_item.releaseDate else None
    
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
            "release_date": movie_item.releaseDate.isoformat() if movie_item and movie_item.releaseDate else None,
            "duration": movie_item.duration if movie_item else None,
            "duration_minutes": movie_item.duration // 60 if movie_item and movie_item.duration else None,
            "genres": movie_item.genre if isinstance(movie_item.genre, list) else (movie_item.genre.split(',') if movie_item and movie_item.genre else []) if movie_item else [],
            "rating": movie_item.imdbRatingValue if movie_item else None,
            "description": subject.get('description', ''),
            "country": subject.get('countryName'),
            "poster": poster,
            "backdrop": backdrop,
            "trailer": trailer,
            "cast": cast,
            "subtitles": subtitles,
            "qualities": [q['quality'] for q in available_qualities],
            "downloads": downloads,
            "streams": streams
        }
    }


# ============================================
# MOVIE DOWNLOAD (Redirect to Worker)
# ============================================

@router.get("/movie/{subject_id}/download")
async def download_movie(
    subject_id: str,
    detail_path: str = Query(...),
    quality: str = Query("1080p", description="360p, 480p, 720p, 1080p")
):
    """Download movie - requires detail_path from search"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "id": subject_id,
        "quality": quality,
        "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&resolution={resolution}",
        "note": "Use download_url to get the file"
    }


@router.get("/movie/{subject_id}/stream")
async def stream_movie(
    subject_id: str,
    detail_path: str = Query(...),
    quality: str = Query("1080p", description="360p, 480p, 720p, 1080p")
):
    """Stream movie - requires detail_path from search"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "id": subject_id,
        "quality": quality,
        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&resolution={resolution}",
        "note": "Use stream_url to play the video"
    }


# ============================================
# LEGACY ENDPOINTS (Deprecated)
# ============================================

@router.get("/movies/{title}")
async def get_movie_legacy(title: str, year: Optional[int] = None):
    """[DEPRECATED] Use search then /api/movie/{id}?detail_path={path}"""
    
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
    detail_path = movie_item.detailPath
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use search then /api/movie/{id}?detail_path={path}",
        "id": subject_id,
        "detail_path": detail_path,
        "url": f"{MEGAN_DOMAIN}/api/movie/{subject_id}?detail_path={detail_path}"
    }

