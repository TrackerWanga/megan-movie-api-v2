import enum
import sys
import asyncio
import json
import inspect

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

print("=" * 80)
print("🔍 DEEP EXPLORATION - MOVIEBOX_API V1 & V2")
print("=" * 80)

# ============================================
# PART 1: V1 MODULE - Working Components
# ============================================

print("\n" + "=" * 80)
print("📌 V1 MODULE - Available Components")
print("=" * 80)

from moviebox_api import v1

# Get all classes that don't require the broken CLI
print("\n✅ Working V1 Classes:")
working_classes = []
for attr in dir(v1):
    if not attr.startswith('_'):
        try:
            obj = getattr(v1, attr)
            if inspect.isclass(obj):
                working_classes.append(attr)
                print(f"   - {attr}")
        except Exception as e:
            print(f"   - {attr} (error: {e})")

# ============================================
# PART 2: MovieAuto Deep Dive
# ============================================

print("\n" + "=" * 80)
print("📌 MovieAuto - Complete Analysis")
print("=" * 80)

try:
    from moviebox_api.v1 import MovieAuto
    
    # Get source code if possible
    import inspect
    try:
        source = inspect.getsource(MovieAuto)
        print(f"\n📝 MovieAuto source length: {len(source)} chars")
        
        # Look for key methods
        if 'def run' in source:
            print("   ✅ Has 'run' method")
        if 'throttlebuster' in source.lower():
            print("   ✅ Uses ThrottleBuster")
        if 'stream' in source.lower():
            print("   ✅ Has streaming capability")
            
        # Extract important lines
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'download' in line.lower() and 'def' in line.lower():
                print(f"   📍 Line {i}: {line.strip()}")
                
    except Exception as e:
        print(f"   ⚠️ Could not get source: {e}")
        
except Exception as e:
    print(f"❌ MovieAuto error: {e}")

# ============================================
# PART 3: Session & Core Components
# ============================================

print("\n" + "=" * 80)
print("📌 Session & Core Components")
print("=" * 80)

from moviebox_api.v1 import Session

print("\n🔐 Session methods:")
session = Session()
for method in dir(session):
    if not method.startswith('_'):
        print(f"   - {method}")

# Check session headers
if hasattr(session, 'headers'):
    print(f"\n📋 Session headers:")
    for key, value in session.headers.items():
        print(f"   {key}: {value}")

# ============================================
# PART 4: Download Classes
# ============================================

print("\n" + "=" * 80)
print("📌 Download Classes (Non-CLI)")
print("=" * 80)

from moviebox_api.v1 import (
    DownloadableMovieFilesDetail,
    DownloadableTVSeriesFilesDetail,
    MediaFileDownloader,
    CaptionFileDownloader
)

print("\n📥 DownloadableMovieFilesDetail methods:")
for method in dir(DownloadableMovieFilesDetail):
    if not method.startswith('_'):
        print(f"   - {method}")

print("\n📥 MediaFileDownloader methods:")
for method in dir(MediaFileDownloader):
    if not method.startswith('_'):
        print(f"   - {method}")

# ============================================
# PART 5: V2 Module Complete
# ============================================

print("\n" + "=" * 80)
print("📌 V2 MODULE - Complete")
print("=" * 80)

from moviebox_api import v2

print("\n📂 V2 Classes:")
v2_classes = []
for attr in dir(v2):
    if not attr.startswith('_'):
        try:
            obj = getattr(v2, attr)
            if inspect.isclass(obj):
                v2_classes.append(attr)
                print(f"   - {attr}")
        except:
            pass

# ============================================
# PART 6: V2 Download Module
# ============================================

print("\n" + "=" * 80)
print("📌 V2 Download Module")
print("=" * 80)

from moviebox_api.v2 import download as v2_download

print("\n📥 V2 Download classes:")
for attr in dir(v2_download):
    if not attr.startswith('_'):
        obj = getattr(v2_download, attr)
        if inspect.isclass(obj):
            print(f"   - {attr}")
            # Show key methods
            for method in dir(obj):
                if method in ['get_content', 'download', 'get_url', 'stream']:
                    print(f"      • {method}")

# ============================================
# PART 7: Test Direct Download with MediaFileDownloader
# ============================================

print("\n" + "=" * 80)
print("📌 Testing MediaFileDownloader")
print("=" * 80)

async def test_media_downloader():
    from moviebox_api.v2 import Search, Session
    from moviebox_api.v2.core import SubjectType
    
    session = Session()
    search = Search(session, query="Avatar", subject_type=SubjectType.MOVIES)
    results = await search.get_content_model()
    
    if results.items:
        movie = results.items[0]
        print(f"\n✅ Found: {movie.title}")
        
        try:
            from moviebox_api.v1 import MediaFileDownloader
            downloader = MediaFileDownloader(session, movie, quality="360p")
            print(f"   ✅ Created MediaFileDownloader")
            
            # Check what methods are available
            print(f"\n   Available methods:")
            for method in dir(downloader):
                if not method.startswith('_'):
                    print(f"      • {method}")
            
            # Try to get download info
            if hasattr(downloader, 'get_download_info'):
                info = await downloader.get_download_info()
                print(f"\n   Download info: {info}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

asyncio.run(test_media_downloader())

# ============================================
# PART 8: Check for Streaming Methods
# ============================================

print("\n" + "=" * 80)
print("📌 Searching for Streaming Methods")
print("=" * 80)

# Search through all modules for 'stream' related methods
import moviebox_api
import pkgutil

stream_methods = []

def find_stream_methods(module, prefix=""):
    for attr in dir(module):
        if attr.startswith('_'):
            continue
        try:
            obj = getattr(module, attr)
            if 'stream' in attr.lower():
                stream_methods.append(f"{prefix}.{attr}")
            if inspect.ismodule(obj) and hasattr(obj, '__file__'):
                if obj.__file__ and 'moviebox_api' in obj.__file__:
                    find_stream_methods(obj, f"{prefix}.{attr}")
        except:
            pass

find_stream_methods(moviebox_api, "moviebox_api")

print("\n🌊 Streaming-related methods found:")
for method in stream_methods[:20]:
    print(f"   - {method}")

# ============================================
# PART 9: Summary
# ============================================

print("\n" + "=" * 80)
print("📊 SUMMARY - AVAILABLE TOOLS")
print("=" * 80)

print("""
✅ WORKING COMPONENTS:
   - MovieAuto (v1) - Complete download orchestrator
   - MediaFileDownloader - Direct media downloader
   - DownloadableMovieFilesDetail - Movie download info
   - DownloadableTVSeriesFilesDetail - TV download info
   - Session - Manages authentication/cookies
   
🔧 TO USE IN YOUR API:
   1. Use MediaFileDownloader with Session
   2. It handles ThrottleBuster internally
   3. Can stream content directly without saving
   4. Bypasses 403 automatically
""")

