from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.download import DownloadableTVSeriesFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/anime", tags=["anime"])

session = Session()

def generate_megan_id(subject_id: str) -> str:
    """Generate Megan ID for anime"""
    return f"megan-anime-{subject_id}"

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

def is_anime(item) -> bool:
    """Check if item is anime (genre contains 'anime')"""
    if hasattr(item, 'genre') and item.genre:
        genres = item.genre if isinstance(item.genre, list) else [item.genre]
        return any('anime' in g.lower() for g in genres)
    return False

def format_anime_item(item) -> Dict:
    """Format an anime item for response"""
    return {
        "megan_id": generate_megan_id(str(item.subjectId)),
        "title": item.title if hasattr(item, 'title') else None,
        "year": item.releaseDate.year if hasattr(item, 'releaseDate') and item.releaseDate else None,
        "rating": item.imdbRatingValue if hasattr(item, 'imdbRatingValue') else None,
        "genres": item.genre if isinstance(item.genre, list) else [item.genre] if item.genre else [],
        "poster": extract_image(item),
        "detail_path": item.detailPath if hasattr(item, 'detailPath') else None,
        "subject_id": str(item.subjectId) if item.subjectId else None,
        "type": "movie" if item.subjectType == 1 else "tv_series",
        "has_download": item.hasResource if hasattr(item, 'hasResource') else False
    }

@router.get("/search")
async def search_anime(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Results limit")
):
    """Search for anime by title"""
    
    # Search in TV_SERIES and MOVIES (anime can be in both)
    search_tv = Search(session, query=q, subject_type=SubjectType.TV_SERIES)
    search_movies = Search(session, query=q, subject_type=SubjectType.MOVIES)
    
    try:
        tv_results = await search_tv.get_content_model()
        movie_results = await search_movies.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e), "query": q}
    
    # Combine and filter for anime
    anime_items = []
    for item in tv_results.items:
        if is_anime(item):
            anime_items.append(format_anime_item(item))
    
    for item in movie_results.items:
        if is_anime(item):
            anime_items.append(format_anime_item(item))
    
    return {
        "success": True,
        "query": q,
        "total": len(anime_items[:limit]),
        "results": anime_items[:limit]
    }

@router.get("/popular")
async def get_popular_anime(limit: int = Query(20, ge=1, le=50)):
    """Get popular anime"""
    
    search = Search(session, query="popular", subject_type=SubjectType.TV_SERIES)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    anime_items = []
    for item in results.items:
        if is_anime(item):
            anime_items.append(format_anime_item(item))
    
    return {
        "success": True,
        "total": len(anime_items[:limit]),
        "popular": anime_items[:limit]
    }

@router.get("/trending")
async def get_trending_anime(limit: int = Query(20, ge=1, le=50)):
    """Get trending anime"""
    
    search = Search(session, query="trending", subject_type=SubjectType.TV_SERIES)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    anime_items = []
    for item in results.items:
        if is_anime(item):
            anime_items.append(format_anime_item(item))
    
    return {
        "success": True,
        "total": len(anime_items[:limit]),
        "trending": anime_items[:limit]
    }

@router.get("/latest")
async def get_latest_anime(limit: int = Query(20, ge=1, le=50)):
    """Get latest anime releases"""
    
    search = Search(session, query="latest", subject_type=SubjectType.TV_SERIES)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    anime_items = []
    for item in results.items:
        if is_anime(item):
            anime_items.append(format_anime_item(item))
    
    return {
        "success": True,
        "total": len(anime_items[:limit]),
        "latest": anime_items[:limit]
    }

@router.get("/{detail_path}")
async def get_anime_details(detail_path: str):
    """Get complete anime details including episodes and download"""
    
    # Search for the anime
    search_tv = Search(session, query=detail_path, subject_type=SubjectType.TV_SERIES)
    results = await search_tv.get_content_model()
    
    anime_item = None
    for item in results.items:
        if item.detailPath == detail_path and is_anime(item):
            anime_item = item
            break
    
    if not anime_item:
        raise HTTPException(status_code=404, detail="Anime not found")
    
    # Get full details
    from moviebox_api.v2 import TVSeriesDetails
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(anime_item.detailPath)
    
    # Extract seasons info
    resource = detail_data.get('resource', {})
    seasons_data = resource.get('seasons', [])
    
    seasons = []
    for season in seasons_data:
        seasons.append({
            "season": season.get('se', 0),
            "max_episodes": season.get('maxEp', 0),
            "resolutions": [r.get('resolution') for r in season.get('resolutions', [])]
        })
    
    # Extract cast/voice actors
    cast = []
    stars = detail_data.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "role": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # Extract poster
    poster = extract_image(anime_item)
    
    # Extract trailer
    subject = detail_data.get('subject', {})
    trailer = None
    trailer_data = subject.get('trailer', {})
    video_addr = trailer_data.get('videoAddress', {})
    if video_addr:
        trailer = video_addr.get('url')
    
    response = {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "anime": {
                "megan_id": generate_megan_id(str(anime_item.subjectId)),
                "title": anime_item.title,
                "year": anime_item.releaseDate.year if anime_item.releaseDate else None,
                "rating": anime_item.imdbRatingValue,
                "genres": anime_item.genre if isinstance(anime_item.genre, list) else [anime_item.genre] if anime_item.genre else [],
                "poster": poster,
                "description": subject.get('description', ''),
                "trailer": trailer,
                "seasons": seasons,
                "total_seasons": len(seasons),
                "cast": cast,
                "detail_path": anime_item.detailPath
            }
        }
    }
    
    return response

@router.get("/{detail_path}/episode")
async def get_anime_episode(
    detail_path: str,
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1)
):
    """Get download URL for a specific anime episode"""
    
    # Search for the anime
    search_tv = Search(session, query=detail_path, subject_type=SubjectType.TV_SERIES)
    results = await search_tv.get_content_model()
    
    anime_item = None
    for item in results.items:
        if item.detailPath == detail_path and is_anime(item):
            anime_item = item
            break
    
    if not anime_item:
        raise HTTPException(status_code=404, detail="Anime not found")
    
    try:
        downloads_obj = DownloadableTVSeriesFilesDetail(session, anime_item)
        download_data = await downloads_obj.get_content(season=season, episode=episode)
        
        if download_data and 'downloads' in download_data:
            return {
                "success": True,
                "megan_id": generate_megan_id(str(anime_item.subjectId)),
                "title": anime_item.title,
                "season": season,
                "episode": episode,
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
    
    return {"success": False, "error": "Episode not available"}
