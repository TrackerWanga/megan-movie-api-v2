import enum
import sys
import asyncio
import json
import traceback

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session, MovieDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail, DownloadableTVSeriesFilesDetail
from moviebox_api.v2.core import TVSeriesDetails

async def raw_test():
    print("=" * 80)
    print("RAW OUTPUT - EVERYTHING UNFILTERED")
    print("=" * 80)
    
    session = Session()
    
    # =========================================================
    # TEST 1: SEARCH FOR INCEPTION (MOVIE)
    # =========================================================
    print("\n\n" + "=" * 80)
    print("TEST 1: SEARCH FOR 'inception'")
    print("=" * 80)
    
    search = Search(session, query="inception")
    results = await search.get_content_model()
    
    print("\n--- RAW SEARCH RESULTS OBJECT ---")
    print(f"Type: {type(results)}")
    print(f"Dir: {[a for a in dir(results) if not a.startswith('_')]}")
    
    print("\n--- FIRST RESULT RAW ---")
    if results.items:
        first = results.items[0]
        print(f"Type: {type(first)}")
        print(f"All attributes: {[a for a in dir(first) if not a.startswith('_')]}")
        print(f"\nSubjectId: {first.subjectId}")
        print(f"Title: {first.title}")
        print(f"DetailPath: {first.detailPath}")
        print(f"SubjectType: {first.subjectType}")
        print(f"ReleaseDate: {first.releaseDate}")
        print(f"ImdbRating: {first.imdbRatingValue}")
        print(f"Genre: {first.genre}")
        print(f"Cover: {first.cover}")
        
        # =========================================================
        # TEST 2: MOVIE DETAILS
        # =========================================================
        print("\n\n" + "=" * 80)
        print(f"TEST 2: MOVIE DETAILS for '{first.title}'")
        print("=" * 80)
        
        try:
            details_obj = MovieDetails(session)
            print(f"\nDetails object type: {type(details_obj)}")
            print(f"Details object methods: {[a for a in dir(details_obj) if not a.startswith('_')]}")
            
            detail_data = await details_obj.get_content(first.detailPath)
            print(f"\nRAW DETAIL DATA TYPE: {type(detail_data)}")
            print(f"\nRAW DETAIL DATA KEYS: {detail_data.keys() if hasattr(detail_data, 'keys') else 'N/A'}")
            
            # Print entire detail_data as JSON
            print("\n--- FULL DETAIL DATA (JSON) ---")
            print(json.dumps(detail_data, indent=2, default=str)[:3000])
            
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()
        
        # =========================================================
        # TEST 3: DOWNLOAD URLS
        # =========================================================
        print("\n\n" + "=" * 80)
        print(f"TEST 3: DOWNLOAD URLS for '{first.title}'")
        print("=" * 80)
        
        try:
            downloads_obj = DownloadableSingleFilesDetail(session, first)
            print(f"\nDownloads object type: {type(downloads_obj)}")
            
            download_data = await downloads_obj.get_content()
            print(f"\nRAW DOWNLOAD DATA TYPE: {type(download_data)}")
            print(f"\nRAW DOWNLOAD DATA KEYS: {download_data.keys() if hasattr(download_data, 'keys') else 'N/A'}")
            
            print("\n--- FULL DOWNLOAD DATA (JSON) ---")
            print(json.dumps(download_data, indent=2, default=str))
            
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()
    
    # =========================================================
    # TEST 4: TV SERIES (Breaking Bad)
    # =========================================================
    print("\n\n" + "=" * 80)
    print("TEST 4: SEARCH FOR 'breaking bad' (TV SERIES)")
    print("=" * 80)
    
    search2 = Search(session, query="breaking bad")
    results2 = await search2.get_content_model()
    
    print(f"\nFound {len(results2.items)} results")
    
    tv_items = [item for item in results2.items if item.subjectType == 2]
    if tv_items:
        tv_first = tv_items[0]
        print(f"\nFIRST TV SERIES:")
        print(f"Title: {tv_first.title}")
        print(f"SubjectType: {tv_first.subjectType}")
        print(f"DetailPath: {tv_first.detailPath}")
        
        # TV Series Details
        print("\n" + "=" * 80)
        print(f"TEST 4b: TV SERIES DETAILS for '{tv_first.title}'")
        print("=" * 80)
        
        try:
            tv_details_obj = TVSeriesDetails(session)
            print(f"\nTV Details object type: {type(tv_details_obj)}")
            
            tv_detail_data = await tv_details_obj.get_content(tv_first.detailPath)
            print(f"\nRAW TV DETAILS DATA TYPE: {type(tv_detail_data)}")
            print(f"\nRAW TV DETAILS KEYS: {tv_detail_data.keys() if hasattr(tv_detail_data, 'keys') else 'N/A'}")
            
            print("\n--- FULL TV DETAILS DATA (JSON) ---")
            print(json.dumps(tv_detail_data, indent=2, default=str)[:3000])
            
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()
        
        # TV Series Downloads
        print("\n" + "=" * 80)
        print(f"TEST 4c: TV SERIES DOWNLOADS for '{tv_first.title}'")
        print("=" * 80)
        
        try:
            tv_downloads_obj = DownloadableTVSeriesFilesDetail(session, tv_first)
            print(f"\nTV Downloads object type: {type(tv_downloads_obj)}")
            
            tv_download_data = await tv_downloads_obj.get_content(season=1, episode=1)
            print(f"\nRAW TV DOWNLOADS DATA TYPE: {type(tv_download_data)}")
            print(f"\nRAW TV DOWNLOADS KEYS: {tv_download_data.keys() if hasattr(tv_download_data, 'keys') else 'N/A'}")
            
            print("\n--- FULL TV DOWNLOADS DATA (JSON) ---")
            print(json.dumps(tv_download_data, indent=2, default=str))
            
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(raw_test())
