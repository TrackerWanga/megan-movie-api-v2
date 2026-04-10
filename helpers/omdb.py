import httpx
from typing import Optional, Dict

OMDB_API_KEY = "9b5d7e52"
OMDB_URL = "http://www.omdbapi.com/"
omdb_cache = {}

async def get_omdb_data(imdb_id: str = None, title: str = None, year: int = None) -> Optional[Dict]:
    """Get OMDb metadata with caching"""
    cache_key = imdb_id or f"{title}_{year}"
    
    if cache_key in omdb_cache:
        return omdb_cache[cache_key]
    
    params = {"apikey": OMDB_API_KEY, "plot": "full"}
    if imdb_id:
        params["i"] = imdb_id
    elif title:
        params["t"] = title
        if year:
            params["y"] = year
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OMDB_URL, params=params)
            data = response.json()
            if data.get("Response") == "True":
                omdb_cache[cache_key] = data
                return data
        except Exception as e:
            print(f"OMDb error: {e}")
    
    omdb_cache[cache_key] = None
    return None

async def get_imdb_id(title: str, year: int = None) -> Optional[str]:
    """Get IMDb ID from title"""
    data = await get_omdb_data(title=title, year=year)
    return data.get("imdbID") if data else None
