import enum
import sys
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session, MovieDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail

app = FastAPI(title="Megan Movie API V2", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = Session()

@app.get("/")
async def root():
    return {"name": "Megan Movie API V2", "status": "running", "message": "No proxy required - works globally"}

@app.get("/api/search")
async def search(q: str = Query(..., min_length=1)):
    search = Search(session, query=q)
    results = await search.get_content_model()
    
    movies = []
    for item in results.items[:20]:
        movies.append({
            "title": item.title,
            "year": item.releaseDate.year if item.releaseDate else None,
            "rating": item.imdbRatingValue,
            "genres": item.genre.split(',') if item.genre else [],
            "poster": item.cover.url if item.cover else None,
            "detailPath": item.detailPath
        })
    
    return {"success": True, "query": q, "total": len(movies), "movies": movies}

@app.get("/api/movie/{detailPath}")
async def get_movie(detailPath: str):
    details = MovieDetails(session)
    data = await details.get_content(detailPath)
    
    subject = data.get('subject', {})
    stars = data.get('stars', [])
    trailer = subject.get('trailer', {}).get('videoAddress', {}).get('url')
    
    return {
        "success": True,
        "title": subject.get('title'),
        "year": subject.get('releaseDate', '')[:4],
        "rating": subject.get('imdbRatingValue'),
        "description": subject.get('description'),
        "trailer": trailer,
        "poster": subject.get('cover', {}).get('url'),
        "cast": [{"name": s.get('name'), "character": s.get('character')} for s in stars[:10]]
    }

@app.get("/api/download/{detailPath}")
async def get_download(detailPath: str):
    search = Search(session, query=detailPath)
    results = await search.get_content_model()
    
    if not results.items:
        return {"success": False, "error": "Not found"}
    
    downloads = DownloadableSingleFilesDetail(session, results.items[0])
    data = await downloads.get_content()
    
    return {
        "success": True,
        "downloads": [
            {"quality": f"{d.get('resolution')}p", "size_mb": round(int(d.get('size', 0)) / 1024 / 1024, 2), "url": d.get('url')}
            for d in data.get('downloads', [])
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
