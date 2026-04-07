import enum
import sys
import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

if not hasattr(enum, 'StrEnum'):
    try:
        from strenum import StrEnum
        enum.StrEnum = StrEnum
    except ImportError:
        from enum import Enum
        class StrEnum(str, Enum):
            pass
        enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.download import DownloadableSingleFilesDetail, DownloadableTVSeriesFilesDetail

app = FastAPI(title="Megan Unified API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CONFIG = {
    "api_name": "Megan Unified API",
    "api_version": "2.0.0",
    "creator": "Megan",
    "api_id_prefix": "megan-unified",
    "vidsrc_api_url": "https://megan-vidsrc.vercel.app"
}

# OMDb API (direct fallback)
OMDB_API_KEY = "9b5d7e52"
OMDB_URL = "http://www.omdbapi.com/"

session = Session()

def generate_megan_id(imdb_id: str = None, moviebox_id: str = None) -> str:
    """Generate a unified Megan ID"""
    if imdb_id:
        return f"{CONFIG['api_id_prefix']}-{imdb_id}"
    elif moviebox_id:
        return f"{CONFIG['api_id_prefix']}-{moviebox_id}"
    return f"{CONFIG['api_id_prefix']}-unknown"

async def get_omdb_data(title: str, year: int = None):
    """Get OMDb metadata directly"""
    params = {"apikey": OMDB_API_KEY, "t": title, "plot": "full"}
    if year:
        params["y"] = year
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OMDB_URL, params=params)
            data = response.json()
            if data.get("Response") == "True":
                return data
        except Exception as e:
            print(f"OMDb error: {e}")
    return None

