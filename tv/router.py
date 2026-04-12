from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx

from moviebox_api.v2 import Search, Session, TVSeriesDetails
from moviebox_api.v2.download import DownloadableTVSeriesFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api", tags=["tv_series"])

# Configuration
WORKER_URL = "https://streamapi.megan.qzz.io"
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"

session = Session()

def generate_megan_id(subject_id: str = None) -> str:
    if subject_id:
        return f"megan-{subject_id}"
    return "megan-unknown"


# ============================================
# TV SERIES METADATA (Fast - No Episodes)
# ============================================

@router.get("/tv/{subject_id}")
async def get_tv_metadata(subject_id: str, detail_path: str = Query(None)):
    """
    Get TV series metadata WITHOUT episode URLs (fast).
    Use /tv/{id}/season/{season} to get episode URLs.
    """
    
    if detail_path:
        try:
            tv_details = TVSeriesDetails(session)
            detail_data = await tv_details.get_content(detail_path)
            subject = detail_data.get('subject', {})
            resource = detail_data.get('resource', {})
            
            return await build_tv_response(subject_id, detail_path, subject, resource, detail_data, include_episodes=False)
        except Exception as e:
            print(f"Error with detail_path: {e}")
    
    raise HTTPException(status_code=404, detail="TV series not found")


# ============================================
# TV SEASON WITH EPISODE URLs (Lazy Loaded)
# ============================================

