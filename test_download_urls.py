import httpx
import asyncio
import json

async def get_download_urls(subject_id, title="movie"):
    """Test getting download URLs from PRINCE API"""
    
    print(f"\n{'='*60}")
    print(f"Testing subjectId: {subject_id} ({title})")
    print(f"{'='*60}")
    
    # PRINCE API endpoint
    url = f"https://movieapi.princetechn.com/api/sources/{subject_id}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                
                # Find direct downloads
                direct_downloads = []
                embed_streams = []
                
                for source in data.get("results", []):
                    if source.get("type") == "direct":
                        direct_downloads.append({
                            "provider": source.get("provider"),
                            "quality": source.get("quality"),
                            "size_mb": round(int(source.get("size", 0)) / 1024 / 1024, 2) if source.get("size") else 0,
                            "download_url": source.get("download_url"),
                            "embed_url": source.get("embed_url")
                        })
                    elif source.get("type") == "embed" or "stream_url" in source:
                        embed_streams.append({
                            "provider": source.get("provider"),
                            "quality": source.get("quality", "Auto"),
                            "stream_url": source.get("stream_url") or source.get("embed_url")
                        })
                
                print(f"\n✅ Direct Downloads ({len(direct_downloads)}):")
                for dl in direct_downloads:
                    print(f"   {dl['quality']}: {dl['size_mb']} MB")
                    print(f"   URL: {dl['download_url'][:80]}...")
                
                print(f"\n✅ Embed Streams ({len(embed_streams)}):")
                for es in embed_streams[:3]:
                    print(f"   {es['provider']}: {es['quality']}")
                
                return direct_downloads
            else:
                print(f"❌ Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []

async def main():
    # Test subjectIds from your earlier search results
    test_cases = [
        ("8035128247149024680", "War Machine (2026)"),
        ("8906247916759695608", "Avatar (2009)"),
        ("6391474290696802080", "Inception"),
        ("74738785354956752", "Avatar: Fire and Ash"),
    ]
    
    all_results = {}
    for subject_id, title in test_cases:
        downloads = await get_download_urls(subject_id, title)
        all_results[title] = len(downloads)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for title, count in all_results.items():
        print(f"{title}: {count} direct downloads")

if __name__ == "__main__":
    asyncio.run(main())