async def get_vidsrc_streams(imdb_id: str):
    """Get proxied stream URLs from Megan Vidsrc API"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(f"{CONFIG['vidsrc_api_url']}/api/streams/{imdb_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("streams", [])
        except Exception as e:
            print(f"Vidsrc API error: {e}")
    return []

@app.get("/")
async def root():
    return {
        "api": CONFIG["api_name"],
        "version": CONFIG["api_version"],
        "creator": CONFIG["creator"],
        "description": "Unified API combining moviebox_api MP4 downloads + OMDb metadata + vidsrc streams",
        "endpoints": {
            "search": "/api/search?q=avengers",
            "movie": "/api/movie/{detailPath}",
            "unified_search": "/api/unified/search?q=avengers",
            "unified_movie": "/api/unified/movie/{title}"
        }
    }

# ============================================
# UNIFIED SEARCH - Combines moviebox_api search
# ============================================
@app.get("/api/unified/search")
async def unified_search(q: str = Query(..., min_length=1)):
    """Search movies - returns moviebox_api results with megan branding"""
    try:
        search_obj = Search(session, query=q)
        results = await search_obj.get_content_model()
        
        movies = []
        for item in results.items[:20]:
            # Generate megan_id
            megan_id = generate_megan_id(moviebox_id=str(item.subjectId))
            
            movies.append({
                "megan_id": megan_id,
                "title": item.title,
                "year": item.releaseDate.year if item.releaseDate else None,
                "rating": item.imdbRatingValue,
                "genres": item.genre if isinstance(item.genre, list) else (item.genre.split(',') if item.genre else []),
                "poster": item.cover.url if item.cover else None,
                "detailPath": item.detailPath,
                "subjectId": item.subjectId,
                "source": "moviebox_api"
            })
        
        return {
            "success": True,
            "api": CONFIG["api_name"],
            "creator": CONFIG["creator"],
            "query": q,
            "total": len(movies),
            "results": movies
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# UNIFIED MOVIE - Combines ALL sources
# ============================================
@app.get("/api/unified/movie/{title}")
async def unified_movie(title: str, year: Optional[int] = None):
    """Get COMPLETE movie data from ALL sources:
    - moviebox_api (MP4 downloads)
    - OMDb (IMDb metadata)
    - Megan Vidsrc API (proxied streams)
    """
    try:
        # 1. Get OMDb data first (for IMDb ID and rich metadata)
        omdb_data = await get_omdb_data(title, year)
        
        # 2. Get moviebox_api data
        search_obj = Search(session, query=title)
        results = await search_obj.get_content_model()
        
        moviebox_item = None
        if results.items:
            # Try to find exact match by year
            for item in results.items:
                if year and item.releaseDate and item.releaseDate.year == year:
                    moviebox_item = item
                    break
            if not moviebox_item:
                moviebox_item = results.items[0]
        
        # 3. Get vidsrc streams (if we have IMDb ID)
        streams = []
        imdb_id = None
        if omdb_data:
            imdb_id = omdb_data.get("imdbID")
            streams = await get_vidsrc_streams(imdb_id)
        
        # 4. Get moviebox download URLs
        downloads = []
        if moviebox_item:
            try:
                downloads_obj = DownloadableSingleFilesDetail(session, moviebox_item)
                download_data = await downloads_obj.get_content()
                if download_data and 'downloads' in download_data:
                    for dl in download_data['downloads']:
                        size_val = dl.get('size', '0')
                        try:
                            size_mb = round(int(size_val) / 1024 / 1024, 2)
                        except (ValueError, TypeError):
                            size_mb = 0
                        downloads.append({
                            "quality": f"{dl.get('resolution')}p",
                            "size_mb": size_mb,
                            "url": dl.get('url')
                        })
            except Exception as e:
                print(f"Downloads error: {e}")
        
        # 5. Generate unified megan_id
        megan_id = generate_megan_id(imdb_id=imdb_id, moviebox_id=moviebox_item.subjectId if moviebox_item else None)
        
        # 6. Build unified response
        response = {
            "success": True,
            "api": CONFIG["api_name"],
            "creator": CONFIG["creator"],
            "megan_id": megan_id,
            "timestamp": None,  # Will add datetime
            "movie": {
                "title": omdb_data.get("Title") if omdb_data else (moviebox_item.title if moviebox_item else title),
                "year": omdb_data.get("Year") if omdb_data else (moviebox_item.releaseDate.year if moviebox_item and moviebox_item.releaseDate else None),
                "rated": omdb_data.get("Rated") if omdb_data else None,
                "runtime": omdb_data.get("Runtime") if omdb_data else None,
                "genres": omdb_data.get("Genre", "").split(", ") if omdb_data else (moviebox_item.genre if moviebox_item else []),
                "director": omdb_data.get("Director") if omdb_data else None,
                "actors": omdb_data.get("Actors") if omdb_data else None,
                "plot": omdb_data.get("Plot") if omdb_data else (moviebox_item.description if moviebox_item else None),
                "poster": omdb_data.get("Poster") if omdb_data else (moviebox_item.cover.url if moviebox_item and moviebox_item.cover else None),
                "imdb_rating": omdb_data.get("imdbRating") if omdb_data else (moviebox_item.imdbRatingValue if moviebox_item else None),
                "imdb_votes": omdb_data.get("imdbVotes") if omdb_data else None,
                "imdb_id": imdb_id,
                "moviebox_id": moviebox_item.subjectId if moviebox_item else None,
                "detailPath": moviebox_item.detailPath if moviebox_item else None
            },
            "sources": {
                "downloads": {
                    "available": len(downloads) > 0,
                    "items": downloads,
                    "source": "moviebox_api",
                    "note": "Direct MP4 download URLs - right click to save"
                },
                "streams": {
                    "available": len(streams) > 0,
                    "items": streams,
                    "source": "Megan Vidsrc API",
                    "note": "Proxied embed URLs - vidsrc domains are hidden"
                }
            }
        }
        
        # Add timestamp
        from datetime import datetime
        response["timestamp"] = datetime.now().isoformat()
        
        return response
        
    except Exception as e:
        return {"success": False, "error": str(e), "megan_id": generate_megan_id()}

# ============================================
# LEGACY ENDPOINTS (for backward compatibility)
# ============================================

@app.get("/api/search")
async def legacy_search(q: str = Query(..., min_length=1)):
    """Legacy moviebox_api search"""
    try:
        search_obj = Search(session, query=q)
        results = await search_obj.get_content_model()
        
        movies = []
        for item in results.items[:20]:
            genres = item.genre if isinstance(item.genre, list) else (item.genre.split(',') if item.genre else [])
            movies.append({
                "title": item.title,
                "year": item.releaseDate.year if item.releaseDate else None,
                "rating": item.imdbRatingValue,
                "genres": genres,
                "poster": item.cover.url if item.cover else None,
                "detailPath": item.detailPath
            })
        
        return {"success": True, "query": q, "total": len(movies), "movies": movies}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/download/{detailPath}")
async def legacy_download(detailPath: str):
    """Legacy moviebox_api download"""
    try:
        search_obj = Search(session, query=detailPath)
        results = await search_obj.get_content_model()
        
        if not results.items:
            return {"success": False, "error": "Not found"}
        
        first_item = results.items[0]
        downloads_obj = DownloadableSingleFilesDetail(session, first_item)
        data = await downloads_obj.get_content()
        
        return {
            "success": True,
            "downloads": [
                {"quality": f"{d.get('resolution')}p", "size_mb": round(int(d.get('size', 0)) / 1024 / 1024, 2), "url": d.get('url')}
                for d in data.get('downloads', [])
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
