# Add this to movies/router.py - Replace the existing download endpoint

# ============================================
# PRINCE-POWERED DOWNLOADS (HIDDEN)
# ============================================

import httpx
from urllib.parse import quote

PRINCE_API = "https://movieapi.princetechn.com"
MEGAN_DOMAIN = "https://movieapi.megan.qzz.io"

@router.get("/{title}/downloads")
async def get_movie_downloads(title: str, year: Optional[int] = None):
    """Get download URLs (powered by Megan CDN - worldwide working)"""
    
    # First, get the subjectId from moviebox_api
    search_obj = Search(session, query=title, subject_type=SubjectType.MOVIES)
    results = await search_obj.get_content_model()
    
    if not results.items:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Find the right movie
    movie_item = results.items[0]
    if year and movie_item.releaseDate and movie_item.releaseDate.year != year:
        for item in results.items:
            if item.releaseDate and item.releaseDate.year == year:
                movie_item = item
                break
    
    subject_id = movie_item.subjectId
    
    # Call PRINCE API (hidden from user)
    async with httpx.AsyncClient(timeout=30.0) as client:
        prince_response = await client.get(f"{PRINCE_API}/api/sources/{subject_id}")
        prince_data = prince_response.json()
    
    # Transform and proxy URLs through YOUR domain
    downloads = []
    for source in prince_data.get("results", []):
        if source.get("type") == "direct" and "MovieBox" in source.get("provider", ""):
            original_url = source.get("download_url") or source.get("embed_url")
            
            # Create proxied URL through your domain
            proxied_url = f"{MEGAN_DOMAIN}/api/proxy/dl?url={quote(original_url, safe='')}&title={quote(movie_item.title)}&quality={source.get('quality')}"
            
            downloads.append({
                "quality": source.get("quality"),
                "size_mb": round(int(source.get("size", 0)) / 1024 / 1024, 2) if source.get("size") else 0,
                "url": proxied_url,
                "provider": "Megan CDN"  # Hide PRINCE completely
            })
    
    return {
        "success": True,
        "title": movie_item.title,
        "year": movie_item.releaseDate.year if movie_item.releaseDate else None,
        "downloads": downloads,
        "note": "Direct MP4 links - right click to save"
    }
