from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from moviebox_api.v2 import Search, Session
from moviebox_api.v2.download import DownloadableSingleFilesDetail
from moviebox_api.v2.core import SubjectType

router = APIRouter(prefix="/api/education", tags=["education"])

session = Session()

def generate_megan_id(subject_id: str) -> str:
    """Generate Megan ID for education content"""
    return f"megan-edu-{subject_id}"

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

def is_education(item) -> bool:
    """Check if item is education content (subjectType 4 or genre contains education)"""
    if hasattr(item, 'subjectType') and item.subjectType == SubjectType.EDUCATION:
        return True
    if hasattr(item, 'genre') and item.genre:
        genres = item.genre if isinstance(item.genre, list) else [item.genre]
        return any('education' in g.lower() or 'documentary' in g.lower() or 'tutorial' in g.lower() for g in genres)
    return False

def format_education_item(item) -> Dict:
    """Format an education item for response"""
    return {
        "megan_id": generate_megan_id(str(item.subjectId)),
        "title": item.title if hasattr(item, 'title') else None,
        "year": item.releaseDate.year if hasattr(item, 'releaseDate') and item.releaseDate else None,
        "rating": item.imdbRatingValue if hasattr(item, 'imdbRatingValue') else None,
        "genres": item.genre if isinstance(item.genre, list) else [item.genre] if item.genre else [],
        "poster": extract_image(item),
        "detail_path": item.detailPath if hasattr(item, 'detailPath') else None,
        "subject_id": str(item.subjectId) if item.subjectId else None,
        "type": "movie" if item.subjectType == 1 else "tv_series" if item.subjectType == 2 else "education",
        "duration_minutes": (item.duration // 60) if hasattr(item, 'duration') and item.duration else None,
        "has_download": item.hasResource if hasattr(item, 'hasResource') else False
    }

@router.get("/search")
async def search_education(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Results limit")
):
    """Search for educational content, documentaries, tutorials"""
    
    # Search in EDUCATION subject type
    search_edu = Search(session, query=q, subject_type=SubjectType.EDUCATION)
    
    try:
        edu_results = await search_edu.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e), "query": q}
    
    # Also search in MOVIES and filter for educational content
    search_movies = Search(session, query=q, subject_type=SubjectType.MOVIES)
    
    try:
        movie_results = await search_movies.get_content_model()
    except Exception as e:
        movie_results = None
    
    # Collect education items
    edu_items = []
    for item in edu_results.items:
        edu_items.append(format_education_item(item))
    
    # Add filtered movies that are educational
    if movie_results:
        for item in movie_results.items:
            if is_education(item):
                edu_items.append(format_education_item(item))
    
    return {
        "success": True,
        "query": q,
        "total": len(edu_items[:limit]),
        "results": edu_items[:limit]
    }

@router.get("/documentaries")
async def get_documentaries(limit: int = Query(20, ge=1, le=50)):
    """Get documentary content"""
    
    search = Search(session, query="documentary", subject_type=SubjectType.MOVIES)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    documentaries = []
    for item in results.items:
        if 'documentary' in str(item.genre).lower() if item.genre else False:
            documentaries.append(format_education_item(item))
    
    return {
        "success": True,
        "total": len(documentaries[:limit]),
        "documentaries": documentaries[:limit]
    }

@router.get("/tutorials")
async def get_tutorials(limit: int = Query(20, ge=1, le=50)):
    """Get tutorial content"""
    
    search = Search(session, query="tutorial", subject_type=SubjectType.EDUCATION)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    tutorials = []
    for item in results.items:
        tutorials.append(format_education_item(item))
    
    # Also search in MOVIES
    search_movies = Search(session, query="tutorial", subject_type=SubjectType.MOVIES)
    
    try:
        movie_results = await search_movies.get_content_model()
        for item in movie_results.items:
            if 'tutorial' in str(item.genre).lower() if item.genre else False:
                tutorials.append(format_education_item(item))
    except:
        pass
    
    # Remove duplicates by detail_path
    seen = set()
    unique_tutorials = []
    for t in tutorials:
        if t['detail_path'] not in seen:
            seen.add(t['detail_path'])
            unique_tutorials.append(t)
    
    return {
        "success": True,
        "total": len(unique_tutorials[:limit]),
        "tutorials": unique_tutorials[:limit]
    }

@router.get("/popular")
async def get_popular_education(limit: int = Query(20, ge=1, le=50)):
    """Get popular educational content"""
    
    search = Search(session, query="popular", subject_type=SubjectType.EDUCATION)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    items = []
    for item in results.items:
        items.append(format_education_item(item))
    
    return {
        "success": True,
        "total": len(items[:limit]),
        "popular": items[:limit]
    }

