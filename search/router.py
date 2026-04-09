from fastapi import APIRouter, Query
from typing import Optional
import httpx
import re
from datetime import datetime

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/search", tags=["search"])

# Type mapping
TYPE_MAP = {
    1: "movie",
    2: "tv_series",
    3: "anime",
    4: "education",
    6: "music",
    7: "anime"
}

TYPE_FILTERS = {
    "all": None,
    "movie": 1,
    "tv": 2,
    "anime": 3,
    "education": 4,
    "music": 6
}

# OMDb configuration
OMDB_API_KEY = "9b5d7e52"
OMDB_URL = "http://www.omdbapi.com/"
omdb_cache = {}

async def get_imdb_id_from_omdb(title: str, year: int = None) -> Optional[str]:
    cache_key = f"{title}_{year}" if year else title
    if cache_key in omdb_cache:
        return omdb_cache[cache_key]
    
    try:
        params = {"apikey": OMDB_API_KEY, "t": title}
        if year:
            params["y"] = year
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(OMDB_URL, params=params)
            data = response.json()
            if data.get("Response") == "True":
                imdb_id = data.get("imdbID")
                omdb_cache[cache_key] = imdb_id
                return imdb_id
    except Exception as e:
        print(f"OMDb error for {title}: {e}")
    
    omdb_cache[cache_key] = None
    return None

def extract_imdb_from_item(item) -> Optional[str]:
    if hasattr(item, 'ops') and item.ops:
        try:
            import json
            ops_data = json.loads(item.ops) if isinstance(item.ops, str) else item.ops
            if 'imdb_id' in ops_data:
                return ops_data['imdb_id']
        except:
            pass
    
    if hasattr(item, 'imdbId') and item.imdbId:
        return item.imdbId
    
    if hasattr(item, 'detailPath') and item.detailPath:
        match = re.search(r'tt\d{7}', item.detailPath)
        if match:
            return match.group(0)
    
    return None

def generate_megan_id(imdb_id: str = None, subject_id: str = None) -> str:
    if imdb_id:
        return f"megan-{imdb_id}"
    elif subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"

@router.get("")
async def search_all(
    q: str = Query(..., min_length=1),
    type: str = Query("all"),
    limit: int = Query(20, ge=1, le=50),
    include_imdb: bool = Query(True)
):
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
        item_type = TYPE_MAP.get(item.subjectType, "unknown")
        year = item.releaseDate.year if item.releaseDate else None
        
        imdb_id = extract_imdb_from_item(item)
        if not imdb_id and include_imdb and year:
            imdb_id = await get_imdb_id_from_omdb(item.title, year)
        
        megan_id = generate_megan_id(imdb_id, str(item.subjectId) if item.subjectId else None)
        
        items.append({
            "title": item.title,
            "year": year,
            "type": item_type,
            "rating": item.imdbRatingValue,
            "poster": item.cover.url if item.cover else None,
            "subjectId": str(item.subjectId) if item.subjectId else None,
            "detailPath": item.detailPath,
            "megan_id": megan_id,
            "imdb_id": imdb_id
        })
    
    return {
        "success": True,
        "query": q,
        "total": len(items),
        "results": items
    }

@router.get("/quick")
async def search_quick(q: str = Query(..., min_length=1), type: str = Query("all"), limit: int = Query(20, ge=1, le=50)):
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
        item_type = TYPE_MAP.get(item.subjectType, "unknown")
        items.append({
            "title": item.title,
            "year": year,
            "type": item_type,
            "rating": item.imdbRatingValue,
            "poster": item.cover.url if item.cover else None,
            "detailPath": item.detailPath,
            "subjectId": str(item.subjectId) if item.subjectId else None
        })
    
    return {"success": True, "query": q, "total": len(items), "results": items}

@router.get("/types")
async def get_available_types():
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
