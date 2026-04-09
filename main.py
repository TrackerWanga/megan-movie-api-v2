import enum
import sys
import os
import httpx
import re
import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse, StreamingResponse
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

# Domain configuration
DOMAIN = "movieapi.megan.qzz.io"
BASE_URL = f"https://{DOMAIN}"

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

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ============================================
# PROXY ENDPOINTS (Hide real CDN URLs)
# ============================================

@app.get("/api/stream")
async def proxy_stream(url: str, range: str = None):
    """Proxy stream a video URL - hides real CDN URL (like PRINCE API)"""
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Referer": f"{BASE_URL}/",
            }
            if range:
                headers["Range"] = range
            
            response = await client.get(url, headers=headers)
            
            # Return streaming response
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=response.status_code,
                headers={
                    "Content-Type": response.headers.get("content-type", "video/mp4"),
                    "Content-Length": response.headers.get("content-length", ""),
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except Exception as e:
        return {"error": str(e), "success": False}

@app.get("/api/dl")
async def proxy_download(url: str, title: str = "video", quality: str = "1080p"):
    """Proxy download a video URL - hides real CDN URL"""
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Referer": f"{BASE_URL}/",
            }
            
            response = await client.get(url, headers=headers)
            
            # Get file extension
            ext = "mp4"
            if ".mp4" in url.lower():
                ext = "mp4"
            elif ".mkv" in url.lower():
                ext = "mkv"
            
            filename = f"{title.replace(' ', '_')}_{quality}.{ext}"
            
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=response.status_code,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except Exception as e:
        return {"error": str(e), "success": False}

# ============================================
# SOURCES ENDPOINT (Like PRINCE API)
# ============================================

@app.get("/api/sources/{subject_id}")
async def get_sources(subject_id: str, season: int = None, episode: int = None):
    """Get streaming sources - embed providers + direct MP4s"""
    from moviebox_api.v2 import Search, Session
    from moviebox_api.v2.download import DownloadableSingleFilesDetail
    
    temp_session = Session()
    
    # Search for the content
    search = Search(temp_session, query=subject_id, subject_type=1)
    results = await search.get_content_model()
    
    imdb_id = None
    title = subject_id
    direct_downloads = []
    
    if results.items:
        title = results.items[0].title
        
        # Try to get IMDb ID
        if hasattr(results.items[0], 'ops') and results.items[0].ops:
            try:
                ops_data = json.loads(results.items[0].ops) if isinstance(results.items[0].ops, str) else results.items[0].ops
                imdb_id = ops_data.get('imdb_id')
            except:
                pass
        
        # Get direct download URLs
        try:
            downloads_obj = DownloadableSingleFilesDetail(temp_session, results.items[0])
            download_data = await downloads_obj.get_content()
            if download_data and 'downloads' in download_data:
                for dl in download_data['downloads']:
                    size_val = dl.get('size', '0')
                    try:
                        size_mb = round(int(size_val) / 1024 / 1024, 2)
                    except:
                        size_mb = 0
                    direct_downloads.append({
                        "provider": "MovieBox",
                        "quality": f"{dl.get('resolution')}p",
                        "type": "direct",
                        "embed_url": f"{BASE_URL}/api/stream?url={dl.get('url')}",
                        "download_url": f"{BASE_URL}/api/dl?url={dl.get('url')}&title={title}&quality={dl.get('resolution')}p",
                        "size": size_val,
                        "size_mb": size_mb,
                        "format": "mp4"
                    })
        except:
            pass
    
    # Embed providers
    embed_providers = []
    
    if imdb_id:
        embed_providers = [
            {"name": "VidLink", "url": f"https://vidlink.pro/movie/{imdb_id}"},
            {"name": "AutoEmbed", "url": f"https://autoembed.co/movie/imdb/{imdb_id}"},
            {"name": "EmbedSU", "url": f"https://embed.su/embed/movie/{imdb_id}"},
            {"name": "VidSrc", "url": f"https://vidsrc.ru/movie/{imdb_id}"},
            {"name": "VidSrcPro", "url": f"https://vidsrc.pro/embed/movie/{imdb_id}"},
        ]
    else:
        embed_providers = [
            {"name": "VidLink", "url": f"https://vidlink.pro/movie/tt{subject_id[-7:]}" if len(subject_id) >= 7 else None},
            {"name": "2Embed", "url": f"https://www.2embed.to/embed/tmdb/movie/{subject_id}"},
        ]
    
    for provider in embed_providers:
        if provider["url"]:
            direct_downloads.append({
                "provider": provider["name"],
                "quality": "Auto",
                "type": "embed",
                "embed_url": provider["url"],
                "download_url": provider["url"]
            })
    
    return {
        "status": 200,
        "success": True,
        "creator": "Megan / Wanga",
        "domain": DOMAIN,
        "imdb_id": imdb_id,
        "title": title,
        "subject_id": subject_id,
        "results": direct_downloads,
        "subtitles": []
    }

# ============================================
# HTML PAGES
# ============================================

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Beautiful landing page"""
    landing_path = os.path.join(os.path.dirname(__file__), "static", "landing.html")
    if os.path.exists(landing_path):
        with open(landing_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = content.replace("https://megan-movie-api-v2.onrender.com", BASE_URL)
            return HTMLResponse(content=content)
    return HTMLResponse(content="<h1>Megan Movie API</h1><p>Welcome</p>")

@app.get("/docs")
async def docs_redirect():
    """Redirect to API documentation"""
    return RedirectResponse(url="/static/index.html")

@app.get("/about")
async def about_page():
    """About page - creator info"""
    about_path = os.path.join(os.path.dirname(__file__), "static", "about.html")
    if os.path.exists(about_path):
        return FileResponse(about_path)
    return RedirectResponse(url="/")

# ============================================
# API INFO
# ============================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Megan Movie API",
        "version": "2.0.0",
        "domain": DOMAIN
    }

@app.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "name": "Megan Movie API",
        "version": "2.0.0",
        "creator": "Tracker Wanga",
        "domain": DOMAIN,
        "description": "Complete movie, TV series, anime, music, and educational content API",
        "total_endpoints": 63,
        "features": [
            "Direct MP4 downloads (360p-1080p)",
            "Proxied streams (hides CDN URLs)",
            "Embed providers (VidLink, AutoEmbed, EmbedSU, VidSrc)",
            "Movie metadata with cast and trailers",
            "TV series with episodes",
            "Anime, Music, Education content",
            "Homepage banners and categories",
            "Sports and Kids content"
        ],
        "documentation": f"{BASE_URL}/static/index.html",
        "about": f"{BASE_URL}/about",
        "health": f"{BASE_URL}/api/health",
        "sources_example": f"{BASE_URL}/api/sources/6391474290696802080"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
