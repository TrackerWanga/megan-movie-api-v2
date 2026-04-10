from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/search", tags=["search"])

# Type mapping for response
TYPE_MAP = {
    1: "movie",
    2: "tv_series",
    3: "anime",
    4: "education",
    6: "music",
    7: "anime"
}

# Type filter mapping
TYPE_FILTERS = {
    "all": None,
    "movie": SubjectType.MOVIES,
    "tv": SubjectType.TV_SERIES,
    "anime": SubjectType.ANIME,
    "education": SubjectType.EDUCATION,
    "music": SubjectType.MUSIC
}

def generate_megan_id(subject_id: str) -> str:
    """Generate Megan ID from subjectId"""
    return f"megan-{subject_id}"

@router.get("")
async def search_all(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str = Query("all", description="Filter by type: all, movie, tv, anime, music, education"),
    limit: int = Query(20, ge=1, le=50, description="Results limit")
):
    """
    Search across all content types with complete metadata
    Returns: title, year, rating, genres, poster, subjectId, megan_id, and more
    """
    session = Session()
    subject_type = TYPE_FILTERS.get(type)
    
    try:
        if subject_type:
            search = Search(session, query=q, subject_type=subject_type)
        else:
            search = Search(session, query=q, subject_type=SubjectType.MOVIES)
        
        results = await search.get_content_model()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": q
        }
    
    items = []
    for item in results.items[:limit]:
        # Get year
        year = item.releaseDate.year if item.releaseDate else None
        
        # Get content type
        content_type = TYPE_MAP.get(item.subjectType, "unknown")
        
        # Get poster URL
        poster_url = str(item.cover.url) if item.cover else None
        
        # Calculate duration in minutes
        duration_min = item.duration // 60 if item.duration else None
        
        # Build result item
        items.append({
            "megan_id": generate_megan_id(str(item.subjectId)),
            "title": item.title,
            "year": year,
            "type": content_type,
            "type_id": item.subjectType if hasattr(item.subjectType, 'value') else item.subjectType,
            "rating": item.imdbRatingValue,
            "genres": item.genre if isinstance(item.genre, list) else [item.genre] if item.genre else [],
            "poster": poster_url,
            "detail_path": item.detailPath,
            "subject_id": str(item.subjectId),
            "has_download": item.hasResource,
            "duration_minutes": duration_min,
            "country": item.countryName if hasattr(item, 'countryName') else None
        })
    
    return {
        "success": True,
        "query": q,
        "type_filter": type,
        "total": len(items),
        "timestamp": datetime.now().isoformat(),
        "results": items
    }

@router.get("/quick")
async def search_quick(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str = Query("all", description="Filter by type"),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Quick search - minimal metadata (faster)
    """
    session = Session()
    subject_type = TYPE_FILTERS.get(type)
    
    try:
        if subject_type:
            search = Search(session, query=q, subject_type=subject_type)
        else:
            search = Search(session, query=q, subject_type=SubjectType.MOVIES)
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e), "query": q}
    
    items = []
    for item in results.items[:limit]:
        year = item.releaseDate.year if item.releaseDate else None
        content_type = TYPE_MAP.get(item.subjectType, "unknown")
        poster_url = str(item.cover.url) if item.cover else None
        
        items.append({
            "title": item.title,
            "year": year,
            "type": content_type,
            "rating": item.imdbRatingValue,
            "poster": poster_url,
            "detail_path": item.detailPath,
            "subject_id": str(item.subjectId)
        })
    
    return {
        "success": True,
        "query": q,
        "type_filter": type,
        "total": len(items),
        "results": items
    }

@router.get("/types")
async def get_available_types():
    """Get list of available content types"""
    return {
        "success": True,
        "types": [
            {"name": "all", "id": 0, "description": "All content types"},
            {"name": "movie", "id": 1, "description": "Movies only"},
            {"name": "tv", "id": 2, "description": "TV series only"},
            {"name": "anime", "id": 3, "description": "Anime only"},
            {"name": "education", "id": 4, "description": "Educational content"},
            {"name": "music", "id": 6, "description": "Music videos"}
        ]
    }
