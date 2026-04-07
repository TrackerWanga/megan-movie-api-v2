import enum
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if not hasattr(enum, 'StrEnum'):
    try:
        from strenum import StrEnum
        enum.StrEnum = StrEnum
    except ImportError:
        from enum import Enum
        class StrEnum(str, Enum):
            pass
        enum.StrEnum = StrEnum

# Import routers
from search.router import router as search_router
from movies.router import router as movies_router
from tv.router import router as tv_router
from banners.router import router as banners_router

app = FastAPI(title="Megan Movie API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router)
app.include_router(movies_router)
app.include_router(tv_router)
app.include_router(banners_router)

@app.get("/")
async def root():
    return {
        "api": "Megan Movie API",
        "version": "2.0.0",
        "endpoints": {
            # Search
            "search": "/api/search?q=movie_name&type=all",
            "search_quick": "/api/search/quick?q=movie_name",
            "search_types": "/api/search/types",
            # Movies
            "movie": "/api/movies/{title}?year=2010",
            "movie_downloads": "/api/movies/{title}/downloads",
            # TV Series
            "tv_series": "/api/tv/{title}",
            "tv_episode": "/api/tv/{title}/episode?season=1&episode=1",
            "tv_seasons": "/api/tv/{title}/seasons",
            "tv_search": "/api/tv/search?q=breaking",
            # Banners / Homepage
            "main_banners": "/api/homepage/banners",
            "trending": "/api/homepage/trending",
            "action": "/api/homepage/action",
            "horror": "/api/homepage/horror",
            "romance": "/api/homepage/romance",
            "adventure": "/api/homepage/adventure",
            "anime": "/api/homepage/anime",
            "kdrama": "/api/homepage/kdrama",
            "cdrama": "/api/homepage/cdrama",
            "turkish": "/api/homepage/turkish",
            "sadrama": "/api/homepage/sadrama",
            "blackshows": "/api/homepage/blackshows",
            "premium": "/api/homepage/premium",
            "hot_shorts": "/api/homepage/hot-shorts",
            "learn_english": "/api/homepage/learn-english",
            "nigerian_skit": "/api/homepage/nigerian-skit",
            "movies_in_minutes": "/api/homepage/movies-in-minutes",
            "viral_sports": "/api/homepage/viral-sports",
            "trending_club": "/api/homepage/trending-club",
            "kung_fu": "/api/homepage/kung-fu",
            "kdrama_shorts": "/api/homepage/kdrama-shorts",
            "box_office": "/api/homepage/box-office",
            "fan_favorites": "/api/homepage/fan-favorites",
            "upcoming": "/api/homepage/upcoming",
            # Sports
            "wwe": "/api/sports/wwe",
            "football": "/api/sports/football",
            "boxing": "/api/sports/boxing",
            "live_sports": "/api/sports/live",
            # Music
            "trending_music": "/api/music/trending",
            "top_singers": "/api/music/top-singers",
            # Kids
            "nursery_rhymes": "/api/kids/nursery",
            "animation": "/api/kids/animation",
            # Platforms
            "platforms": "/api/platforms"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Import music router
from music.router import router as music_router

app.include_router(music_router)
