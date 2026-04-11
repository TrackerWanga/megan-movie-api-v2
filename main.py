import enum
import sys
import os
import httpx
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

# Configuration
DOMAIN = "movieapi.megan.qzz.io"
BASE_URL = f"https://{DOMAIN}"
WORKER_URL = "https://movieapi2.trackerwanga254.workers.dev"

app = FastAPI(title="Megan Movie API", version="3.0.0", docs_url=None, redoc_url=None)

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
# WORKER-POWERED DOWNLOAD (Clean)
# ============================================

@app.get("/api/download/{subject_id}")
async def api_download(
    subject_id: str,
    detail_path: str,
    resolution: str = "720",
    se: int = None,
    ep: int = None
):
    """
    Proxied download through Megan Stream Engine
    - Hides Worker URL completely
    - Forces download with proper filename
    - Supports TV episodes with se/ep parameters
    """
    params = {"detail_path": detail_path, "resolution": resolution}
    if se is not None and ep is not None:
        params["se"] = se
        params["ep"] = ep
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(
                f"{WORKER_URL}/download/{subject_id}",
                params=params,
                headers={"Range": request.headers.get("Range") if hasattr(request, 'headers') else None}
            )
            
            if response.status_code != 200:
                return {"error": f"Stream engine returned {response.status_code}", "success": False}
            
            headers = {
                "Content-Type": response.headers.get("Content-Type", "video/mp4"),
                "Content-Disposition": response.headers.get("Content-Disposition", ""),
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
            }
            if response.headers.get("Content-Length"):
                headers["Content-Length"] = response.headers.get("Content-Length")
            
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=200,
                headers=headers
            )
    except Exception as e:
        return {"error": str(e), "success": False}

# ============================================
# WORKER-POWERED STREAM (Clean)
# ============================================

@app.get("/api/watch/{subject_id}")
async def api_watch(
    subject_id: str,
    detail_path: str,
    resolution: str = "720",
    se: int = None,
    ep: int = None
):
    """
    Proxied stream through Megan Stream Engine
    - Hides Worker URL completely
    - Zero-buffer streaming
    - Supports TV episodes with se/ep parameters
    """
    params = {"detail_path": detail_path, "resolution": resolution}
    if se is not None and ep is not None:
        params["se"] = se
        params["ep"] = ep
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(
                f"{WORKER_URL}/watch/{subject_id}",
                params=params,
                headers={"Range": request.headers.get("Range") if hasattr(request, 'headers') else None}
            )
            
            if response.status_code not in (200, 206):
                return {"error": f"Stream engine returned {response.status_code}", "success": False}
            
            headers = {
                "Content-Type": response.headers.get("Content-Type", "video/mp4"),
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
            }
            if response.headers.get("Content-Length"):
                headers["Content-Length"] = response.headers.get("Content-Length")
            if response.headers.get("Content-Range"):
                headers["Content-Range"] = response.headers.get("Content-Range")
            
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=response.status_code,
                headers=headers
            )
    except Exception as e:
        return {"error": str(e), "success": False}

# ============================================
# STREAM SOURCES (JSON)
# ============================================

@app.get("/api/sources/{subject_id}")
async def get_sources(
    subject_id: str,
    detail_path: str,
    se: int = None,
    ep: int = None
):
    """Get available stream sources from Worker"""
    params = {"detail_path": detail_path}
    if se is not None and ep is not None:
        params["se"] = se
        params["ep"] = ep
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{WORKER_URL}/api/stream/{subject_id}",
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "api": "Megan Movie API",
                    "creator": "Megan / Wanga",
                    "data": data
                }
            return {"success": False, "error": f"Worker returned {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
        "version": "3.0.0",
        "domain": DOMAIN,
        "stream_engine": "Megan Stream Engine (Cloudflare Workers)"
    }

# ============================================
# LEGACY COMPATIBILITY (Redirect old endpoints)
# ============================================

@app.get("/api/dl")
async def legacy_download(url: str = None):
    """Legacy endpoint - returns deprecation notice"""
    return {
        "success": False,
        "error": "This endpoint is deprecated. Use /api/download/{subject_id}?detail_path=...",
        "migration_note": "Check /api/movies/{title} for new URL format"
    }

@app.get("/api/proxy/dl")
async def legacy_proxy_download():
    return await legacy_download()

@app.get("/api/prince/search/{query}")
async def legacy_prince_search():
    return {"success": False, "error": "Prince API integration removed. Use /api/search instead."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
