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

# ============================================
# NEW RESTful ENDPOINTS (ID-based) - PREFERRED
# ============================================

@router.get("/movie/{subject_id}")
async def get_movie_by_id(subject_id: str):
    """Get complete movie details by subject_id"""
    
    # Search for movie using subject_id as reference
    search_obj = Search(session, query=subject_id, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        # Try to get basic info from Worker sources
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                sources_resp = await client.get(
                    f"{WORKER_URL}/api/stream/{subject_id}",
                    params={"detail_path": subject_id}
                )
                if sources_resp.status_code == 200:
                    sources_data = sources_resp.json()
                    return {
                        "success": True,
                        "api": "Megan Movie API",
                        "creator": "Megan / Wanga",
                        "data": {
                            "movie": {
                                "megan_id": generate_megan_id(subject_id),
                                "subject_id": subject_id,
                                "title": sources_data.get('title', 'Unknown'),
                                "available_qualities": []
                            },
                            "downloads": [],
                            "streams": []
                        }
                    }
        except:
            pass
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_item = results.items[0]
    detail_path = movie_item.detailPath
    
    # Get full movie details
    details_obj = MovieDetails(session)
    full_details = await details_obj.get_content(detail_path)
    subject = full_details.get('subject', {})
    
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
            "url": f"{MEGAN_DOMAIN}/api/movie/{subject_id}/download?quality={quality}"
        })
        streams.append({
            "quality": quality,
            "url": f"{MEGAN_DOMAIN}/api/movie/{subject_id}/stream?quality={quality}"
        })
    
    # Extract poster, backdrop, trailer
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


@router.get("/movie/{subject_id}/download")
async def download_movie_by_id(
    subject_id: str,
    quality: str = Query("1080p", description="360p, 480p, 720p, 1080p")
):
    """Download movie by subject_id"""
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "subject_id": subject_id,
        "quality": quality,
        "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={subject_id}&resolution={resolution}",
        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={subject_id}&resolution={resolution}",
        "note": "Use download_url to get the file"
    }


@router.get("/movie/{subject_id}/stream")
async def stream_movie_by_id(
    subject_id: str,
    quality: str = Query("1080p", description="360p, 480p, 720p, 1080p")
):
    """Stream movie by subject_id"""
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "subject_id": subject_id,
        "quality": quality,
        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={subject_id}&resolution={resolution}"
    }


@router.get("/movie/{subject_id}/sources")
async def get_movie_sources_by_id(subject_id: str):
    """Get all available sources/qualities for a movie"""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{WORKER_URL}/api/stream/{subject_id}",
                params={"detail_path": subject_id}
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "subject_id": subject_id,
                    "sources": data.get('sources', []),
                    "count": data.get('count', 0)
                }
    except Exception as e:
        print(f"Sources error: {e}")
    
    return {"success": False, "error": "Failed to fetch sources", "sources": []}


# ============================================
# LEGACY ENDPOINTS (Title-based) - DEPRECATED
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
    detail_path = movie_item.detailPath
    
    details_obj = MovieDetails(session)
    full_details = await details_obj.get_content(detail_path)
    subject = full_details.get('subject', {})
    
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
    except:
        pass
    
    downloads = []
    streams = []
    for q in available_qualities:
        quality = q['quality']
        resolution = quality.replace('p', '')
        downloads.append({
            "quality": quality,
            "size_mb": q['size_mb'],
            "url": f"{MEGAN_DOMAIN}/api/movie/{subject_id}/download?quality={quality}"
        })
        streams.append({
            "quality": quality,
            "url": f"{MEGAN_DOMAIN}/api/movie/{subject_id}/stream?quality={quality}"
        })
    
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
    
    cast = []
    stars = full_details.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    subtitles = []
    if hasattr(movie_item, 'subtitles') and movie_item.subtitles:
        subs = movie_item.subtitles.split(',') if isinstance(movie_item.subtitles, str) else movie_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "deprecated": True,
        "message": "Use /api/movie/{id} instead",
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


@router.get("/movies/{title}/download")
async def download_movie_legacy(title: str, quality: str = Query("1080p"), year: Optional[int] = None):
    """[DEPRECATED] Use /movie/{id}/download instead"""
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_item = results.items[0]
    subject_id = str(movie_item.subjectId)
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use /api/movie/{id}/download instead",
        "movie": {
            "title": movie_item.title,
            "subject_id": subject_id
        },
        "download": {
            "quality": quality,
            "url": f"{MEGAN_DOMAIN}/api/movie/{subject_id}/download?quality={quality}"
        }
    }


@router.get("/movies/{title}/qualities")
async def get_qualities_legacy(title: str, year: Optional[int] = None):
    """[DEPRECATED] Use /movie/{id}/sources instead"""
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_item = results.items[0]
    subject_id = str(movie_item.subjectId)
    
    qualities = []
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, movie_item)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            for dl in download_data['downloads']:
                qualities.append({
                    "quality": f"{dl.get('resolution')}p",
                    "size_mb": round(int(dl.get('size', 0)) / 1024 / 1024, 2) if dl.get('size') else 0,
                    "format": dl.get('format', 'mp4')
                })
    except:
        pass
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use /api/movie/{id}/sources instead",
        "movie": movie_item.title,
        "subject_id": subject_id,
        "qualities": qualities
    }

