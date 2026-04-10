from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime

from moviebox_api.v2 import Search, Session
from moviebox_api.v2 import MovieDetails
from moviebox_api.v2.core import SubjectType

from helpers import get_prince_downloads, get_vidsrc_streams, get_omdb_data

router = APIRouter(prefix="/api/movies", tags=["movies"])

session = Session()

def generate_megan_id(imdb_id: str = None, subject_id: str = None) -> str:
    if imdb_id:
        return f"megan-{imdb_id}"
    elif subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"

def extract_image(item):
    if hasattr(item, 'cover') and item.cover:
        cover = item.cover
        return {
            "url": str(cover.url),
            "width": cover.width,
            "height": cover.height,
            "size_kb": round(cover.size / 1024, 2) if cover.size else 0
        }
    return None

@router.get("/{title}")
async def get_movie(title: str, year: Optional[int] = None):
    # 1. Search for movie
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Find best match
    movie_item = None
    for item in results.items:
        if year and item.releaseDate and item.releaseDate.year == year:
            movie_item = item
            break
    if not movie_item:
        movie_item = results.items[0]
    
    subject_id = movie_item.subjectId
    
    # 2. Get full movie details
    details_obj = MovieDetails(session)
    full_details = await details_obj.get_content(movie_item.detailPath)
    
    # 3. Get OMDb data
    omdb_data = await get_omdb_data(title=movie_item.title, year=movie_item.releaseDate.year if movie_item.releaseDate else None)
    imdb_id = omdb_data.get("imdbID") if omdb_data else None
    
    # 4. Get downloads from PRINCE (using helper)
    downloads = await get_prince_downloads(subject_id)
    
    # 5. Get streams from vidsrc (fallback)
    streams = []
    if imdb_id:
        streams = await get_vidsrc_streams(imdb_id)
    
    # 6. Build response
    poster = extract_image(movie_item)
    
    backdrop = None
    if movie_item and hasattr(movie_item, 'stills') and movie_item.stills:
        backdrop = {
            "url": str(movie_item.stills.url),
            "width": movie_item.stills.width,
            "height": movie_item.stills.height,
            "size_kb": round(movie_item.stills.size / 1024, 2) if movie_item.stills.size else 0
        }
    
    trailer = None
    if full_details and 'subject' in full_details:
        trailer_data = full_details.get('subject', {}).get('trailer', {})
        if trailer_data and 'videoAddress' in trailer_data:
            trailer = {
                "url": trailer_data['videoAddress'].get('url'),
                "duration": trailer_data['videoAddress'].get('duration'),
                "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
            }
    
    cast = []
    if full_details and 'stars' in full_details:
        for star in full_details.get('stars', [])[:15]:
            cast.append({
                "name": star.get('name'),
                "character": star.get('character'),
                "avatar": star.get('avatarUrl')
            })
    
    subtitles = []
    if movie_item and hasattr(movie_item, 'subtitles') and movie_item.subtitles:
        subs = movie_item.subtitles.split(',') if isinstance(movie_item.subtitles, str) else movie_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "movie": {
                "megan_id": generate_megan_id(imdb_id, str(movie_item.subjectId)),
                "imdb_id": imdb_id,
                "title": movie_item.title,
                "year": movie_item.releaseDate.year if movie_item.releaseDate else None,
                "runtime": omdb_data.get("Runtime") if omdb_data else None,
                "release_date": movie_item.releaseDate.isoformat() if movie_item.releaseDate else None,
                "genres": movie_item.genre if isinstance(movie_item.genre, list) else (movie_item.genre.split(',') if movie_item.genre else []),
                "director": omdb_data.get("Director") if omdb_data else None,
                "cast": cast,
                "plot": omdb_data.get("Plot") if omdb_data else movie_item.description,
                "poster": poster,
                "backdrop": backdrop,
                "trailer": trailer,
                "ratings": {
                    "imdb": float(omdb_data.get("imdbRating", 0)) if omdb_data and omdb_data.get("imdbRating") != "N/A" else None,
                    "imdb_votes": omdb_data.get("imdbVotes") if omdb_data else None
                },
                "subtitles": subtitles
            },
            "sources": {
                "downloads": downloads,
                "streams": streams
            }
        }
    }
