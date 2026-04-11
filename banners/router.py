from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx

from moviebox_api.v2 import Homepage, Session

router = APIRouter(prefix="/api", tags=["banners"])

session = Session()
WORKER_URL = "https://streamapi.megan.qzz.io"

def extract_image(item) -> Optional[Dict]:
    """Extract cover image from item"""
    if hasattr(item, 'cover') and item.cover:
        cover = item.cover
        return {
            "url": str(cover.url) if hasattr(cover, 'url') else None,
            "width": cover.width if hasattr(cover, 'width') else None,
            "height": cover.height if hasattr(cover, 'height') else None,
            "format": cover.format if hasattr(cover, 'format') else None
        }
    return None

def format_subject(subject) -> Dict:
    """Format a subject (movie/TV) for response"""
    genres = []
    if hasattr(subject, 'genre') and subject.genre:
        if isinstance(subject.genre, list):
            genres = subject.genre
        elif isinstance(subject.genre, str):
            genres = [g.strip() for g in subject.genre.split(',')]

    return {
        "id": str(subject.subjectId) if hasattr(subject, 'subjectId') else None,
        "title": subject.title if hasattr(subject, 'title') else None,
        "type": subject.subjectType if hasattr(subject, 'subjectType') else None,
        "year": subject.releaseDate.year if hasattr(subject, 'releaseDate') and subject.releaseDate else None,
        "rating": subject.imdbRatingValue if hasattr(subject, 'imdbRatingValue') else None,
        "genres": genres,
        "poster": extract_image(subject),
        "detail_path": subject.detailPath if hasattr(subject, 'detailPath') else None,
        "subject_id": str(subject.subjectId) if hasattr(subject, 'subjectId') else None
    }

def get_homepage_data():
    """Helper to get homepage data once"""
    homepage = Homepage(session)
    return homepage.get_content_model()

# ============================================
# COMPLETE HOMEPAGE (All Sections)
# ============================================

@router.get("/homepage")
async def get_complete_homepage():
    """Complete homepage - Python + Worker combined"""

    home_data = await get_homepage_data()

    # Get banners from Worker (has working images!)
    banners = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WORKER_URL}/home/banner")
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('featured', []):
                    poster_url = item.get('poster_url')
                    banners.append({
                        "title": item.get('name'),
                        "image": {"url": poster_url} if poster_url else None,
                        "subject_id": item.get('subject_id'),
                        "detail_path": item.get('slug')
                    })
    except Exception as e:
        print(f"Worker banner error: {e}")

    # Get Python trending
    trending = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title in ["Popular Series", "Popular Movie"]:
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            trending.append(format_subject(subject))

    # Get Python sections
    sections = {}
    section_map = {
        "action": "Action Movies",
        "horror": "Horror Movies",
        "romance": "💓Teen Romance 💓",
        "adventure": "Adventure Movies",
        "anime": "Anime[English Dubbed]",
        "kdrama": "K-Drama",
        "cdrama": "C-Drama",
        "turkish": "Turkish Drama",
        "sadrama": "SA Drama",
        "blackshows": "Must-watch Black Shows",
        "premium": "Premium VIP HD Access>>",
        "hotshorts": "🔥Hot Short TV",
        "upcoming": "Upcoming Calendar",
        "smartstart": "🧸 Smart Start Cartoons"
    }

    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type in ["SUBJECTS_MOVIE", "APPOINTMENT_LIST"]:
                title = item.title if hasattr(item, 'title') else None
                for key, target_title in section_map.items():
                    if title == target_title and hasattr(item, 'subjects'):
                        sections[key] = [format_subject(s) for s in item.subjects]
                        break

    # Get platforms
    platforms = []
    if hasattr(home_data, 'platformList'):
        for item in home_data.platformList:
            platforms.append({
                "name": item.name if hasattr(item, 'name') else None,
                "uploaded_by": item.uploadBy if hasattr(item, 'uploadBy') else None
            })

    # Get Worker sections (Hot, Cinema, Ranking)
    worker_data = {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            hot_resp = await client.get(f"{WORKER_URL}/home/hot")
            if hot_resp.status_code == 200:
                worker_data["hot"] = hot_resp.json()

            cinema_resp = await client.get(f"{WORKER_URL}/home/cinema")
            if cinema_resp.status_code == 200:
                worker_data["cinema"] = cinema_resp.json()

            ranking_resp = await client.get(f"{WORKER_URL}/ranking")
            if ranking_resp.status_code == 200:
                worker_data["ranking"] = ranking_resp.json()
    except:
        worker_data = {"hot": [], "cinema": [], "ranking": []}

    return {
        "success": True,
        "api": "Megan Movie API",
        "creator": "Megan / Wanga",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "banners": banners,
            "trending": trending,
            "hot": worker_data.get("hot", []),
            "cinema": worker_data.get("cinema", []),
            "ranking": worker_data.get("ranking", []),
            "sections": sections,
            "platforms": platforms,
            "total": {
                "banners": len(banners),
                "trending": len(trending),
                "sections": len(sections),
                "platforms": len(platforms)
            }
        }
    }

