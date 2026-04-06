import enum
import sys
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Fix for Python 3.10 StrEnum
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
from moviebox_api.v2.download import DownloadableSingleFilesDetail

app = FastAPI(title="Megan Movie API V2", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create session once
session = Session()

@app.get("/")
async def root():
    return {
        "name": "Megan Movie API V2",
        "status": "running",
        "message": "No proxy required - works globally"
    }

@app.get("/api/search")
async def search(q: str = Query(..., min_length=1)):
    try:
        search_obj = Search(session, query=q)
        results = await search_obj.get_content_model()
        
        movies = []
        for item in results.items[:20]:
            # Handle genre - it's already a list, not a string
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

@app.get("/api/movie/{detailPath}")
async def get_movie(detailPath: str):
    try:
        from moviebox_api.v2 import MovieDetails
        details_obj = MovieDetails(session)
        data = await details_obj.get_content(detailPath)
        
        subject = data.get('subject', {})
        stars = data.get('stars', [])
        trailer = subject.get('trailer', {}).get('videoAddress', {}).get('url')
        
        # Handle genre - it might be string or list
        genre = subject.get('genre', [])
        if isinstance(genre, str):
            genre = genre.split(',')
        
        return {
            "success": True,
            "title": subject.get('title'),
            "year": subject.get('releaseDate', '')[:4] if subject.get('releaseDate') else None,
            "rating": subject.get('imdbRatingValue'),
            "description": subject.get('description'),
            "trailer": trailer,
            "poster": subject.get('cover', {}).get('url'),
            "genres": genre,
            "cast": [{"name": s.get('name'), "character": s.get('character')} for s in stars[:10]]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/download/{detailPath}")
async def get_download(detailPath: str):
    try:
        search_obj = Search(session, query=detailPath)
        results = await search_obj.get_content_model()
        
        if not results.items:
            return {"success": False, "error": "Not found"}
        
        downloads_obj = DownloadableSingleFilesDetail(session, results.items[0])
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
