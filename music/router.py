from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/music", tags=["music"])

MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"
session = Session()

def generate_megan_id(subject_id: str) -> str:
    return f"megan-music-{subject_id}"

def extract_image(item) -> Optional[Dict]:
    if hasattr(item, 'cover') and item.cover:
        cover = item.cover
        return {
            "url": str(cover.url) if hasattr(cover, 'url') else None,
            "width": cover.width if hasattr(cover, 'width') else None,
            "height": cover.height if hasattr(cover, 'height') else None
        }
    return None

def format_music_item(item) -> Dict:
    return {
        "megan_id": generate_megan_id(str(item.subjectId)),
        "title": item.title if hasattr(item, 'title') else None,
        "year": item.releaseDate.year if hasattr(item, 'releaseDate') and item.releaseDate else None,
        "rating": item.imdbRatingValue if hasattr(item, 'imdbRatingValue') else None,
        "poster": extract_image(item),
        "detail_path": item.detailPath if hasattr(item, 'detailPath') else None,
        "subject_id": str(item.subjectId) if item.subjectId else None,
        "duration_seconds": item.duration if hasattr(item, 'duration') else None
    }

@router.get("/search")
async def search_music(q: str = Query(...), limit: int = Query(20)):
    search = Search(session, query=q, subject_type=SubjectType.MUSIC)
    try:
        results = await search.get_content_model()
        items = [format_music_item(item) for item in results.items[:limit]]
        return {"success": True, "query": q, "total": len(items), "results": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/{detail_path}")
async def get_music_details(detail_path: str):
    search = Search(session, query=detail_path, subject_type=SubjectType.MUSIC)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Music video not found")
    
    music_item = results.items[0]
    subject_id = str(music_item.subjectId)
    
    # Get qualities
    qualities = []
    try:
        dl_obj = DownloadableSingleFilesDetail(session, music_item)
        dl_data = await dl_obj.get_content()
        if dl_data and 'downloads' in dl_data:
            for dl in dl_data['downloads']:
                qualities.append(f"{dl.get('resolution')}p")
    except:
        pass
    
    # Build download URLs
    downloads = []
    for q in qualities:
        resolution = q.replace('p', '')
        downloads.append({
            "quality": q,
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&resolution={resolution}"
        })
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "music": {
                "megan_id": generate_megan_id(subject_id),
                "subject_id": subject_id,
                "detail_path": detail_path,
                "title": music_item.title,
                "year": music_item.releaseDate.year if music_item.releaseDate else None,
                "rating": music_item.imdbRatingValue,
                "poster": extract_image(music_item),
                "duration_seconds": music_item.duration if hasattr(music_item, 'duration') else None,
                "downloads": downloads
            }
        }
    }

@router.get("/trending")
async def get_trending(limit: int = 20):
    search = Search(session, query="trending", subject_type=SubjectType.MUSIC)
    try:
        results = await search.get_content_model()
        items = [format_music_item(item) for item in results.items[:limit]]
        return {"success": True, "total": len(items), "trending": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/popular")
async def get_popular(limit: int = 20):
    search = Search(session, query="popular", subject_type=SubjectType.MUSIC)
    try:
        results = await search.get_content_model()
        items = [format_music_item(item) for item in results.items[:limit]]
        return {"success": True, "total": len(items), "popular": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/latest")
async def get_latest(limit: int = 20):
    search = Search(session, query="latest", subject_type=SubjectType.MUSIC)
    try:
        results = await search.get_content_model()
        items = [format_music_item(item) for item in results.items[:limit]]
        return {"success": True, "total": len(items), "latest": items}
    except Exception as e:
        return {"success": False, "error": str(e)}
