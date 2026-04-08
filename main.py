import enum
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
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

app = FastAPI(title="Megan Movie API", version="2.0.0", docs_url=None, redoc_url=None)

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

# Serve static files (HTML documentation and landing page)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve the beautiful landing page"""
    landing_path = os.path.join(os.path.dirname(__file__), "static", "landing.html")
    if os.path.exists(landing_path):
        with open(landing_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Megan Movie API</h1><p>Welcome to Megan Movie API</p>")

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
    """Redirect to the API documentation page"""
    return RedirectResponse(url="/static/docs.html")

@app.get("/docs")
async def docs_redirect():
    """Redirect to API documentation"""
    return RedirectResponse(url="/static/docs.html")

@app.get("/about")
async def about_page():
    """About page - creator info and project details"""
    about_path = os.path.join(os.path.dirname(__file__), "static", "about.html")
    if os.path.exists(about_path):
        return FileResponse(about_path)
    return RedirectResponse(url="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