# ============================================
# MAIN BANNERS (Proxied from Worker)
# ============================================

@router.get("/homepage/banners")
async def get_main_banners():
    """Main hero banners - proxied from Worker (has working images!)"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WORKER_URL}/home/banner")
            if resp.status_code != 200:
                return {"success": False, "error": "Worker unavailable", "banners": []}
            
            data = resp.json()
            banners = []
            for item in data.get('featured', []):
                poster_url = item.get('poster_url')
                banners.append({
                    "title": item.get('name'),
                    "image": {"url": poster_url} if poster_url else None,
                    "subject_id": item.get('subject_id'),
                    "detail_path": item.get('slug')
                })
            
            return {"success": True, "total": len(banners), "banners": banners}
    except Exception as e:
        return {"success": False, "error": str(e), "banners": []}

# ============================================
# TRENDING
# ============================================

@router.get("/homepage/trending")
async def get_trending():
    """Trending content (Popular Series + Popular Movie)"""
    home_data = await get_homepage_data()

    trending = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title in ["Popular Series", "Popular Movie"]:
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            trending.append(format_subject(subject))

    return {"success": True, "total": len(trending), "trending": trending}

# ============================================
# WORKER SECTIONS (Hot, Cinema, Ranking)
# ============================================

@router.get("/homepage/hot")
async def get_hot():
    """Hot section from Worker"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WORKER_URL}/home/hot")
            data = resp.json()
            return {"success": True, "source": "worker", **data}
    except Exception as e:
        return {"success": False, "error": str(e), "hot": []}

@router.get("/homepage/cinema")
async def get_cinema():
    """Cinema section from Worker"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WORKER_URL}/home/cinema")
            data = resp.json()
            return {"success": True, "source": "worker", **data}
    except Exception as e:
        return {"success": False, "error": str(e), "cinema": []}

@router.get("/ranking")
async def get_ranking():
    """Ranking lists from Worker"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{WORKER_URL}/ranking")
            data = resp.json()
            return {"success": True, "source": "worker", **data}
    except Exception as e:
        return {"success": False, "error": str(e), "ranking": []}

# ============================================
# MOVIE SECTIONS
# ============================================

@router.get("/homepage/action")
async def get_action_movies():
    """Action Movies"""
    home_data = await get_homepage_data()
    movies = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "Action Movies":
                    if hasattr(item, 'subjects'):
                        movies = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(movies), "movies": movies}

@router.get("/homepage/horror")
async def get_horror_movies():
    """Horror Movies"""
    home_data = await get_homepage_data()
    movies = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "Horror Movies":
                    if hasattr(item, 'subjects'):
                        movies = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(movies), "movies": movies}

@router.get("/homepage/romance")
async def get_romance_movies():
    """Teen Romance Movies"""
    home_data = await get_homepage_data()
    movies = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "💓Teen Romance 💓":
                    if hasattr(item, 'subjects'):
                        movies = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(movies), "movies": movies}

