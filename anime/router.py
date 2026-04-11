from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from moviebox_api.v2 import Search, Session, TVSeriesDetails
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/anime", tags=["anime"])

MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"
session = Session()

def generate_megan_id(subject_id: str) -> str:
    return f"megan-anime-{subject_id}"

def extract_image(item) -> Optional[Dict]:
    if hasattr(item, 'cover') and item.cover:
        cover = item.cover
        return {
            "url": str(cover.url) if hasattr(cover, 'url') else None,
            "width": cover.width if hasattr(cover, 'width') else None,
            "height": cover.height if hasattr(cover, 'height') else None
        }
    return None

def is_anime(item) -> bool:
    if hasattr(item, 'genre') and item.genre:
        genres = item.genre if isinstance(item.genre, list) else [item.genre]
        return any('anime' in g.lower() for g in genres)
    return False

def format_anime_item(item) -> Dict:
    return {
        "megan_id": generate_megan_id(str(item.subjectId)),
        "title": item.title if hasattr(item, 'title') else None,
        "year": item.releaseDate.year if hasattr(item, 'releaseDate') and item.releaseDate else None,
        "rating": item.imdbRatingValue if hasattr(item, 'imdbRatingValue') else None,
        "poster": extract_image(item),
        "detail_path": item.detailPath if hasattr(item, 'detailPath') else None,
        "subject_id": str(item.subjectId) if item.subjectId else None,
        "type": "tv_series" if item.subjectType == 2 else "movie"
    }

@router.get("/search")
async def search_anime(q: str = Query(...), limit: int = Query(20)):
    search_tv = Search(session, query=q, subject_type=SubjectType.TV_SERIES)
    search_movies = Search(session, query=q, subject_type=SubjectType.MOVIES)
    
    try:
        tv_results = await search_tv.get_content_model()
        movie_results = await search_movies.get_content_model()
        
        items = []
        for item in tv_results.items + movie_results.items:
            if is_anime(item):
                items.append(format_anime_item(item))
        
        return {"success": True, "query": q, "total": len(items[:limit]), "results": items[:limit]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/{detail_path}")
async def get_anime_details(detail_path: str):
    search = Search(session, query=detail_path, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    anime_item = None
    for item in results.items:
        if item.detailPath == detail_path and is_anime(item):
            anime_item = item
            break
    
    if not anime_item:
        raise HTTPException(status_code=404, detail="Anime not found")
    
    subject_id = str(anime_item.subjectId)
    
    # Get seasons
    seasons = []
    try:
        tv_details = TVSeriesDetails(session)
        detail_data = await tv_details.get_content(detail_path)
        resource = detail_data.get('resource', {})
        for s in resource.get('seasons', []):
            seasons.append({
                "season": s.get('se', 0),
                "episodes": s.get('maxEp', 0)
            })
    except:
        pass
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "anime": {
                "megan_id": generate_megan_id(subject_id),
                "subject_id": subject_id,
                "detail_path": detail_path,
                "title": anime_item.title,
                "year": anime_item.releaseDate.year if anime_item.releaseDate else None,
                "rating": anime_item.imdbRatingValue,
                "poster": extract_image(anime_item),
                "seasons": seasons,
                "total_seasons": len(seasons)
            }
        }
    }

@router.get("/{detail_path}/episode")
async def get_anime_episode(detail_path: str, season: int = Query(...), episode: int = Query(...), quality: str = Query("720p")):
    search = Search(session, query=detail_path, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    anime_item = None
    for item in results.items:
        if item.detailPath == detail_path and is_anime(item):
            anime_item = item
            break
    
    if not anime_item:
        raise HTTPException(status_code=404, detail="Anime not found")
    
    subject_id = str(anime_item.subjectId)
    resolution = quality.replace('p', '')
    
    return {
        "success": True,
        "title": anime_item.title,
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

@router.get("/popular")
async def get_popular(limit: int = 20):
    search = Search(session, query="popular", subject_type=SubjectType.TV_SERIES)
    try:
        results = await search.get_content_model()
        items = [format_anime_item(item) for item in results.items if is_anime(item)]
        return {"success": True, "total": len(items[:limit]), "results": items[:limit]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/trending")
async def get_trending(limit: int = 20):
    search = Search(session, query="trending", subject_type=SubjectType.TV_SERIES)
    try:
        results = await search.get_content_model()
        items = [format_anime_item(item) for item in results.items if is_anime(item)]
        return {"success": True, "total": len(items[:limit]), "results": items[:limit]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/latest")
async def get_latest(limit: int = 20):
    search = Search(session, query="latest", subject_type=SubjectType.TV_SERIES)
    try:
        results = await search.get_content_model()
        items = [format_anime_item(item) for item in results.items if is_anime(item)]
        return {"success": True, "total": len(items[:limit]), "results": items[:limit]}
    except Exception as e:
        return {"success": False, "error": str(e)}
