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

@app.get("/")
async def root():
    return {
        "api": "Megan Movie API",
        "version": "2.0.0",
        "endpoints": {
            "search": "/api/search?q=movie_name&type=all",
            "movie": "/api/movies/{title}?year=2010",
            "movie_downloads": "/api/movies/{title}/downloads",
            "movie_types": "/api/search/types"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
