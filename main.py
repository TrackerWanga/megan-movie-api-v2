import enum
import sys
import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
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

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.download import DownloadableSingleFilesDetail, DownloadableTVSeriesFilesDetail
from moviebox_api.v2.core import SubjectType

app = FastAPI(title="Megan Movie API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OMDB_API_KEY = "9b5d7e52"
OMDB_URL = "http://www.omdbapi.com/"
VIDSRC_API_URL = "https://megan-vidsrc.vercel.app"

session = Session()

def is_tv_series(item) -> bool:
    """Check if item is a TV series (subjectType 2)"""
    return item.subjectType == SubjectType.TV_SERIES

def is_movie(item) -> bool:
    """Check if item is a movie (subjectType 1)"""
    return item.subjectType == SubjectType.MOVIES

async def get_omdb_data(imdb_id: str = None, title: str = None, year: int = None):
    """Get OMDb metadata"""
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
                return data
        except Exception as e:
            print(f"OMDb error: {e}")
    return None

async def get_vidsrc_streams(imdb_id: str):
    """Get proxied stream URLs"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(f"{VIDSRC_API_URL}/api/streams/{imdb_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("streams", [])
        except Exception as e:
            print(f"Vidsrc error: {e}")
    return []

@app.get("/api/movie/{title}")
async def get_movie(title: str, year: Optional[int] = None):
    """Get COMPLETE movie/TV series data with ALL metadata"""
    try:
        # 1. Get OMDb data
        omdb = await get_omdb_data(title=title, year=year)
        if not omdb:
            return {"success": False, "error": "Movie/TV series not found"}
        
        imdb_id = omdb.get("imdbID")
        
        # 2. Get moviebox_api data
        search_obj = Search(session, query=title)
        results = await search_obj.get_content_model()
        
        moviebox_item = None
        if results.items:
            for item in results.items:
                if item.releaseDate and str(item.releaseDate.year) == omdb.get("Year", ""):
                    moviebox_item = item
                    break
            if not moviebox_item:
                moviebox_item = results.items[0]
        
        # 3. Determine content type
        content_type = "movie" if moviebox_item and is_movie(moviebox_item) else "tv_series"
        
        # 4. Get FULL details (contains stars/cast)
        full_details = None
        if moviebox_item:
            from moviebox_api.v2 import MovieDetails, TVSeriesDetails
            
            if content_type == "movie":
                details_obj = MovieDetails(session)
            else:
                details_obj = TVSeriesDetails(session)
            full_details = await details_obj.get_content(moviebox_item.detailPath)
        
        # 5. Get vidsrc streams
        streams = await get_vidsrc_streams(imdb_id) if imdb_id else []
        
        # 6. Get downloads (different for movies vs TV series)
        downloads = []
        if moviebox_item:
            try:
                if content_type == "movie":
                    # Movies: use DownloadableSingleFilesDetail
                    downloads_obj = DownloadableSingleFilesDetail(session, moviebox_item)
                    download_data = await downloads_obj.get_content()
                    if download_data and 'downloads' in download_data:
                        for dl in download_data['downloads']:
                            size_val = dl.get('size', '0')
                            try:
                                size_mb = round(int(size_val) / 1024 / 1024, 2)
                            except:
                                size_mb = 0
                            downloads.append({
                                "quality": f"{dl.get('resolution')}p",
                                "size_mb": size_mb,
                                "url": dl.get('url')
                            })
                else:
                    # TV Series: need to show available seasons/episodes info
                    # Note: Actual download requires season/episode parameters
                    # We'll show what's available instead
                    if full_details and 'resource' in full_details:
                        seasons_data = full_details.get('resource', {}).get('seasons', [])
                        downloads = {
                            "note": "TV series episodes require specific season/episode parameters",
                            "available_seasons": [
                                {
                                    "season": s.get('se'),
                                    "episodes": s.get('maxEp'),
                                    "resolutions": [r.get('resolution') for r in s.get('resolutions', [])]
                                }
                                for s in seasons_data
                            ],
                            "example": "/api/download/tt0903747?season=1&episode=1"
                        }
            except Exception as e:
                print(f"Downloads error: {e}")
        
        # 7. Poster with dimensions
        poster = None
        if moviebox_item and moviebox_item.cover:
            poster = {
                "url": str(moviebox_item.cover.url),
                "width": moviebox_item.cover.width,
                "height": moviebox_item.cover.height,
                "size_kb": round(moviebox_item.cover.size / 1024, 2) if moviebox_item.cover.size else 0
            }
        elif omdb.get("Poster") and omdb.get("Poster") != "N/A":
            poster = {"url": omdb.get("Poster"), "width": None, "height": None, "size_kb": None}
        
        # 8. Backdrop/stills
        backdrop = None
        if moviebox_item and hasattr(moviebox_item, 'stills') and moviebox_item.stills:
            backdrop = {
                "url": str(moviebox_item.stills.url),
                "width": moviebox_item.stills.width,
                "height": moviebox_item.stills.height,
                "size_kb": round(moviebox_item.stills.size / 1024, 2) if moviebox_item.stills.size else 0
            }
        
        # 9. Trailer
        trailer = None
        if full_details and 'subject' in full_details:
            trailer_data = full_details.get('subject', {}).get('trailer', {})
            if trailer_data and 'videoAddress' in trailer_data:
                trailer = {
                    "url": trailer_data['videoAddress'].get('url'),
                    "duration": trailer_data['videoAddress'].get('duration'),
                    "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
                }
        
        # 10. Subtitles
        subtitles = []
        if moviebox_item and hasattr(moviebox_item, 'subtitles') and moviebox_item.subtitles:
            subs = moviebox_item.subtitles.split(',') if isinstance(moviebox_item.subtitles, str) else moviebox_item.subtitles
            for sub in subs[:20]:
                if sub.strip():
                    lang = sub.strip()
                    code_map = {
                        "English": "en", "Arabic": "ar", "French": "fr", "Spanish": "es",
                        "Indonesian": "id", "Malay": "ms", "Portuguese": "pt", "Russian": "ru",
                        "Swahili": "sw", "Urdu": "ur", "Bengali": "bn", "Punjabi": "pa",
                        "Chinese": "zh", "Filipino": "fil", "Kiswahili": "sw", "German": "de",
                        "Italian": "it", "Japanese": "ja", "Korean": "ko", "Turkish": "tr",
                        "Hindi": "hi", "Tamil": "ta", "Telugu": "te"
                    }
                    code = code_map.get(lang, lang[:2].lower())
                    subtitles.append({"language": lang, "code": code})
        
        # 11. Cast from stars array
        cast = []
        if full_details and 'stars' in full_details:
            for star in full_details.get('stars', [])[:15]:
                cast.append({
                    "name": star.get('name'),
                    "character": star.get('character'),
                    "avatar": star.get('avatarUrl')
                })
        
        # Fallback to OMDb if no cast
        if not cast and omdb.get("Actors"):
            actor_names = omdb.get("Actors", "").split(", ")
            for actor in actor_names[:10]:
                cast.append({
                    "name": actor,
                    "character": None,
                    "avatar": None
                })
        
        # 12. Ratings
        ratings = {
            "imdb": float(omdb.get("imdbRating", 0)) if omdb.get("imdbRating") != "N/A" else None,
            "imdb_votes": omdb.get("imdbVotes", "N/A"),
            "rotten_tomatoes": None,
            "metacritic": None
        }
        for rating in omdb.get("Ratings", []):
            if rating.get("Source") == "Rotten Tomatoes":
                ratings["rotten_tomatoes"] = rating.get("Value")
            elif rating.get("Source") == "Metacritic":
                ratings["metacritic"] = rating.get("Value")
        
        # 13. Build response
        return {
            "success": True,
            "api": "Megan Movie API",
            "data": {
                "movie": {
                    "id": {
                        "imdb": imdb_id,
                        "tmdb": None,
                        "moviebox": moviebox_item.subjectId if moviebox_item else None
                    },
                    "title": omdb.get("Title"),
                    "year": omdb.get("Year"),
                    "rated": omdb.get("Rated"),
                    "runtime": omdb.get("Runtime"),
                    "release_date": moviebox_item.releaseDate.isoformat() if moviebox_item and moviebox_item.releaseDate else None,
                    "genres": omdb.get("Genre", "").split(", ") if omdb.get("Genre") != "N/A" else (moviebox_item.genre if moviebox_item else []),
                    "director": omdb.get("Director"),
                    "cast": cast,
                    "plot": omdb.get("Plot"),
                    "poster": poster,
                    "backdrop": backdrop,
                    "trailer": trailer,
                    "ratings": ratings,
                    "subtitles": subtitles,
                    "type": content_type
                },
                "sources": {
                    "downloads": downloads,
                    "streams": streams
                }
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/download/{imdb_id}")
async def download_episode(imdb_id: str, season: int = 1, episode: int = 1):
    """Download a specific TV episode (requires season and episode)"""
    try:
        # Search for the series
        search_obj = Search(session, query=imdb_id)
        results = await search_obj.get_content_model()
        
        if not results.items:
            return {"success": False, "error": "Series not found"}
        
        series_item = results.items[0]
        
        # Check if it's a TV series
        if not is_tv_series(series_item):
            return {"success": False, "error": "Not a TV series"}
        
        # Download specific episode
        downloads_obj = DownloadableTVSeriesFilesDetail(session, series_item)
        download_data = await downloads_obj.get_content(season=season, episode=episode)
        
        if download_data and 'downloads' in download_data:
            return {
                "success": True,
                "type": "tv_series",
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
        else:
            return {"success": False, "error": "Episode not available"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
