import httpx
import asyncio
import json
from urllib.parse import unquote

async def show_full_urls(subject_id, title):
    print(f"\n{'='*80}")
    print(f"📀 {title}")
    print(f"SubjectId: {subject_id}")
    print(f"{'='*80}")
    
    url = f"https://movieapi.princetechn.com/api/sources/{subject_id}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            
            for source in data.get("results", []):
                if source.get("type") == "direct":
                    print(f"\n🎬 QUALITY: {source.get('quality')}")
                    print(f"   Size: {round(int(source.get('size', 0)) / 1024 / 1024, 2)} MB")
                    print(f"   Download URL: {source.get('download_url')}")
                    print(f"   Embed URL: {source.get('embed_url')}")
                    print()

async def main():
    test_cases = [
        ("8035128247149024680", "War Machine (2026)"),
        ("8906247916759695608", "Avatar (2009)"),
        ("74738785354956752", "Avatar: Fire and Ash"),
    ]
    
    for subject_id, title in test_cases:
        await show_full_urls(subject_id, title)

if __name__ == "__main__":
    asyncio.run(main())
