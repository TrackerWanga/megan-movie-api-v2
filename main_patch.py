# Add this import at the top of main.py
from fastapi import FastAPI, Query, Request

# Then in the download/watch endpoints, change:
# headers={"Range": request.headers.get("Range") if hasattr(request, 'headers') else None}
# to:
# headers={"Range": request.headers.get("Range")} if request else {}
