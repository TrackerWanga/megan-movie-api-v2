import enum
import sys
import asyncio
import json
import pprint

if not hasattr(enum, 'StrEnum'):
    from strenum import StrEnum
    enum.StrEnum = StrEnum

from moviebox_api.v2 import Search, Session, MovieDetails, TVSeriesDetails
from moviebox_api.v2.download import DownloadableSingleFilesDetail, DownloadableTVSeriesFilesDetail
from moviebox_api.v2.core import Homepage

pp = pprint.PrettyPrinter(indent=2, width=200, compact=False)

async def dump_all():
    session = Session()
    
    print("=" * 100)
    print("RAW DUMP - DESPICABLE ME 4 SEARCH")
    print("=" * 100)
    
    search1 = Search(session, query="despicable me 4")
    results1 = await search1.get_content()
    
    print("\n--- RAW SEARCH RESULTS (dict) ---")
    pp.pprint(results1)
    
    print("\n" + "=" * 100)
    print("RAW DUMP - SEARCH MODEL")
    print("=" * 100)
    
    model1 = await search1.get_content_model()
    print(f"\nModel type: {type(model1)}")
    print(f"\nModel dict: {model1.__dict__}")
    
    print("\n" + "=" * 100)
    print("RAW DUMP - FIRST MOVIE ITEM")
    print("=" * 100)
    
    movies = [r for r in model1.items if r.subjectType == 1]
    if movies:
        movie = movies[0]
        print(f"\nMovie item type: {type(movie)}")
        print(f"\nMovie item dict: {movie.__dict__}")
        
        print("\n" + "=" * 100)
        print("RAW DUMP - MOVIE DETAILS")
        print("=" * 100)
        
        details = MovieDetails(session)
        detail_data = await details.get_content(movie.detailPath)
        print(f"\nDetail data type: {type(detail_data)}")
        print(f"\nDetail data:")
        pp.pprint(detail_data)
        
        print("\n" + "=" * 100)
        print("RAW DUMP - MOVIE DOWNLOADS")
        print("=" * 100)
        
        download_obj = DownloadableSingleFilesDetail(session, movie)
        download_data = await download_obj.get_content()
        print(f"\nDownload data type: {type(download_data)}")
        print(f"\nDownload data:")
        pp.pprint(download_data)
        
        if hasattr(download_data, 'downloads'):
            print(f"\n--- DOWNLOADS LIST ---")
            for i, dl in enumerate(download_data.downloads):
                print(f"\nDownload item {i}:")
                print(f"Type: {type(dl)}")
                print(f"Dict: {dl.__dict__ if hasattr(dl, '__dict__') else dl}")
        
        if hasattr(download_data, 'captions'):
            print(f"\n--- CAPTIONS LIST ---")
            for i, cap in enumerate(download_data.captions):
                print(f"\nCaption item {i}:")
                print(f"Type: {type(cap)}")
                print(f"Dict: {cap.__dict__ if hasattr(cap, '__dict__') else cap}")
    
    print("\n" + "=" * 100)
    print("RAW DUMP - EVERYBODY HATES CHRIS SEARCH")
    print("=" * 100)
    
    search2 = Search(session, query="everybody hates chris")
    results2 = await search2.get_content()
    
    print("\n--- RAW SEARCH RESULTS ---")
    pp.pprint(results2)
    
    print("\n" + "=" * 100)
    print("RAW DUMP - TV SEARCH MODEL")
    print("=" * 100)
    
    model2 = await search2.get_content_model()
    print(f"\nModel type: {type(model2)}")
    print(f"\nModel dict: {model2.__dict__}")
    
    print("\n" + "=" * 100)
    print("RAW DUMP - FIRST TV ITEM")
    print("=" * 100)
    
    tv_shows = [r for r in model2.items if r.subjectType == 2]
    if tv_shows:
        show = tv_shows[0]
        print(f"\nTV item type: {type(show)}")
        print(f"\nTV item dict: {show.__dict__}")
        
        print("\n" + "=" * 100)
        print("RAW DUMP - TV DETAILS")
        print("=" * 100)
        
        tv_details = TVSeriesDetails(session)
        tv_detail_data = await tv_details.get_content(show.detailPath)
        print(f"\nTV Detail data:")
        pp.pprint(tv_detail_data)
        
        print("\n" + "=" * 100)
        print("RAW DUMP - TV DOWNLOADS")
        print("=" * 100)
        
        tv_download_obj = DownloadableTVSeriesFilesDetail(session, show)
        tv_download_data = await tv_download_obj.get_content()
        print(f"\nTV Download data:")
        pp.pprint(tv_download_data)
        
        if hasattr(tv_download_data, 'downloads'):
            print(f"\n--- TV DOWNLOADS LIST ---")
            for i, dl in enumerate(tv_download_data.downloads):
                print(f"\nTV Download item {i}:")
                print(f"Type: {type(dl)}")
                print(f"Dict: {dl.__dict__ if hasattr(dl, '__dict__') else dl}")
        
        if hasattr(tv_download_data, 'captions'):
            print(f"\n--- TV CAPTIONS LIST ---")
            for i, cap in enumerate(tv_download_data.captions):
                print(f"\nTV Caption item {i}:")
                print(f"Type: {type(cap)}")
                print(f"Dict: {cap.__dict__ if hasattr(cap, '__dict__') else cap}")
    
    print("\n" + "=" * 100)
    print("RAW DUMP - HOMEPAGE")
    print("=" * 100)
    
    homepage = Homepage(session)
    home_data = await homepage.get_content()
    print(f"\nHomepage data:")
    pp.pprint(home_data)
    
    try:
        home_model = await homepage.get_content_model()
        print(f"\nHomepage model type: {type(home_model)}")
        print(f"\nHomepage model dict: {home_model.__dict__}")
    except Exception as e:
        print(f"\nHomepage model error: {e}")

asyncio.run(dump_all())
