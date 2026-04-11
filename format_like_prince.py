from urllib.parse import quote

# Raw CDN URL from moviebox_api
raw_url = "https://bcdnxw.hakunaymatata.com/resource/4395ced5b1d2515978eb4e40d0061d8c.mp4?sign=ba8bb11c15a8ef4993bd3beb21541049&t=1775806376"

# PRINCE format
prince_format = f"https://movieapi.princetechn.com/api/dl?url={quote(raw_url, safe='')}&title=War%20Machine&quality=1080p"

print("=" * 80)
print("PRINCE STYLE URL")
print("=" * 80)
print(prince_format)
print("\n" + "=" * 80)
print("YOUR API COULD USE SAME PATTERN")
print("=" * 80)
print(f"https://movieapi.megan.qzz.io/api/dl?url={quote(raw_url, safe='')}&title=War%20Machine&quality=1080p")
