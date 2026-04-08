import enum
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from datetime import datetime

if not hasattr(enum, 'StrEnum'):
    try:
        from strenum import StrEnum
        enum.StrEnum = StrEnum
    except ImportError:
        from enum import Enum
        class StrEnum(str, Enum):
            pass
        enum.StrEnum = StrEnum

# Import all routers
from search.router import router as search_router
from movies.router import router as movies_router
from tv.router import router as tv_router
from banners.router import router as banners_router
from music.router import router as music_router
from anime.router import router as anime_router
from education.router import router as education_router

app = FastAPI(title="Megan Movie API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(search_router)
app.include_router(movies_router)
app.include_router(tv_router)
app.include_router(banners_router)
app.include_router(music_router)
app.include_router(anime_router)
app.include_router(education_router)

# Serve static files (HTML documentation)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/docs", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/")
async def root():
    return {
        "api": "Megan Movie API",
        "version": "2.0.0",
        "creator": "Megan / Wanga",
        "description": "Complete movie, TV series, anime, music, and educational content API",
        "documentation": "/docs/index.html",
        "about": "/about",
        "health": "/api/health",
        "total_endpoints": 63,
        "endpoints": {
            "search": "/api/search?q=movie_name&type=all",
            "search_quick": "/api/search/quick?q=movie_name",
            "search_types": "/api/search/types",
            "movie": "/api/movies/{title}?year=2010",
            "movie_downloads": "/api/movies/{title}/downloads",
            "tv_search": "/api/tv/search?q=breaking",
            "tv_series": "/api/tv/{title}",
            "tv_episode": "/api/tv/{title}/episode?season=1&episode=1",
            "tv_seasons": "/api/tv/{title}/seasons",
            "music_search": "/api/music/search?q=pharrell",
            "music_artist": "/api/music/artist/{name}",
            "music_trending": "/api/music/trending",
            "music_popular": "/api/music/popular",
            "music_latest": "/api/music/latest",
            "anime_search": "/api/anime/search?q=naruto",
            "anime_popular": "/api/anime/popular",
            "anime_trending": "/api/anime/trending",
            "anime_latest": "/api/anime/latest",
            "education_search": "/api/education/search?q=python",
            "education_documentaries": "/api/education/documentaries",
            "education_tutorials": "/api/education/tutorials",
            "main_banners": "/api/homepage/banners",
            "trending": "/api/homepage/trending",
            "action": "/api/homepage/action",
            "horror": "/api/homepage/horror",
            "romance": "/api/homepage/romance",
            "adventure": "/api/homepage/adventure",
            "kdrama": "/api/homepage/kdrama",
            "cdrama": "/api/homepage/cdrama",
            "turkish": "/api/homepage/turkish",
            "sadrama": "/api/homepage/sadrama",
            "blackshows": "/api/homepage/blackshows",
            "wwe": "/api/sports/wwe",
            "football": "/api/sports/football",
            "boxing": "/api/sports/boxing",
            "live_sports": "/api/sports/live",
            "nursery_rhymes": "/api/kids/nursery",
            "animation": "/api/kids/animation",
            "platforms": "/api/platforms"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for keep-alive services"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Megan Movie API",
        "version": "2.0.0"
    }

@app.get("/api/docs")
async def api_docs_redirect():
    """Redirect to the beautiful API documentation page"""
    return RedirectResponse(url="/docs/index.html")

@app.get("/about")
async def about_page():
    """About page - creator info and project details"""
    about_path = os.path.join(os.path.dirname(__file__), "static", "about.html")
    if os.path.exists(about_path):
        return FileResponse(about_path)
    return RedirectResponse(url="/docs/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
