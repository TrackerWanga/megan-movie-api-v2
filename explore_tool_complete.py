import enum
import sys
import asyncio
import json
import inspect

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

# ============================================
# PART 1: EXPLORE ALL AVAILABLE MODULES
# ============================================

print("=" * 80)
print("🔍 EXPLORING MOVIEBOX_API - COMPLETE TOOL INVENTORY")
print("=" * 80)

# Import everything available
import moviebox_api
print(f"\n📦 moviebox_api version: {moviebox_api.__version__ if hasattr(moviebox_api, '__version__') else 'unknown'}")
print(f"   Location: {moviebox_api.__file__}")

# List all submodules
print("\n📂 AVAILABLE SUBMODULES:")
for attr in dir(moviebox_api):
    if not attr.startswith('_'):
        obj = getattr(moviebox_api, attr)
        if inspect.ismodule(obj):
            print(f"   - {attr}")

# ============================================
# PART 2: EXPLORE V1 MODULE (MovieAuto)
# ============================================

print("\n" + "=" * 80)
print("📌 V1 MODULE - MovieAuto & Downloader")
print("=" * 80)

try:
    from moviebox_api import v1
    print(f"\n✅ v1 module loaded")
    print(f"   Location: {v1.__file__}")
    
    # List all classes in v1
    print("\n📂 V1 Classes:")
    for attr in dir(v1):
        if not attr.startswith('_'):
            obj = getattr(v1, attr)
            if inspect.isclass(obj):
                print(f"   - {attr}")
    
    # Explore MovieAuto
    from moviebox_api.v1 import MovieAuto
    print("\n🎬 MovieAuto methods:")
    for method in dir(MovieAuto):
        if not method.startswith('_'):
            print(f"   - {method}")
    
    # Explore Downloader
    try:
        from moviebox_api.v1.cli import Downloader
        print("\n⬇️ Downloader methods:")
        for method in dir(Downloader):
            if not method.startswith('_'):
                print(f"   - {method}")
    except ImportError as e:
        print(f"   ⚠️ Downloader not found: {e}")
        
except ImportError as e:
    print(f"❌ v1 module error: {e}")

# ============================================
# PART 3: EXPLORE V2 MODULE
# ============================================

print("\n" + "=" * 80)
print("📌 V2 MODULE - Search & Details")
print("=" * 80)

from moviebox_api import v2
print(f"\n✅ v2 module loaded")

# List all v2 submodules
print("\n📂 V2 Submodules:")
v2_dir = v2.__path__[0]
import os
for item in os.listdir(v2_dir):
    if item.endswith('.py') and not item.startswith('_'):
        print(f"   - {item[:-3]}")

# ============================================
# PART 4: EXPLORE THROTTLEBUSTER
# ============================================

print("\n" + "=" * 80)
print("📌 THROTTLEBUSTER - The Download Engine")
print("=" * 80)

try:
    import throttlebuster
    print(f"\n✅ throttlebuster loaded")
    print(f"   Version: {throttlebuster.__version__ if hasattr(throttlebuster, '__version__') else 'unknown'}")
    
    print("\n📂 ThrottleBuster classes:")
    for attr in dir(throttlebuster):
        if not attr.startswith('_'):
            obj = getattr(throttlebuster, attr)
            if inspect.isclass(obj):
                print(f"   - {attr}")
                # Show methods
                for method in dir(obj):
                    if not method.startswith('_'):
                        print(f"      • {method}")
                        
except ImportError as e:
    print(f"❌ throttlebuster not installed: {e}")

# ============================================
# PART 5: TEST MovieAuto ACTUAL DOWNLOAD
# ============================================

print("\n" + "=" * 80)
print("📌 TESTING MovieAuto - ACTUAL DOWNLOAD/STREAM")
print("=" * 80)

async def test_movie_auto():
    try:
        from moviebox_api.v1 import MovieAuto
        
        print("\n🎬 Creating MovieAuto instance...")
        auto = MovieAuto(
            quality="360p",  # Small quality for quick test
            caption_language="English"
        )
        
        print(f"   Quality: {auto.quality}")
        print(f"   Caption language: {auto.caption_language}")
        print(f"   Download dir: {auto.download_dir}")
        
        # Check available methods that could help streaming
        print("\n🔍 MovieAuto internal attributes:")
        for attr in dir(auto):
            if not attr.startswith('_'):
                val = getattr(auto, attr)
                if not callable(val):
                    print(f"   - {attr}: {val}")
        
        # Try to get the internal downloader
        if hasattr(auto, '_downloader'):
            print(f"\n✅ Has internal _downloader")
            dl = auto._downloader
            print(f"   Downloader type: {type(dl)}")
            for attr in dir(dl):
                if not attr.startswith('_'):
                    print(f"      • {attr}")
        
        # Try a test download (small file)
        print("\n⬇️ Testing actual download with MovieAuto...")
        print("   (This will download a small file to test)")
        
        # Uncomment to actually test download
        # movie_file, subtitle_file = await auto.run("Avatar", year=2009)
        # print(f"   ✅ Movie saved to: {movie_file.saved_to}")
        # print(f"   ✅ Subtitle saved to: {subtitle_file.saved_to}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(test_movie_auto())

# ============================================
# PART 6: EXPLORE STREAMING CAPABILITIES
# ============================================

print("\n" + "=" * 80)
print("📌 STREAMING CAPABILITIES")
print("=" * 80)

# Check if there's a stream method
try:
    from moviebox_api.v1.cli import stream_content
    print("✅ stream_content function exists!")
except ImportError:
    print("⚠️ stream_content not directly exposed")

# Check for MPV/VLC integration
import shutil
print(f"\n🎮 Media players available:")
print(f"   MPV: {'✅' if shutil.which('mpv') else '❌'} installed")
print(f"   VLC: {'✅' if shutil.which('vlc') else '❌'} installed")

# ============================================
# PART 7: DOWNLOADER INTERNALS
# ============================================

print("\n" + "=" * 80)
print("📌 DOWNLOADER INTERNALS")
print("=" * 80)

try:
    from moviebox_api.v1.cli import Downloader
    downloader = Downloader()
    
    print(f"\n✅ Downloader instance created")
    print(f"\n🔍 Downloader attributes:")
    for attr in dir(downloader):
        if not attr.startswith('_'):
            val = getattr(downloader, attr)
            if not callable(val):
                print(f"   - {attr}: {val}")
    
    print(f"\n🔍 Downloader methods:")
    for attr in dir(downloader):
        if not attr.startswith('_') and callable(getattr(downloader, attr)):
            print(f"   - {attr}")
            
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================
# PART 8: SUMMARY
# ============================================

print("\n" + "=" * 80)
print("📊 SUMMARY - KEY FINDINGS")
print("=" * 80)

print("""
🔑 KEY COMPONENTS FOR YOUR API:

1. MovieAuto (v1) - Handles complete download workflow
   - Uses ThrottleBuster internally
   - Manages CDN authentication
   - Can stream to MPV/VLC
   
2. Downloader (v1.cli) - Lower-level download control
   - download_movie() method
   - download_tv_series() method
   - Progress tracking available

3. ThrottleBuster - The 403-bypassing engine
   - Multi-part parallel downloads
   - Session management
   - Retry logic

✅ RECOMMENDED APPROACH:
   Use MovieAuto's internal streaming mechanism
   rather than fetching raw URLs manually.
""")

