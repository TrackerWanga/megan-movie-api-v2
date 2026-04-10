import httpx
from typing import List, Dict, Optional

VIDSRC_API = "https://megan-vidsrc.vercel.app"

async def get_vidsrc_streams(imdb_id: str, season: int = 1, episode: int = 1) -> List[Dict]:
    """Get stream URLs from vidsrc API"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(f"{VIDSRC_API}/api/streams/{imdb_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("streams", [])
        except Exception as e:
            print(f"Vidsrc error: {e}")
    
    # Fallback: return empty list
    return []
