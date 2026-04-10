import enum
import sys
import os
import httpx
import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse, StreamingResponse
from datetime import datetime
from urllib.parse import quote, unquote

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

# Configuration
PRINCE_API = "https://movieapi.princetechn.com"
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
# HIDDEN PRINCE API PROXY
# ============================================

async def fetch_from_prince(endpoint: str, params: dict = None):
    """Fetch data from PRINCE API (hidden from users)"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{PRINCE_API}{endpoint}"
        response = await client.get(url, params=params)
        return response.json()

@app.get("/api/prince/search/{query}")
async def prince_search(query: str, type: int = 1, page: int = 1):
    """Search using PRINCE API (hidden)"""
    result = await fetch_from_prince(f"/api/search/{query}", {"type": type, "page": page})
    return result

@app.get("/api/prince/sources/{subject_id}")
async def prince_sources(subject_id: str, season: int = None, episode: int = None):
    """Get sources from PRINCE API"""
    params = {}
    if season:
        params["season"] = season
    if episode:
        params["episode"] = episode
    result = await fetch_from_prince(f"/api/sources/{subject_id}", params)
    return result

@app.get("/api/prince/download/{subject_id}")
async def prince_download(subject_id: str, season: int = None, episode: int = None):
    """Get download links from PRINCE API"""
    params = {}
    if season:
        params["season"] = season
    if episode:
        params["episode"] = episode
    result = await fetch_from_prince(f"/api/download/{subject_id}", params)
    return result

# ============================================
# UNIFIED SOURCES (Hides PRINCE)
# ============================================

@app.get("/api/sources/{subject_id}")
async def get_unified_sources(subject_id: str, season: int = None, episode: int = None):
    """Get sources - uses PRINCE API internally but hides it"""
    params = {}
    if season:
        params["season"] = season
    if episode:
        params["episode"] = episode

    prince_result = await fetch_from_prince(f"/api/sources/{subject_id}", params)

    transformed = {
        "success": True,
        "status": 200,
        "creator": "Megan / Wanga",
        "domain": DOMAIN,
        "title": prince_result.get("title", "Unknown"),
        "subject_id": subject_id,
        "sources": []
    }

    for source in prince_result.get("results", []):
        provider = source.get("provider", "Unknown")
        embed_url = source.get("embed_url", "")
        download_url = source.get("download_url", "")

        if "bcdnxw" in embed_url or "hakunaymatata" in embed_url:
            proxied_embed = f"{BASE_URL}/api/stream?url={quote(embed_url, safe='')}"
            proxied_download = f"{BASE_URL}/api/dl?url={quote(download_url, safe='')}&title={prince_result.get('title', 'video')}"
        else:
            proxied_embed = embed_url
            proxied_download = download_url

        transformed["sources"].append({
            "provider": provider,
            "quality": source.get("quality", "Auto"),
            "type": source.get("type", "embed"),
            "embed_url": proxied_embed,
            "download_url": proxied_download
        })

    transformed["subtitles"] = prince_result.get("subtitles", [])
    return transformed

# ============================================
# ENHANCED PROXY STREAM (Hides CDN)
# ============================================

@app.get("/api/stream")
async def proxy_stream(url: str):
    """Proxy stream a video URL - with working CDN headers"""
    decoded_url = unquote(url)
    
    try:
        cookie = None
        try:
            from movies.router import session as movie_session
            if hasattr(movie_session, '_client'):
                client = movie_session._client
                if hasattr(client, 'cookies'):
                    for c in client.cookies.jar:
                        if c.name == 'token':
                            cookie = c.value
                            break
        except:
            pass
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            headers = {
                "Origin": "https://videodownloader.site/",
                "Referer": "https://videodownloader.site/",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
                "Accept": "*/*",
            }
            
            if cookie:
                headers["Cookie"] = f"token={cookie}"
            
            response = await client.get(decoded_url, headers=headers)
            
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=response.status_code,
                headers={
                    "Content-Type": "video/mp4",
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except Exception as e:
        return {"error": str(e), "success": False}
# ============================================
# ENHANCED PROXY DOWNLOAD (Hides CDN)
# ============================================

@app.get("/api/dl")
async def proxy_download(url: str, title: str = "video", quality: str = "1080p"):
    """Proxy download a video URL - with working CDN headers"""
    decoded_url = unquote(url)
    print(f"⬇️ Downloading: {title} ({quality})")
    
    try:
        cookie = None
        try:
            from movies.router import session as movie_session
            if hasattr(movie_session, '_client'):
                client = movie_session._client
                if hasattr(client, 'cookies'):
                    for c in client.cookies.jar:
                        if c.name == 'token':
                            cookie = c.value
                            break
        except:
            pass
        
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            headers = {
                "Origin": "https://videodownloader.site/",
                "Referer": "https://videodownloader.site/",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
            
            if cookie:
                headers["Cookie"] = f"token={cookie}"
            
            response = await client.get(decoded_url, headers=headers)
            
            if response.status_code != 200:
                return {"error": f"CDN returned {response.status_code}", "success": False}
            
            filename = f"{title.replace(' ', '_')}_{quality}.mp4"
            
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=200,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*",
                    "Content-Length": response.headers.get("content-length", ""),
                }
            )
    except Exception as e:
        return {"error": str(e), "success": False}
# ============================================
# LEGACY PROXY ENDPOINTS (for compatibility)
# ============================================

@app.get("/api/proxy/dl")
async def proxy_download_legacy(url: str, title: str = "video", quality: str = "1080p"):
    """Legacy proxy download endpoint"""
    return await proxy_download(url, title, quality)

@app.get("/api/proxy/stream")
async def proxy_stream_legacy(url: str):
    """Legacy proxy stream endpoint"""
    return await proxy_stream(url)

# ============================================
# HTML PAGES
# ============================================

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    landing_path = os.path.join(os.path.dirname(__file__), "static", "landing.html")
    if os.path.exists(landing_path):
        with open(landing_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = content.replace("https://megan-movie-api-v2.onrender.com", BASE_URL)
            return HTMLResponse(content=content)
    return HTMLResponse(content="<h1>Megan Movie API</h1><p>Welcome</p>")

@app.get("/docs")
async def docs_redirect():
    return RedirectResponse(url="/static/index.html")

@app.get("/about")
async def about_page():
    about_path = os.path.join(os.path.dirname(__file__), "static", "about.html")
    if os.path.exists(about_path):
        return FileResponse(about_path)
    return RedirectResponse(url="/")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Megan Movie API",
        "version": "2.0.0",
        "domain": DOMAIN
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
