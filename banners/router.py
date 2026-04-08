from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import datetime

from moviebox_api.v2 import Homepage, Session

router = APIRouter(prefix="/api", tags=["banners"])

session = Session()

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
    # Handle genre - it could be list or string
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
        "detail_path": subject.detailPath if hasattr(subject, 'detailPath') else None
    }

def get_homepage_data():
    """Helper to get homepage data once"""
    homepage = Homepage(session)
    return homepage.get_content_model()

# ============================================
# MAIN BANNERS
# ============================================

@router.get("/homepage/banners")
async def get_main_banners():
    """Main hero banners (Banner_Africa)"""
    home_data = await get_homepage_data()
    
    banners = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "BANNER":
                if hasattr(item, 'banner') and item.banner and hasattr(item.banner, 'items'):
                    for banner_item in item.banner.items:
                        banners.append({
                            "title": banner_item.title if hasattr(banner_item, 'title') else None,
                            "image": extract_image(banner_item) if hasattr(banner_item, 'image') else None,
                            "subject_id": str(banner_item.subjectId) if hasattr(banner_item, 'subjectId') else None,
                            "detail_path": banner_item.detailPath if hasattr(banner_item, 'detailPath') else None
                        })
    
    return {"success": True, "total": len(banners), "banners": banners}

# ============================================
# HOMEPAGE SECTIONS
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
                        for subject in item.subjects:
                            movies.append(format_subject(subject))
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
                        for subject in item.subjects:
                            movies.append(format_subject(subject))
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
                        for subject in item.subjects:
                            movies.append(format_subject(subject))
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
                        for subject in item.subjects:
                            movies.append(format_subject(subject))
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
                        for subject in item.subjects:
                            anime.append(format_subject(subject))
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
                        for subject in item.subjects:
                            dramas.append(format_subject(subject))
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
                        for subject in item.subjects:
                            dramas.append(format_subject(subject))
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
                        for subject in item.subjects:
                            dramas.append(format_subject(subject))
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
                        for subject in item.subjects:
                            dramas.append(format_subject(subject))
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
                        for subject in item.subjects:
                            shows.append(format_subject(subject))
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
                        for subject in item.subjects:
                            premium.append(format_subject(subject))
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
                        for subject in item.subjects:
                            shorts.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(shorts), "shorts": shorts}

@router.get("/homepage/learn-english")
async def get_learn_english():
    """Learn English with Movies"""
    home_data = await get_homepage_data()
    
    content = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "✨ Learn English with Movies":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            content.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(content), "content": content}

@router.get("/homepage/nigerian-skit")
async def get_nigerian_skit():
    """Nigerian Skit"""
    home_data = await get_homepage_data()
    
    skits = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Nigerian Skit":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            skits.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(skits), "skits": skits}

@router.get("/homepage/movies-in-minutes")
async def get_movies_in_minutes():
    """Movies in Minutes (short recaps)"""
    home_data = await get_homepage_data()
    
    recaps = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Movies in Minutes":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            recaps.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(recaps), "recaps": recaps}

@router.get("/homepage/viral-sports")
async def get_viral_sports():
    """Viral Sports Shorts"""
    home_data = await get_homepage_data()
    
    sports = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Viral Sports Shorts":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            sports.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(sports), "sports": sports}

@router.get("/homepage/trending-club")
async def get_trending_club():
    """Trending Club & Competition Picks"""
    home_data = await get_homepage_data()
    
    picks = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Trending Club & Competition Picks":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            picks.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(picks), "picks": picks}

@router.get("/homepage/kung-fu")
async def get_kung_fu():
    """Secrets of Asian Kung Fu"""
    home_data = await get_homepage_data()
    
    martial = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Secrets of Asian Kung Fu":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            martial.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(martial), "martial_arts": martial}

@router.get("/homepage/kdrama-shorts")
async def get_kdrama_shorts():
    """K-Drama Shorts"""
    home_data = await get_homepage_data()
    
    shorts = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "K-Drama Shorts":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            shorts.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(shorts), "shorts": shorts}

@router.get("/homepage/box-office")
async def get_box_office():
    """Global BoxOffice"""
    home_data = await get_homepage_data()
    
    movies = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Global BoxOffice":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            movies.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(movies), "movies": movies}

@router.get("/homepage/fan-favorites")
async def get_fan_favorites():
    """Fan Favorites"""
    home_data = await get_homepage_data()
    
    favorites = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Fan Favorites":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            favorites.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(favorites), "favorites": favorites}

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
                        for subject in item.subjects:
                            upcoming.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(upcoming), "upcoming": upcoming}

# ============================================
# SPORTS CATEGORIES
# ============================================

@router.get("/sports/wwe")
async def get_wwe():
    """WWE content"""
    home_data = await get_homepage_data()
    
    wwe = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title in ["🤼The Best of WWE", "WWE Best of Live Replays"]:
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            wwe.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(wwe), "wwe": wwe}

@router.get("/sports/football")
async def get_football():
    """Football highlights"""
    home_data = await get_homepage_data()
    
    football = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Football Highlights":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            football.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(football), "football": football}

@router.get("/sports/boxing")
async def get_boxing():
    """Fight Zone / Boxing content"""
    home_data = await get_homepage_data()
    
    boxing = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title in ["🔥Fight Zone Shorts", "FightZone Channel Top Picks 👇"]:
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            boxing.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(boxing), "boxing": boxing}

@router.get("/sports/live")
async def get_live_sports():
    """Live sports"""
    home_data = await get_homepage_data()
    
    live = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "SPORT_LIVE":
                if hasattr(item, 'title') and item.title == "Live":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            live.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(live), "live": live}

# ============================================
# MUSIC CATEGORIES
# ============================================

@router.get("/music/trending")
async def get_trending_music():
    """Trending Music Videos in Kenya"""
    home_data = await get_homepage_data()
    
    music = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Trending Music Videos in Kenya":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            music.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(music), "music": music}

@router.get("/music/top-singers")
async def get_top_singers():
    """Top Singers Mix"""
    home_data = await get_homepage_data()
    
    music = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Top Singers Mix":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            music.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(music), "music": music}

# ============================================
# KIDS CATEGORIES
# ============================================

@router.get("/kids/nursery")
async def get_nursery_rhymes():
    """Nursery Rhymes Playlist"""
    home_data = await get_homepage_data()
    
    nursery = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Nursery Rhymes Playlist":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            nursery.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(nursery), "nursery": nursery}

@router.get("/kids/animation")
async def get_animation():
    """Animation Collection"""
    home_data = await get_homepage_data()
    
    animation = []
    if hasattr(home_data, 'operatingList'):
        for item in home_data.operatingList:
            if hasattr(item, 'type') and item.type == "CUSTOM":
                if hasattr(item, 'title') and item.title == "Animation Collection":
                    if hasattr(item, 'subjects'):
                        for subject in item.subjects:
                            animation.append(format_subject(subject))
                    break
    
    return {"success": True, "total": len(animation), "animation": animation}

# ============================================
# PLATFORM BANNERS
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