@router.get("/latest")
async def get_latest_education(limit: int = Query(20, ge=1, le=50)):
    """Get latest educational content"""
    
    search = Search(session, query="latest", subject_type=SubjectType.EDUCATION)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    items = []
    for item in results.items:
        items.append(format_education_item(item))
    
    return {
        "success": True,
        "total": len(items[:limit]),
        "latest": items[:limit]
    }

@router.get("/trending")
async def get_trending_education(limit: int = Query(20, ge=1, le=50)):
    """Get trending educational content"""
    
    search = Search(session, query="trending", subject_type=SubjectType.EDUCATION)
    
    try:
        results = await search.get_content_model()
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    items = []
    for item in results.items:
        items.append(format_education_item(item))
    
    return {
        "success": True,
        "total": len(items[:limit]),
        "trending": items[:limit]
    }

@router.get("/{detail_path}")
async def get_education_details(detail_path: str):
    """Get complete education content details including download"""
    
    # Search for the education content
    search_edu = Search(session, query=detail_path, subject_type=SubjectType.EDUCATION)
    results = await search_edu.get_content_model()
    
    edu_item = None
    for item in results.items:
        if item.detailPath == detail_path:
            edu_item = item
            break
    
    # If not found in EDUCATION, search in MOVIES
    if not edu_item:
        search_movies = Search(session, query=detail_path, subject_type=SubjectType.MOVIES)
        movie_results = await search_movies.get_content_model()
        for item in movie_results.items:
            if item.detailPath == detail_path and is_education(item):
                edu_item = item
                break
    
    if not edu_item:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Get full details
    from moviebox_api.v2 import MovieDetails
    details_obj = MovieDetails(session)
    detail_data = await details_obj.get_content(edu_item.detailPath)
    
    # Extract subject info
    subject = detail_data.get('subject', {})
    
    # Extract cast/creators
    cast = []
    stars = detail_data.get('stars', [])
    for star in stars[:10]:
        cast.append({
            "name": star.get('name'),
            "role": star.get('character'),
            "avatar": star.get('avatarUrl')
        })
    
    # Extract poster
    poster = extract_image(edu_item)
    
    # Extract trailer if available
    trailer = None
    trailer_data = subject.get('trailer', {})
    video_addr = trailer_data.get('videoAddress', {})
    if video_addr:
        trailer = video_addr.get('url')
    
    # Get download URL
    download_url = None
    download_quality = None
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, edu_item)
        download_data = await downloads_obj.get_content()
        if download_data and 'downloads' in download_data and download_data['downloads']:
            best = download_data['downloads'][0]
            download_url = best.get('url')
            download_quality = f"{best.get('resolution')}p"
    except Exception as e:
        print(f"Download error: {e}")
    
    response = {
        "success": True,
        "api": "Megan Movie API",
        "data": {
            "education": {
                "megan_id": generate_megan_id(str(edu_item.subjectId)),
                "title": edu_item.title,
                "year": edu_item.releaseDate.year if edu_item.releaseDate else None,
                "rating": edu_item.imdbRatingValue,
                "genres": edu_item.genre if isinstance(edu_item.genre, list) else [edu_item.genre] if edu_item.genre else [],
                "poster": poster,
                "description": subject.get('description', ''),
                "trailer": trailer,
                "duration_minutes": (edu_item.duration // 60) if edu_item.duration else None,
                "cast": cast,
                "detail_path": edu_item.detailPath,
                "download": {
                    "available": download_url is not None,
                    "quality": download_quality,
                    "url": download_url
                }
            }
        }
    }
    
    return response

@router.get("/download/{detail_path}")
async def get_education_download(detail_path: str):
    """Get download URL for educational content"""
    
    # Search for the content
    search_edu = Search(session, query=detail_path, subject_type=SubjectType.EDUCATION)
    results = await search_edu.get_content_model()
    
    edu_item = None
    for item in results.items:
        if item.detailPath == detail_path:
            edu_item = item
            break
    
    if not edu_item:
        search_movies = Search(session, query=detail_path, subject_type=SubjectType.MOVIES)
        movie_results = await search_movies.get_content_model()
        for item in movie_results.items:
            if item.detailPath == detail_path and is_education(item):
                edu_item = item
                break
    
    if not edu_item:
        raise HTTPException(status_code=404, detail="Content not found")
    
    try:
        downloads_obj = DownloadableSingleFilesDetail(session, edu_item)
        download_data = await downloads_obj.get_content()
        
        if download_data and 'downloads' in download_data:
            return {
                "success": True,
                "megan_id": generate_megan_id(str(edu_item.subjectId)),
                "title": edu_item.title,
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
        return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "No download available"}
