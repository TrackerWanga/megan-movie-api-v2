import httpx
from urllib.parse import quote
from typing import Optional, List, Dict, Any

PRINCE_API = "https://movieapi.princetechn.com"
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"

async def get_prince_sources(subject_id: str, season: int = None, episode: int = None) -> Optional[Dict]:
    """Fetch sources from PRINCE API (hidden from users)"""
    url = f"{PRINCE_API}/api/sources/{subject_id}"
    if season and episode:
        url += f"?season={season}&episode={episode}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"PRINCE API error: {e}")
    return None

async def get_prince_downloads(subject_id: str) -> List[Dict]:
    """Extract direct download URLs from PRINCE response"""
    prince_data = await get_prince_sources(subject_id)
    downloads = []
    
    if prince_data:
        for source in prince_data.get("results", []):
            # Look for direct MP4 downloads from MovieBox
            if source.get("type") == "direct" and "MovieBox" in source.get("provider", ""):
                original_url = source.get("download_url") or source.get("embed_url")
                if original_url:
                    downloads.append({
                        "quality": source.get("quality"),
                        "size_mb": round(int(source.get("size", 0)) / 1024 / 1024, 2) if source.get("size") else 0,
                        "url": original_url,
                        "proxied_url": f"{MEGAN_DOMAIN}/api/proxy/dl?url={quote(original_url, safe='')}"
                    })
    
    return downloads

async def get_prince_streams(subject_id: str) -> List[Dict]:
    """Extract embed stream URLs from PRINCE response"""
    prince_data = await get_prince_sources(subject_id)
    streams = []
    
    if prince_data:
        for source in prince_data.get("results", []):
            # Look for embed providers (VidLink, AutoEmbed, EmbedSU, etc.)
            if source.get("type") == "embed" or "stream_url" in source:
                streams.append({
                    "provider": source.get("provider"),
                    "quality": source.get("quality", "Auto"),
                    "embed_url": source.get("stream_url") or source.get("embed_url"),
                    "type": "embed"
                })
    
    return streams

async def get_prince_info(subject_id: str) -> Optional[Dict]:
    """Get metadata from PRINCE API"""
    url = f"{PRINCE_API}/api/info/{subject_id}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"PRINCE info error: {e}")
    return None

async def get_prince_search(query: str, type: int = 1) -> Optional[Dict]:
    """Search using PRINCE API"""
    url = f"{PRINCE_API}/api/search/{query}?type={type}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"PRINCE search error: {e}")
    return None
