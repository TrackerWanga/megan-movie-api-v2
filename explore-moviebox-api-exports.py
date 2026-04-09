import enum
import sys
import asyncio
import json
import inspect
from types import ModuleType
from typing import get_type_hints

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

# Import all main modules
print("=" * 80)
print("🔍 MOVIEBOX-API V2 - COMPLETE EXPORT EXPLORER")
print("=" * 80)

# Track all exports
all_exports = {
    "classes": [],
    "functions": [],
    "modules": [],
    "constants": [],
    "exceptions": [],
    "models": []
}

# Helper to inspect module
def inspect_module(module, name):
    print(f"\n📦 MODULE: {name}")
    print("-" * 50)
    
    if not module:
        print(f"   ❌ Module not found")
        return
    
    members = inspect.getmembers(module)
    
    for member_name, member in members:
        if member_name.startswith('_'):
            continue
            
        try:
            if inspect.isclass(member):
                all_exports["classes"].append(f"{name}.{member_name}")
                print(f"   🏗️  CLASS: {member_name}")
                
                # Show methods
                methods = [m for m in dir(member) if not m.startswith('_')]
                if methods:
                    print(f"       Methods: {', '.join(methods[:5])}{'...' if len(methods) > 5 else ''}")
                
                # Show if it's a Pydantic model
                if hasattr(member, '__fields__'):
                    print(f"       📋 Pydantic Model with fields: {list(member.__fields__.keys())[:3]}...")
                elif hasattr(member, 'model_fields'):
                    print(f"       📋 Pydantic Model with fields: {list(member.model_fields.keys())[:3]}...")
                    
            elif inspect.isfunction(member) or inspect.isroutine(member):
                all_exports["functions"].append(f"{name}.{member_name}")
                print(f"   ⚙️  FUNCTION: {member_name}{inspect.signature(member)}")
                
            elif inspect.ismodule(member):
                all_exports["modules"].append(f"{name}.{member_name}")
                print(f"   📁 SUBMODULE: {member_name}")
                
            elif isinstance(member, Exception):
                all_exports["exceptions"].append(f"{name}.{member_name}")
                print(f"   💥 EXCEPTION: {member_name}")
                
            else:
                all_exports["constants"].append(f"{name}.{member_name}")
                value_str = str(member)[:50]
                print(f"   🔧 CONSTANT: {member_name} = {value_str}")
                
        except Exception as e:
            print(f"   ⚠️  ERROR inspecting {member_name}: {e}")

# 1. Main package exports
print("\n\n🔥 MAIN PACKAGE: moviebox_api")
print("=" * 80)

try:
    import moviebox_api
    inspect_module(moviebox_api, "moviebox_api")
    
    # Check __all__ if defined
    if hasattr(moviebox_api, '__all__'):
        print(f"\n   📋 __all__ exports: {moviebox_api.__all__}")
except ImportError as e:
    print(f"   ❌ Cannot import moviebox_api: {e}")

# 2. V2 module exports
print("\n\n🔥 SUBMODULE: moviebox_api.v2")
print("=" * 80)

try:
    from moviebox_api import v2
    inspect_module(v2, "moviebox_api.v2")
except ImportError as e:
    print(f"   ❌ Cannot import v2: {e}")

# 3. Core module exports
print("\n\n🔥 SUBMODULE: moviebox_api.v2.core")
print("=" * 80)

try:
    from moviebox_api.v2 import core
    inspect_module(core, "moviebox_api.v2.core")
except ImportError as e:
    print(f"   ❌ Cannot import core: {e}")

# 4. Download module exports
print("\n\n🔥 SUBMODULE: moviebox_api.v2.download")
print("=" * 80)

try:
    from moviebox_api.v2 import download
    inspect_module(download, "moviebox_api.v2.download")
except ImportError as e:
    print(f"   ❌ Cannot import download: {e}")

# 5. Search module exports
print("\n\n🔥 SUBMODULE: moviebox_api.v2.search")
print("=" * 80)

try:
    from moviebox_api.v2 import search as search_mod
    inspect_module(search_mod, "moviebox_api.v2.search")
except ImportError as e:
    print(f"   ❌ Cannot import search: {e}")

# 6. Session module
print("\n\n🔥 SUBMODULE: moviebox_api.v2.session")
print("=" * 80)

try:
    from moviebox_api.v2 import session as session_mod
    inspect_module(session_mod, "moviebox_api.v2.session")
except ImportError as e:
    print(f"   ❌ Cannot import session: {e}")

# 7. CLI module (if available)
print("\n\n🔥 SUBMODULE: moviebox_api.cli")
print("=" * 80)

try:
    from moviebox_api import cli
    inspect_module(cli, "moviebox_api.cli")
except ImportError as e:
    print(f"   ❌ CLI not available: {e}")

# 8. Auto-download module
print("\n\n🔥 SUBMODULE: moviebox_api.auto")
print("=" * 80)

try:
    from moviebox_api import auto
    inspect_module(auto, "moviebox_api.auto")
except ImportError as e:
    print(f"   ❌ Auto module not available: {e}")

# Summary
print("\n\n" + "=" * 80)
print("📊 COMPLETE EXPORT SUMMARY")
print("=" * 80)

for category, items in all_exports.items():
    if items:
        print(f"\n{category.upper()} ({len(items)} total):")
        for item in sorted(items)[:20]:  # Show first 20
            print(f"   • {item}")
        if len(items) > 20:
            print(f"   ... and {len(items) - 20} more")

# Functional test like your original
print("\n\n" + "=" * 80)
print("🧪 FUNCTIONAL TEST - ACTUAL USAGE")
print("=" * 80)

async def test_exports():
    try:
        from moviebox_api.v2 import Search, Session, MovieDetails
        from moviebox_api.v2.download import DownloadableSingleFilesDetail
        from moviebox_api.v2.core import Homepage
        
        print("\n✅ Core imports successful!")
        
        # Test instantiation
        session = Session()
        print(f"✅ Session created: {type(session).__name__}")
        
        # Test Search
        search = Search(session, query="test")
        print(f"✅ Search created: {type(search).__name__}")
        
        # Test Homepage
        homepage = Homepage(session)
        print(f"✅ Homepage created: {type(homepage).__name__}")
        
        # Test MovieDetails
        details = MovieDetails(session)
        print(f"✅ MovieDetails created: {type(details).__name__}")
        
        # Test Download
        # Need a search result first
        print("\n📋 Available methods on Search:")
        for method in [m for m in dir(search) if not m.startswith('_')]:
            print(f"   • {method}")
            
    except Exception as e:
        print(f"❌ Error during functional test: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_exports())

print("\n" + "=" * 80)
print("✅ EXPORT EXPLORATION COMPLETE")
print("=" * 80)
