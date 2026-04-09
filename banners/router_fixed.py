from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import datetime

from moviebox_api.v2 import Homepage, Session

router = APIRouter(prefix="/api", tags=["banners"])

session = Session()

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

def format_subject(subject) -> Dict:
    """Format a subject (movie/TV) for response"""
    # Handle genre - it could be list or string
    genres = []
    if hasattr(subject, 'genre') and subject.genre:
        if isinstance(subject.genre, list):
            genres = subject.genre
        elif isinstance(subject.genre, str):
            genres = subject.genre.split(',')
    
    return {
        "id": str(subject.subjectId) if hasattr(subject, 'subjectId') else None,
        "title": subject.title if hasattr(subject, 'title') else None,
        "type": subject.subjectType if hasattr(subject, 'subjectType') else None,
        "year": subject.releaseDate.year if hasattr(subject, 'releaseDate') and subject.releaseDate else None,
        "rating": subject.imdbRatingValue if hasattr(subject, 'imdbRatingValue') else None,
        "genres": genres,
        "poster": extract_image(subject),
        "detail_path": subject.detailPath if hasattr(subject, 'detailPath') else None
    }

def get_homepage_data():
    """Helper to get homepage data once"""
    homepage = Homepage(session)
    return homepage.get_content_model()

@router.get("/homepage/banners")
async def get_main_banners():
    """Main hero banners (Banner_Africa)"""
    home_data = await get_homepage_data()
    
    banners = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "BANNER":
                if hasattr(item, 'banner') and item.banner and hasattr(item.banner, 'items'):
                    for banner_item in item.banner.items:
                        banners.append({
                            "title": banner_item.title if hasattr(banner_item, 'title') else None,
                            "image": extract_image(banner_item) if hasattr(banner_item, 'image') else None,
                            "subject_id": str(banner_item.subjectId) if hasattr(banner_item, 'subjectId') else None,
                            "detail_path": banner_item.detailPath if hasattr(banner_item, 'detailPath') else None
                        })
    
    return {"success": True, "total": len(banners), "banners": banners}

@router.get("/homepage/action")
async def get_action_movies():
    """Action Movies"""
    home_data = await get_homepage_data()
    
    movies = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "Action Movies":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            movies.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(movies), "movies": movies}

# Add all other endpoints similarly (trending, horror, romance, etc.)
# For brevity, I'll add a generic handler for all SUBJECTS_MOVIE types
@router.get("/homepage/{section}")
async def get_homepage_section(section: str):
    """Generic handler for homepage sections"""
    home_data = await get_homepage_data()
    
    # Map section names to actual titles in the API
    section_map = {
        "trending": ["Popular Series", "Popular Movie"],
        "action": "Action Movies",
        "horror": "Horror Movies",
        "romance": "💓Teen Romance 💓",
        "adventure": "Adventure Movies",
        "anime": "Anime[English Dubbed]",
        "kdrama": "K-Drama",
        "cdrama": "C-Drama",
        "turkish": "Turkish Drama",
        "sadrama": "SA Drama",
        "blackshows": "Must-watch Black Shows",
        "premium": "Premium VIP HD Access>>",
        "hot-shorts": "🔥Hot Short TV"
    }
    
    target = section_map.get(section)
    if not target:
        return {"success": False, "error": f"Section '{section}' not found"}
    
    items = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                title = getattr(item, 'title', '')
                if isinstance(target, list):
                    if title in target:
                        if hasattr(item, 'subjects'):
                            items = [format_subject(s) for s in item.subjects]
                        break
                else:
                    if title == target:
                        if hasattr(item, 'subjects'):
                            items = [format_subject(s) for s in item.subjects]
                        break
    
    return {"success": True, "total": len(items), "results": items}

@router.get("/platforms")
async def get_platforms():
    """Get platform banners (Netflix, PrimeVideo, Disney, etc.)"""
    home_data = await get_homepage_data()
    
    platforms = []
    if hasattr(home_data, 'platformList'):
        for item in home_data.platformList:
            platforms.append({
                "name": item.name if hasattr(item, 'name') else None,
                "uploaded_by": item.uploadBy if hasattr(item, 'uploadBy') else None
            })
    
    return {"success": True, "total": len(platforms), "platforms": platforms}
