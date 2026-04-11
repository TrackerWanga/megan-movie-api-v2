from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
import httpx

from moviebox_api.v2 import Search, Session, MovieDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/movies", tags=["movies"])

# Configuration
WORKER_URL = "https://movieapi2.trackerwanga254.workers.dev"
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"

session = Session()

def generate_megan_id(subject_id: str = None) -> str:
    """Generate Megan ID"""
    if subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"

def extract_image(item):
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

def get_session_token():
    """Get token for Worker authentication"""
    try:
        if hasattr(session, '_client'):
            client = session._client
            if hasattr(client, 'cookies'):
                for cookie in client.cookies.jar:
                    if cookie.name == 'token':
                        return cookie.value
    except:
        pass
    return None

# ============================================
# MOVIE DETAILS
# ============================================

@router.get("/{title}")
async def get_movie(title: str, year: Optional[int] = None):
    """Get complete movie details with download/stream URLs"""
    
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
    
    subject_id = str(movie_item.subjectId)
    detail_path = movie_item.detailPath
    
    # 2. Get full movie details
    details_obj = MovieDetails(session)
    full_details = await details_obj.get_content(detail_path)
    subject = full_details.get('subject', {})
    
    # 3. Get available qualities
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
    
    # 4. Build download/stream URLs
    downloads = []
    streams = []
    for q in available_qualities:
        quality = q['quality']
        downloads.append({
            "quality": quality,
            "size_mb": q['size_mb'],
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&resolution={quality.replace('p', '')}"
        })
        streams.append({
            "quality": quality,
            "url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&resolution={quality.replace('p', '')}"
        })
    
    # 5. Extract poster, backdrop, trailer
    poster = extract_image(movie_item)
    
    backdrop = None
    if hasattr(movie_item, 'stills') and movie_item.stills:
        backdrop = {
            "url": str(movie_item.stills.url),
            "width": movie_item.stills.width,
            "height": movie_item.stills.height
        }
    
    trailer = None
    if 'trailer' in subject and subject['trailer']:
        trailer_data = subject['trailer']
        if 'videoAddress' in trailer_data:
            trailer = {
                "url": trailer_data['videoAddress'].get('url'),
                "duration": trailer_data['videoAddress'].get('duration'),
                "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
            }
    
    # 6. Extract cast
    cast = []
    stars = full_details.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # 7. Extract subtitles
    subtitles = []
    if hasattr(movie_item, 'subtitles') and movie_item.subtitles:
        subs = movie_item.subtitles.split(',') if isinstance(movie_item.subtitles, str) else movie_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({
                    "language": sub.strip(),
                    "code": sub.strip()[:2].lower()
                })
    
    # 8. Build response
    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "data": {
            "movie": {
                "megan_id": generate_megan_id(subject_id),
                "subject_id": subject_id,
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
                "subtitles": subtitles
            },
            "downloads": downloads,
            "streams": streams,
            "total_qualities": len(available_qualities)
        }
    }

# ============================================
# QUICK DOWNLOAD (Redirect to Worker)
# ============================================

@router.get("/{title}/download")
async def download_movie(
    title: str,
    quality: str = Query("1080p", description="360p, 480p, 720p, 1080p"),
    year: Optional[int] = None
):
    """Get download URL for a movie"""
    
    # Search for movie
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_item = results.items[0]
    subject_id = str(movie_item.subjectId)
    detail_path = movie_item.detailPath
    
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "movie": {
            "title": movie_item.title,
            "year": movie_item.releaseDate.year if movie_item.releaseDate else None,
            "subject_id": subject_id
        },
        "download": {
            "quality": quality,
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&resolution={resolution}",
            "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&resolution={resolution}"
        },
        "note": "Use the URL immediately - it proxies through our streaming engine."
    }

# ============================================
# AVAILABLE QUALITIES
# ============================================

@router.get("/{title}/qualities")
async def get_qualities(title: str, year: Optional[int] = None):
    """Get available qualities for a movie"""
    
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_item = results.items[0]
    
    qualities = []
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie_item)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            for dl in download_data['downloads']:
                quality = f"{dl.get('resolution')}p"
                size_val = dl.get('size', '0')
                try:
                    size_mb = round(int(size_val) / 1024 / 1024, 2)
                except:
                    size_mb = 0
                
                qualities.append({
                    "quality": quality,
                    "size_mb": size_mb,
                    "format": dl.get('format', 'mp4')
                })
    except Exception as e:
        print(f"Error: {e}")
    
    return {
        "success": True,
        "movie": movie_item.title,
        "year": movie_item.releaseDate.year if movie_item.releaseDate else None,
        "qualities": qualities
    }

# ============================================
# SESSION REFRESH
# ============================================

@router.get("/session/refresh")
async def refresh_session():
    """Refresh MovieBox session token"""
    try:
        search_obj = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
        await search_obj.get_content_model()
        token = get_session_token()
        return {
            "success": True,
            "message": "Session refreshed",
            "has_token": token is not None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
