from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime

from moviebox_api.v2 import Search, Session, TVSeriesDetails
from moviebox_api.v2.download import DownloadableTVSeriesFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/tv", tags=["tv_series"])

# Configuration
OMDB_API_KEY = "9b5d7e52"
OMDB_URL = "http://www.omdbapi.com/"
VIDSRC_API_URL = "https://megan-vidsrc.vercel.app"

# Cache for OMDb results
omdb_cache = {}

session = Session()

async def get_omdb_data(imdb_id: str = None, title: str = None, year: int = None):
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

async def get_vidsrc_streams(imdb_id: str, season: int = 1, episode: int = 1):
    """Get proxied stream URLs for TV episode"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Vidsrc TV format: /tv/{imdb_id}/{season}/{episode}
            response = await client.get(f"{VIDSRC_API_URL}/api/tv/{imdb_id}/{season}/{episode}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("streams", [])
        except Exception as e:
            print(f"Vidsrc error: {e}")
    
    # Fallback to movie-style streams (might not work for TV)
    try:
        response = await client.get(f"{VIDSRC_API_URL}/api/streams/{imdb_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("streams", [])
    except:
        pass
    
    return []

def generate_megan_id(imdb_id: str = None, subject_id: str = None) -> str:
    """Generate Megan ID"""
    if imdb_id:
        return f"megan-{imdb_id}"
    elif subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"

@router.get("/search")
async def search_tv(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Results limit")
):
    """Search for TV series only"""
    
    search = Search(session, query=q, subject_type=SubjectType.TV_SERIES)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e), "query": q}
    
    items = []
    for item in results.items[:limit]:
        year = item.releaseDate.year if item.releaseDate else None
        
        items.append({
            "title": item.title,
            "year": year,
            "rating": item.imdbRatingValue,
            "poster": item.cover.url if item.cover else None,
            "detailPath": item.detailPath,
            "subjectId": str(item.subjectId) if item.subjectId else None
        })
    
    return {
        "success": True,
        "query": q,
        "total": len(items),
        "results": items
    }

@router.get("/{title}")
async def get_tv_series(
    title: str,
    year: Optional[int] = None,
    include_omdb: bool = Query(True, description="Include OMDb metadata"),
    include_streams: bool = Query(True, description="Include stream URLs")
):
    """Get complete TV series data: metadata + seasons + episodes + downloads + streams"""
    
    # 1. Search for TV series
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    # Find best match by year
    series_item = None
    for item in results.items:
        if year and item.releaseDate and item.releaseDate.year == year:
            series_item = item
            break
    if not series_item:
        series_item = results.items[0]
    
    # 2. Get series details (seasons, episodes)
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(series_item.detailPath)
    
    # 3. Get OMDb data if requested
    omdb_data = None
    imdb_id = None
    if include_omdb:
        omdb_data = await get_omdb_data(title=series_item.title, year=series_item.releaseDate.year if series_item.releaseDate else None)
        if omdb_data:
            imdb_id = omdb_data.get("imdbID")
    
    # 4. Extract seasons info
    resource = detail_data.get('resource', {})
    seasons_data = resource.get('seasons', [])
    
    seasons = []
    for season in seasons_data:
        se = season.get('se', 0)
        max_ep = season.get('maxEp', 0)
        resolutions = season.get('resolutions', [])
        
        seasons.append({
            "season": se,
            "max_episodes": max_ep,
            "available_qualities": [r.get('resolution') for r in resolutions]
        })
    
    # 5. Get episode download example (S1E1)
    episode_download = None
    try:
        downloads_obj = DownloadableTVSeriesFilesDetail(session, series_item)
        download_data = await downloads_obj.get_content(season=1, episode=1)
        
        if download_data and 'downloads' in download_data:
            episode_download = {
                "season": 1,
                "episode": 1,
                "downloads": [
                    {
                        "quality": f"{dl.get('resolution')}p",
                        "size_mb": round(int(dl.get('size', 0)) / 1024 / 1024, 2),
                        "url": dl.get('url')
                    }
                    for dl in download_data['downloads']
                ]
            }
    except Exception as e:
        print(f"Episode download error: {e}")
    
    # 6. Get streams if requested and imdb_id available
    streams = []
    if include_streams and imdb_id:
        streams = await get_vidsrc_streams(imdb_id, 1, 1)
    
    # 7. Extract poster with dimensions
    poster = None
    subject = detail_data.get('subject', {})
    cover = subject.get('cover', {})
    if cover:
        poster = {
            "url": cover.get('url'),
            "width": cover.get('width'),
            "height": cover.get('height'),
            "size_kb": round(cover.get('size', 0) / 1024, 2) if cover.get('size') else 0
        }
    
    # 8. Extract backdrop/stills
    backdrop = None
    stills = subject.get('stills', {})
    if stills:
        backdrop = {
            "url": stills.get('url'),
            "width": stills.get('width'),
            "height": stills.get('height'),
            "size_kb": round(stills.get('size', 0) / 1024, 2) if stills.get('size') else 0
        }
    
    # 9. Extract trailer
    trailer = None
    trailer_data = subject.get('trailer', {})
    video_addr = trailer_data.get('videoAddress', {})
    if video_addr:
        trailer = {
            "url": video_addr.get('url'),
            "duration": video_addr.get('duration'),
            "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
        }
    
    # 10. Extract cast
    cast = []
    stars = detail_data.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # 11. Extract subtitles
    subtitles = []
    if series_item and hasattr(series_item, 'subtitles') and series_item.subtitles:
        subs = series_item.subtitles.split(',') if isinstance(series_item.subtitles, str) else series_item.subtitles
        code_map = {
            "English": "en", "Arabic": "ar", "French": "fr", "Spanish": "es",
            "Indonesian": "id", "Malay": "ms", "Portuguese": "pt", "Russian": "ru",
            "Swahili": "sw", "Urdu": "ur", "Bengali": "bn", "Punjabi": "pa",
            "Chinese": "zh", "Filipino": "fil", "German": "de", "Italian": "it",
            "Japanese": "ja", "Korean": "ko", "Turkish": "tr", "Hindi": "hi"
        }
        for sub in subs[:20]:
            if sub.strip():
                lang = sub.strip()
                code = code_map.get(lang, lang[:2].lower())
                subtitles.append({"language": lang, "code": code})
    
    # 12. Build response
    response = {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "series": {
                "megan_id": generate_megan_id(imdb_id, str(series_item.subjectId)),
                "imdb_id": imdb_id,
                "title": series_item.title,
                "year": omdb_data.get("Year") if omdb_data else (series_item.releaseDate.year if series_item.releaseDate else None),
                "rated": omdb_data.get("Rated") if omdb_data else None,
                "runtime": omdb_data.get("Runtime") if omdb_data else None,
                "genres": series_item.genre if isinstance(series_item.genre, list) else (series_item.genre.split(',') if series_item.genre else []),
                "director": omdb_data.get("Director") if omdb_data else None,
                "cast": cast,
                "plot": omdb_data.get("Plot") if omdb_data else subject.get('description'),
                "poster": poster,
                "backdrop": backdrop,
                "trailer": trailer,
                "ratings": {
                    "imdb": float(omdb_data.get("imdbRating", 0)) if omdb_data and omdb_data.get("imdbRating") != "N/A" else series_item.imdbRatingValue,
                    "imdb_votes": omdb_data.get("imdbVotes") if omdb_data else None,
                    "rotten_tomatoes": None,
                    "metacritic": None
                },
                "subtitles": subtitles,
                "seasons": seasons,
                "total_seasons": len(seasons)
            },
            "sources": {
                "episode_download": episode_download,
                "streams": streams
            }
        }
    }
    
    # Add OMDB ratings if available
    if omdb_data:
        for rating in omdb_data.get("Ratings", []):
            if rating.get("Source") == "Rotten Tomatoes":
                response["data"]["series"]["ratings"]["rotten_tomatoes"] = rating.get("Value")
            elif rating.get("Source") == "Metacritic":
                response["data"]["series"]["ratings"]["metacritic"] = rating.get("Value")
    
    return response

@router.get("/{title}/episode")
async def get_tv_episode(
    title: str,
    season: int = Query(..., ge=1, description="Season number"),
    episode: int = Query(..., ge=1, description="Episode number"),
    year: Optional[int] = None
):
    """Get download and stream URLs for a specific episode"""
    
    # Search for TV series
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    
    # Get OMDb data for IMDb ID
    omdb_data = await get_omdb_data(title=series_item.title, year=series_item.releaseDate.year if series_item.releaseDate else None)
    imdb_id = omdb_data.get("imdbID") if omdb_data else None
    
    # Get episode download
    episode_download = None
    try:
        downloads_obj = DownloadableTVSeriesFilesDetail(session, series_item)
        download_data = await downloads_obj.get_content(season=season, episode=episode)
        
        if download_data and 'downloads' in download_data:
            episode_download = {
                "season": season,
                "episode": episode,
                "downloads": [
                    {
                        "quality": f"{dl.get('resolution')}p",
                        "size_mb": round(int(dl.get('size', 0)) / 1024 / 1024, 2),
                        "url": dl.get('url')
                    }
                    for dl in download_data['downloads']
                ]
            }
    except Exception as e:
        print(f"Episode download error: {e}")
    
    # Get streams
    streams = []
    if imdb_id:
        streams = await get_vidsrc_streams(imdb_id, season, episode)
    
    return {
        "success": True,
        "series": series_item.title,
        "season": season,
        "episode": episode,
        "imdb_id": imdb_id,
        "megan_id": generate_megan_id(imdb_id, str(series_item.subjectId)),
        "downloads": episode_download,
        "streams": streams
    }

@router.get("/{title}/seasons")
async def get_tv_seasons(title: str, year: Optional[int] = None):
    """Get all seasons and episodes info for a TV series"""
    
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(series_item.detailPath)
    
    resource = detail_data.get('resource', {})
    seasons_data = resource.get('seasons', [])
    
    seasons = []
    for season in seasons_data:
        se = season.get('se', 0)
        max_ep = season.get('maxEp', 0)
        resolutions = season.get('resolutions', [])
        
        seasons.append({
            "season": se,
            "max_episodes": max_ep,
            "available_qualities": [r.get('resolution') for r in resolutions],
            "episodes_available": max_ep > 0
        })
    
    return {
        "success": True,
        "title": series_item.title,
        "total_seasons": len(seasons),
        "seasons": seasons,
        "example": f"/api/tv/{title}/episode?season=1&episode=1"
    }
