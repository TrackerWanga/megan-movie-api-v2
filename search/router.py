from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/search", tags=["search"])

# Configuration
WORKER_URL = "https://streamapi.megan.qzz.io"

# Type mapping
TYPE_MAP = {
    1: "movie",
    2: "tv_series", 
    7: "anime",
    5: "education",
    6: "music"
}

TYPE_FILTERS = {
    "all": None,
    "movie": SubjectType.MOVIES,
    "tv": SubjectType.TV_SERIES,
    "anime": SubjectType.ANIME,
    "education": SubjectType.EDUCATION,
    "music": SubjectType.MUSIC
}

def generate_megan_id(subject_id: str) -> str:
    return f"megan-{subject_id}"

def format_python_result(item) -> Dict:
    year = item.releaseDate.year if item.releaseDate else None
    content_type = TYPE_MAP.get(item.subjectType, "unknown")
    poster_url = str(item.cover.url) if item.cover else None

    return {
        "megan_id": generate_megan_id(str(item.subjectId)),
        "title": item.title,
        "year": year,
        "type": content_type,
        "rating": item.imdbRatingValue,
        "genres": item.genre if isinstance(item.genre, list) else [item.genre] if item.genre else [],
        "poster": poster_url,
        "detail_path": item.detailPath,
        "subject_id": str(item.subjectId),
        "has_download": item.hasResource,
        "country": item.countryName if hasattr(item, 'countryName') else None,
        "source": "python"
    }

# ============================================
# UNIFIED SEARCH
# ============================================

@router.get("")
async def search_all(
    q: str = Query(..., min_length=1),
    type: str = Query("all", description="all, movie, tv, anime, music, education"),
    limit: int = Query(30, ge=1, le=50),
    source: str = Query("all", description="python, worker, all")
):
    """Unified search combining Python and Worker"""
    
    results = []
    seen_ids = set()
    
    # Python Search
    if source in ["python", "all"]:
        session = Session()
        subject_type = TYPE_FILTERS.get(type)
        
        try:
            if subject_type:
                search = Search(session, query=q, subject_type=subject_type)
            else:
                search = Search(session, query=q, subject_type=SubjectType.MOVIES)
            
            python_results = await search.get_content_model()
            for item in python_results.items:
                formatted = format_python_result(item)
                sid = formatted['subject_id']
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    results.append(formatted)
        except Exception as e:
            print(f"Python search error: {e}")
    
    # Worker Search
    if source in ["worker", "all"]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{WORKER_URL}/search?q={q}")
                if resp.status_code == 200:
                    data = resp.json()
                    for movie in data.get('movies', []):
                        sid = str(movie.get('subject_id'))
                        if sid and sid not in seen_ids:
                            seen_ids.add(sid)
                            results.append({
                                "megan_id": generate_megan_id(sid),
                                "title": movie.get('name'),
                                "year": movie.get('year', '')[:4] if movie.get('year') else None,
                                "type": "movie",
                                "rating": None,
                                "genres": [],
                                "poster": movie.get('poster_url'),
                                "detail_path": movie.get('slug'),
                                "subject_id": sid,
                                "blurhash": movie.get('blurhash'),
                                "source": "worker"
                            })
        except Exception as e:
            print(f"Worker search error: {e}")
    
    return {
        "success": True,
        "query": q,
        "type_filter": type,
        "source": source,
        "total": len(results[:limit]),
        "timestamp": datetime.now().isoformat(),
        "results": results[:limit]
    }

# ============================================
# QUICK SEARCH
# ============================================

@router.get("/quick")
async def search_quick(
    q: str = Query(..., min_length=1),
    type: str = Query("all"),
    limit: int = Query(20, ge=1, le=50)
):
    """Quick search - minimal metadata"""
    session = Session()
    subject_type = TYPE_FILTERS.get(type)

    try:
        if subject_type:
            search = Search(session, query=q, subject_type=subject_type)
        else:
            search = Search(session, query=q, subject_type=SubjectType.MOVIES)
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}

    items = []
    for item in results.items[:limit]:
        items.append({
            "title": item.title,
            "year": item.releaseDate.year if item.releaseDate else None,
            "type": TYPE_MAP.get(item.subjectType, "unknown"),
            "rating": item.imdbRatingValue,
            "poster": str(item.cover.url) if item.cover else None,
            "detail_path": item.detailPath,
            "subject_id": str(item.subjectId)
        })

    return {"success": True, "query": q, "total": len(items), "results": items}

# ============================================
# SUGGESTIONS (Worker)
# ============================================

@router.get("/suggest")
async def search_suggest(q: str = Query(..., min_length=1)):
    """Autocomplete suggestions from Worker"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WORKER_URL}/search/suggest?q={q}")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "query": q,
                    "suggestions": data.get('suggestions', [])
                }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False, "suggestions": []}

# ============================================
# TYPE-SPECIFIC SEARCHES
# ============================================

@router.get("/movies")
async def search_movies(q: str = Query(..., min_length=1), limit: int = Query(20)):
    session = Session()
    try:
        search = Search(session, query=q, subject_type=SubjectType.MOVIES)
        results = await search.get_content_model()
        items = [format_python_result(item) for item in results.items[:limit]]
        return {"success": True, "query": q, "total": len(items), "results": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/tv")
async def search_tv(q: str = Query(..., min_length=1), limit: int = Query(20)):
    session = Session()
    try:
        search = Search(session, query=q, subject_type=SubjectType.TV_SERIES)
        results = await search.get_content_model()
        items = [format_python_result(item) for item in results.items[:limit]]
        return {"success": True, "query": q, "total": len(items), "results": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/anime")
async def search_anime(q: str = Query(..., min_length=1), limit: int = Query(20)):
    session = Session()
    try:
        search = Search(session, query=q, subject_type=SubjectType.ANIME)
        results = await search.get_content_model()
        items = [format_python_result(item) for item in results.items[:limit]]
        return {"success": True, "query": q, "total": len(items), "results": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# CATALOGS (Worker)
# ============================================

@router.get("/catalog/movies")
async def catalog_movies():
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{WORKER_URL}/movies")
            if resp.status_code == 200:
                return {"success": True, "source": "worker", "data": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/catalog/tv")
async def catalog_tv():
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{WORKER_URL}/tv-series")
            if resp.status_code == 200:
                return {"success": True, "source": "worker", "data": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/catalog/animation")
async def catalog_animation():
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{WORKER_URL}/animation")
            if resp.status_code == 200:
                return {"success": True, "source": "worker", "data": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# TYPES & TRENDING
# ============================================

@router.get("/types")
async def get_types():
    return {
        "success": True,
        "types": [
            {"name": "all", "id": 0},
            {"name": "movie", "id": 1},
            {"name": "tv", "id": 2},
            {"name": "anime", "id": 7},
            {"name": "education", "id": 5},
            {"name": "music", "id": 6}
        ]
    }

@router.get("/trending")
async def get_trending():
    return {
        "success": True,
        "trending": ["Avatar", "Game of Thrones", "Inception", "Breaking Bad", 
                     "Stranger Things", "The Dark Knight", "Interstellar", "Vikings"]
    }