@router.get("/tv/{subject_id}/season/{season}")
async def get_tv_season_episodes(
    subject_id: str,
    season: int,
    detail_path: str = Query(...),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """
    Get episodes for a specific season WITH download/stream URLs.
    This is called when the user expands a season.
    """
    
    resolution = quality.replace('p', '')
    
    # Get series_item for downloads
    search = Search(session, query=subject_id, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    
    episodes = []
    
    try:
        # Get season info to know max episodes
        tv_details = TVSeriesDetails(session)
        detail_data = await tv_details.get_content(detail_path)
        resource = detail_data.get('resource', {})
        seasons_data = resource.get('seasons', [])
        
        target_season = None
        for s in seasons_data:
            if s.get('se') == season:
                target_season = s
                break
        
        if not target_season:
            raise HTTPException(status_code=404, detail=f"Season {season} not found")
        
        max_ep = target_season.get('maxEp', 0)
        
        # Fetch download URLs for each episode
        for ep in range(1, max_ep + 1):
            try:
                downloads_obj = DownloadableTVSeriesFilesDetail(session, series_item)
                download_data = await downloads_obj.get_content(season=season, episode=ep)
                
                download_url = None
                size_mb = 0
                
                if download_data and 'downloads' in download_data:
                    # Find the requested quality or best available
                    for dl in download_data['downloads']:
                        dl_quality = f"{dl.get('resolution')}p"
                        if dl_quality == quality:
                            download_url = dl.get('url')
                            size_bytes = dl.get('size', 0)
                            try:
                                size_mb = round(int(size_bytes) / 1024 / 1024, 2)
                            except:
                                size_mb = 0
                            break
                    
                    # If requested quality not found, use first available
                    if not download_url and download_data['downloads']:
                        best = download_data['downloads'][0]
                        download_url = best.get('url')
                        size_bytes = best.get('size', 0)
                        try:
                            size_mb = round(int(size_bytes) / 1024 / 1024, 2)
                        except:
                            size_mb = 0
                
                episodes.append({
                    "episode": ep,
                    "name": f"Episode {ep}",
                    "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={season}&ep={ep}&resolution={resolution}" if download_url else None,
                    "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={season}&ep={ep}&resolution={resolution}",
                    "size_mb": size_mb
                })
                
            except Exception as e:
                print(f"Error fetching episode {ep}: {e}")
                episodes.append({
                    "episode": ep,
                    "name": f"Episode {ep}",
                    "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={season}&ep={ep}&resolution={resolution}",
                    "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={season}&ep={ep}&resolution={resolution}",
                    "size_mb": 0
                })
    
    except Exception as e:
        print(f"Error getting season data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get episodes: {str(e)}")
    
    return {
        "success": True,
        "season": season,
        "quality": quality,
        "episodes": episodes
    }


# ============================================
# ALL SEASONS WITH EPISODES (Full Load - Slower)
# ============================================

@router.get("/tv/{subject_id}/full")
async def get_tv_full(subject_id: str, detail_path: str = Query(None)):
    """
    Get COMPLETE TV series with all episodes for all seasons.
    WARNING: This is slow! Use /tv/{id} + /tv/{id}/season/{season} for better UX.
    """
    
    if detail_path:
        try:
            tv_details = TVSeriesDetails(session)
            detail_data = await tv_details.get_content(detail_path)
            subject = detail_data.get('subject', {})
            resource = detail_data.get('resource', {})
            
            # Get series_item for downloads
            title = subject.get('title', '')
            search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
            results = await search.get_content_model()
            series_item = results.items[0] if results.items else None
            
            return await build_tv_response(subject_id, detail_path, subject, resource, detail_data, 
                                          series_item=series_item, include_episodes=True)
        except Exception as e:
            print(f"Error with detail_path: {e}")
    
    raise HTTPException(status_code=404, detail="TV series not found")


async def build_tv_response(
    subject_id: str, 
    detail_path: str, 
    subject: dict, 
    resource: dict, 
    detail_data: dict,
    series_item=None,
    include_episodes: bool = False
):
    """Build the TV series response"""
    
    # Extract seasons metadata
    seasons_data = resource.get('seasons', [])
    seasons = []
    
    for season in seasons_data:
        se = season.get('se', 0)
        max_ep = season.get('maxEp', 0)
        resolutions = season.get('resolutions', [])
        
        season_obj = {
            "season": se,
            "max_episodes": max_ep,
            "available_qualities": [r.get('resolution') for r in resolutions],
            "episodes": []
        }
        
        # Only fetch episodes if requested (slow!)
        if include_episodes and series_item:
            for ep in range(1, min(max_ep + 1, 11)):  # Max 10 episodes per season
                try:
                    downloads_obj = DownloadableTVSeriesFilesDetail(session, series_item)
                    download_data = await downloads_obj.get_content(season=se, episode=ep)
                    
                    download_url = None
                    if download_data and 'downloads' in download_data and download_data['downloads']:
                        download_url = download_data['downloads'][0].get('url')
                    
                    season_obj["episodes"].append({
                        "episode": ep,
                        "name": f"Episode {ep}",
                        "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={se}&ep={ep}&resolution=720" if download_url else None,
                        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={se}&ep={ep}&resolution=720"
                    })
                except:
                    pass
        
        seasons.append(season_obj)
    
    # Extract poster
    cover = subject.get('cover', {})
    poster = None
    if cover:
        poster = {
            "url": cover.get('url'),
            "width": cover.get('width'),
            "height": cover.get('height')
        }
    
    # Extract backdrop
    stills = subject.get('stills', {})
    backdrop = None
    if stills:
        backdrop = {
            "url": stills.get('url'),
            "width": stills.get('width'),
            "height": stills.get('height')
        }
    
    # Extract trailer
    trailer = None
    trailer_data = subject.get('trailer', {})
    video_addr = trailer_data.get('videoAddress', {})
    if video_addr:
        trailer = {
            "url": video_addr.get('url'),
            "duration": video_addr.get('duration'),
            "thumbnail": trailer_data.get('cover', {}).get('url') if trailer_data.get('cover') else None
        }
    
    # Extract cast
    cast = []
    stars = detail_data.get('stars', [])
    for star in stars[:15]:
        cast.append({
            "name": star.get('name'),
            "character": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # Extract subtitles
    subtitles = []
    if series_item and hasattr(series_item, 'subtitles') and series_item.subtitles:
        subs = series_item.subtitles.split(',') if isinstance(series_item.subtitles, str) else series_item.subtitles
        for sub in subs[:20]:
            if sub.strip():
                subtitles.append({"language": sub.strip(), "code": sub.strip()[:2].lower()})
    
    title = subject.get('title', 'Unknown')
    year = subject.get('releaseDate', '')[:4] if subject.get('releaseDate') else None
    try:
        year = int(year) if year else None
    except:
        year = None
    
    rating = subject.get('imdbRatingValue')
    try:
        rating = float(rating) if rating else None
    except:
        rating = None
    
    genres_str = subject.get('genre', '')
    genres = [g.strip() for g in genres_str.split(',')] if genres_str else []
    
    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "data": {
            "id": subject_id,
            "megan_id": generate_megan_id(subject_id),
            "detail_path": detail_path,
            "title": title,
            "year": year,
            "genres": genres,
            "rating": rating,
            "description": subject.get('description', ''),
            "poster": poster,
            "backdrop": backdrop,
            "trailer": trailer,
            "cast": cast,
            "subtitles": subtitles,
            "seasons": seasons,
            "total_seasons": len(seasons),
            "note": "Use /api/tv/{id}/season/{season}?detail_path={path} to get episode download/stream URLs" if not include_episodes else None
        }
    }


# ============================================
# TV SEASONS (Metadata only - Fast)
# ============================================

@router.get("/tv/{subject_id}/seasons")
async def get_tv_seasons(subject_id: str, detail_path: str = Query(...)):
    """Get seasons metadata only (no episode URLs)"""
    
    tv_details = TVSeriesDetails(session)
    detail_data = await tv_details.get_content(detail_path)
    
    resource = detail_data.get('resource', {})
    seasons_data = resource.get('seasons', [])
    
    seasons = []
    for season in seasons_data:
        seasons.append({
            "season": season.get('se', 0),
            "episodes": season.get('maxEp', 0),
            "available_qualities": [r.get('resolution') for r in season.get('resolutions', [])]
        })
    
    return {
        "success": True,
        "total_seasons": len(seasons),
        "seasons": seasons
    }


# ============================================
# SINGLE EPISODE
# ============================================

@router.get("/tv/{subject_id}/episode")
async def get_tv_episode(
    subject_id: str,
    detail_path: str = Query(...),
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Get download/stream URLs for a specific episode"""
    
    resolution = quality.replace('p', '')
    
    # Get series_item for downloads
    search = Search(session, query=subject_id, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    
    download_url = None
    size_mb = 0
    
    try:
        downloads_obj = DownloadableTVSeriesFilesDetail(session, series_item)
        download_data = await downloads_obj.get_content(season=season, episode=episode)
        
        if download_data and 'downloads' in download_data:
            for dl in download_data['downloads']:
                dl_quality = f"{dl.get('resolution')}p"
                if dl_quality == quality:
                    download_url = dl.get('url')
                    size_bytes = dl.get('size', 0)
                    try:
                        size_mb = round(int(size_bytes) / 1024 / 1024, 2)
                    except:
                        size_mb = 0
                    break
            
            if not download_url and download_data['downloads']:
                best = download_data['downloads'][0]
                download_url = best.get('url')
                size_bytes = best.get('size', 0)
                try:
                    size_mb = round(int(size_bytes) / 1024 / 1024, 2)
                except:
                    size_mb = 0
    except Exception as e:
        print(f"Download error: {e}")
    
    return {
        "success": True,
        "season": season,
        "episode": episode,
        "quality": quality,
        "download": {
            "url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}" if download_url else None,
            "size_mb": size_mb
        },
        "stream": {
            "url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
        }
    }


# ============================================
# TV DOWNLOAD (Direct)
# ============================================

@router.get("/tv/{subject_id}/download")
async def download_tv(
    subject_id: str,
    detail_path: str = Query(...),
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Direct download URL for TV episode"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "download_url": f"{MEGAN_DOMAIN}/api/download/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
    }


@router.get("/tv/{subject_id}/stream")
async def stream_tv(
    subject_id: str,
    detail_path: str = Query(...),
    season: int = Query(..., ge=1),
    episode: int = Query(..., ge=1),
    quality: str = Query("720p", description="360p, 480p, 720p, 1080p")
):
    """Direct stream URL for TV episode"""
    resolution = quality.replace('p', '')
    return {
        "success": True,
        "stream_url": f"{MEGAN_DOMAIN}/api/watch/{subject_id}?detail_path={detail_path}&se={season}&ep={episode}&resolution={resolution}"
    }


# ============================================
# LEGACY ENDPOINTS
# ============================================

@router.get("/tv/{title}")
async def get_tv_legacy(title: str, year: Optional[int] = None):
    """[DEPRECATED] Use search then /api/tv/{id}?detail_path={path}"""
    
    search = Search(session, query=title, subject_type=SubjectType.TV_SERIES)
    results = await search.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="TV series not found")
    
    series_item = results.items[0]
    subject_id = str(series_item.subjectId)
    detail_path = series_item.detailPath
    
    return {
        "success": True,
        "deprecated": True,
        "message": "Use search then /api/tv/{id}?detail_path={path}",
        "id": subject_id,
        "detail_path": detail_path,
        "url": f"{MEGAN_DOMAIN}/api/tv/{subject_id}?detail_path={detail_path}"
    }