@router.get("/homepage/adventure")
async def get_adventure_movies():
    """Adventure Movies"""
    home_data = await get_homepage_data()
    movies = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "Adventure Movies":
                    if hasattr(item, 'subjects'):
                        movies = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(movies), "movies": movies}

@router.get("/homepage/anime")
async def get_anime():
    """Anime (English Dubbed)"""
    home_data = await get_homepage_data()
    anime = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "Anime[English Dubbed]":
                    if hasattr(item, 'subjects'):
                        anime = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(anime), "anime": anime}

@router.get("/homepage/kdrama")
async def get_kdrama():
    """K-Drama"""
    home_data = await get_homepage_data()
    dramas = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "K-Drama":
                    if hasattr(item, 'subjects'):
                        dramas = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(dramas), "dramas": dramas}

@router.get("/homepage/cdrama")
async def get_cdrama():
    """C-Drama"""
    home_data = await get_homepage_data()
    dramas = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "C-Drama":
                    if hasattr(item, 'subjects'):
                        dramas = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(dramas), "dramas": dramas}

@router.get("/homepage/turkish")
async def get_turkish_drama():
    """Turkish Drama"""
    home_data = await get_homepage_data()
    dramas = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "Turkish Drama":
                    if hasattr(item, 'subjects'):
                        dramas = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(dramas), "dramas": dramas}

@router.get("/homepage/sadrama")
async def get_sa_drama():
    """SA Drama (South African)"""
    home_data = await get_homepage_data()
    dramas = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "SA Drama":
                    if hasattr(item, 'subjects'):
                        dramas = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(dramas), "dramas": dramas}

@router.get("/homepage/blackshows")
async def get_black_shows():
    """Must-watch Black Shows"""
    home_data = await get_homepage_data()
    shows = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "Must-watch Black Shows":
                    if hasattr(item, 'subjects'):
                        shows = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(shows), "shows": shows}

@router.get("/homepage/premium")
async def get_premium_vip():
    """Premium VIP HD Access"""
    home_data = await get_homepage_data()
    premium = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "Premium VIP HD Access>>":
                    if hasattr(item, 'subjects'):
                        premium = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(premium), "premium": premium}

@router.get("/homepage/hot-shorts")
async def get_hot_shorts():
    """Hot Short TV"""
    home_data = await get_homepage_data()
    shorts = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "🔥Hot Short TV":
                    if hasattr(item, 'subjects'):
                        shorts = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(shorts), "shorts": shorts}

@router.get("/homepage/smartstart")
async def get_smart_start():
    """Smart Start Cartoons"""
    home_data = await get_homepage_data()
    cartoons = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SUBJECTS_MOVIE":
                if hasattr(item, 'title') and item.title == "🧸 Smart Start Cartoons":
                    if hasattr(item, 'subjects'):
                        cartoons = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(cartoons), "cartoons": cartoons}

@router.get("/homepage/upcoming")
async def get_upcoming():
    """Upcoming Calendar"""
    home_data = await get_homepage_data()
    upcoming = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "APPOINTMENT_LIST":
                if hasattr(item, 'title') and item.title == "Upcoming Calendar":
                    if hasattr(item, 'subjects'):
                        upcoming = [format_subject(s) for s in item.subjects]
                    break
    return {"success": True, "total": len(upcoming), "upcoming": upcoming}

# ============================================
# PLATFORMS
# ============================================

@router.get("/platforms")
async def get_platforms():
    """Get platform banners (Netflix, PrimeVideo, Disney, etc.)"""
    home_data = await get_homepage_data()

    platforms = []
    if hasattr(home_data, 'platformList'):
        for item in home_data.platformList:
            platforms.append({
                "name": item.name if hasattr(item, 'name') else None,
                "uploaded_by": item.uploadBy if hasattr(item, 'uploadBy') else None
            })

    return {"success": True, "total": len(platforms), "platforms": platforms}
