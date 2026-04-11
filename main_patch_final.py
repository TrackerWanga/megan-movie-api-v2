# Replace the /api/dl endpoint in main.py with this working version

@app.get("/api/dl")
async def proxy_download(url: str, title: str = "video", quality: str = "1080p"):
    """Proxy download a video URL - with working CDN headers"""
    from urllib.parse import unquote
    import httpx
    from fastapi.responses import StreamingResponse
    
    decoded_url = unquote(url)
    print(f"⬇️ Downloading: {title} ({quality})")
    print(f"   URL: {decoded_url[:100]}...")
    
    try:
        # Get the token cookie from the MovieBox session
        cookie = None
        try:
            from movies.router import session as movie_session
            if hasattr(movie_session, '_client'):
                client = movie_session._client
                if hasattr(client, 'cookies'):
                    for c in client.cookies.jar:
                        if c.name == 'token':
                            cookie = c.value
                            break
        except Exception as e:
            print(f"   ⚠️ Could not get cookie: {e}")
        
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            headers = {
                "Origin": "https://videodownloader.site/",
                "Referer": "https://videodownloader.site/",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
            
            if cookie:
                headers["Cookie"] = f"token={cookie}"
                print(f"   ✅ Using cookie: token={cookie[:50]}...")
            else:
                print(f"   ⚠️ No cookie available - CDN may reject")
            
            response = await client.get(decoded_url, headers=headers)
            
            if response.status_code != 200:
                print(f"   ❌ CDN returned {response.status_code}")
                return {"error": f"CDN returned {response.status_code}", "success": False}
            
            print(f"   ✅ CDN responded with {response.status_code}")
            filename = f"{title.replace(' ', '_')}_{quality}.mp4"
            
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=200,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*",
                    "Content-Length": response.headers.get("content-length", ""),
                }
            )
    except Exception as e:
        print(f"   ❌ Download error: {e}")
        return {"error": str(e), "success": False}


@app.get("/api/stream")
async def proxy_stream(url: str):
    """Proxy stream a video URL - with working CDN headers"""
    from urllib.parse import unquote
    import httpx
    from fastapi.responses import StreamingResponse
    
    decoded_url = unquote(url)
    print(f"📺 Streaming: {decoded_url[:100]}...")
    
    try:
        cookie = None
        try:
            from movies.router import session as movie_session
            if hasattr(movie_session, '_client'):
                client = movie_session._client
                if hasattr(client, 'cookies'):
                    for c in client.cookies.jar:
                        if c.name == 'token':
                            cookie = c.value
                            break
        except:
            pass
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            headers = {
                "Origin": "https://videodownloader.site/",
                "Referer": "https://videodownloader.site/",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
                "Accept": "*/*",
            }
            
            if cookie:
                headers["Cookie"] = f"token={cookie}"
            
            response = await client.get(decoded_url, headers=headers)
            
            return StreamingResponse(
                response.aiter_bytes(),
                status_code=response.status_code,
                headers={
                    "Content-Type": "video/mp4",
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except Exception as e:
        return {"error": str(e), "success": False}
