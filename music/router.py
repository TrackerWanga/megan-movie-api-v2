from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/music", tags=["music"])

session = Session()

def generate_megan_id(subject_id: str) -> str:
    """Generate Megan ID for music"""
    return f"megan-music-{subject_id}"

def extract_image(item) -> Optional[Dict]:
    """Extract cover image from item"""
    if hasattr(item, 'cover') and item.cover:
        cover = item.cover
        return {
            "url": str(cover.url) if hasattr(cover, 'url') else None,
            "width": cover.width if hasattr(cover, 'width') else None,
            "height": cover.height if hasattr(cover, 'height') else None,
            "format": cover.format if hasattr(cover, 'format') else None
        }
    return None

def format_music_item(item) -> Dict:
    """Format a music item for response"""
    duration_min = None
    if hasattr(item, 'duration') and item.duration:
        duration_min = item.duration // 60
        duration_sec = item.duration % 60
    
    return {
        "megan_id": generate_megan_id(str(item.subjectId)),
        "title": item.title if hasattr(item, 'title') else None,
        "year": item.releaseDate.year if hasattr(item, 'releaseDate') and item.releaseDate else None,
        "rating": item.imdbRatingValue if hasattr(item, 'imdbRatingValue') else None,
        "genres": item.genre if isinstance(item.genre, list) else [item.genre] if item.genre else [],
        "poster": extract_image(item),
        "detail_path": item.detailPath if hasattr(item, 'detailPath') else None,
        "subject_id": str(item.subjectId) if item.subjectId else None,
        "duration_seconds": item.duration if hasattr(item, 'duration') else None,
        "duration_minutes": duration_min,
        "has_download": item.hasResource if hasattr(item, 'hasResource') else False
    }

@router.get("/search")
async def search_music(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Results limit")
):
    """Search for music videos and songs"""
    
    search = Search(session, query=q, subject_type=SubjectType.MUSIC)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e), "query": q}
    
    items = []
    for item in results.items[:limit]:
        items.append(format_music_item(item))
    
    return {
        "success": True,
        "query": q,
        "total": len(items),
        "results": items
    }

@router.get("/artist/{name}")
async def get_artist_music(
    name: str,
    limit: int = Query(20, ge=1, le=50, description="Results limit")
):
    """Get music videos by artist name"""
    
    search = Search(session, query=name, subject_type=SubjectType.MUSIC)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    items = []
    for item in results.items[:limit]:
        items.append(format_music_item(item))
    
    return {
        "success": True,
        "artist": name,
        "total": len(items),
        "videos": items
    }

@router.get("/{detail_path}")
async def get_music_details(detail_path: str):
    """Get complete music video details including download URL and artists"""
    
    # Search for the music video by detail_path
    search = Search(session, query=detail_path, subject_type=SubjectType.MUSIC)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Music video not found")
    
    music_item = results.items[0]
    
    # Get full details
    from moviebox_api.v2 import MovieDetails
    details_obj = MovieDetails(session)
    full_details = await details_obj.get_content(music_item.detailPath)
    
    # Extract artists (stars)
    artists = []
    if full_details and 'stars' in full_details:
        for star in full_details.get('stars', []):
            artists.append({
                "name": star.get('name'),
                "role": star.get('character', 'Artist'),
                "avatar": star.get('avatarUrl')
            })
    
    # Get download URL
    download_url = None
    download_quality = None
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, music_item)
        download_data = await downloads_obj.get_content()
        if download_data and 'downloads' in download_data and download_data['downloads']:
            best = download_data['downloads'][0]
            download_url = best.get('url')
            download_quality = f"{best.get('resolution')}p"
    except Exception as e:
        print(f"Download error: {e}")
    
    # Extract duration
    duration_min = None
    duration_sec = None
    if hasattr(music_item, 'duration') and music_item.duration:
        duration_min = music_item.duration // 60
        duration_sec = music_item.duration % 60
    
    response = {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "music": {
                "megan_id": generate_megan_id(str(music_item.subjectId)),
                "title": music_item.title,
                "year": music_item.releaseDate.year if music_item.releaseDate else None,
                "rating": music_item.imdbRatingValue,
                "genres": music_item.genre if isinstance(music_item.genre, list) else [music_item.genre] if music_item.genre else [],
                "poster": extract_image(music_item),
                "duration": {
                    "seconds": music_item.duration,
                    "minutes": duration_min,
                    "remaining_seconds": duration_sec,
                    "formatted": f"{duration_min}:{duration_sec:02d}" if duration_min else None
                },
                "artists": artists,
                "download": {
                    "available": download_url is not None,
                    "quality": download_quality,
                    "url": download_url
                }
            }
        }
    }
    
    return response

@router.get("/download/{detail_path}")
async def get_music_download(detail_path: str):
    """Get download URL for a music video"""
    
    search = Search(session, query=detail_path, subject_type=SubjectType.MUSIC)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Music video not found")
    
    music_item = results.items[0]
    
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, music_item)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            return {
                "success": True,
                "megan_id": generate_megan_id(str(music_item.subjectId)),
                "title": music_item.title,
                "downloads": [
                    {
                        "quality": f"{dl.get('resolution')}p",
                        "size_mb": round(int(dl.get('size', 0)) / 1024 / 1024, 2),
                        "url": dl.get('url')
                    }
                    for dl in download_data['downloads']
                ]
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "No download available"}

@router.get("/trending")
async def get_trending_music(limit: int = Query(20, ge=1, le=50)):
    """Get trending music videos"""
    
    search = Search(session, query="trending", subject_type=SubjectType.MUSIC)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    items = []
    for item in results.items[:limit]:
        items.append(format_music_item(item))
    
    return {
        "success": True,
        "total": len(items),
        "trending": items
    }

@router.get("/popular")
async def get_popular_music(limit: int = Query(20, ge=1, le=50)):
    """Get popular music videos"""
    
    search = Search(session, query="popular", subject_type=SubjectType.MUSIC)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    items = []
    for item in results.items[:limit]:
        items.append(format_music_item(item))
    
    return {
        "success": True,
        "total": len(items),
        "popular": items
    }

@router.get("/latest")
async def get_latest_music(limit: int = Query(20, ge=1, le=50)):
    """Get latest music videos"""
    
    search = Search(session, query="latest", subject_type=SubjectType.MUSIC)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    items = []
    for item in results.items[:limit]:
        items.append(format_music_item(item))
    
    return {
        "success": True,
        "total": len(items),
        "latest": items
    }
