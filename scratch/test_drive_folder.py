import re
import httpx

test_folder_id = "1b_v7qXy5eE_placeholder" # We will test pattern extraction first
patterns = [
    r"drive\.google\.com/drive/(?:u/\d+/)?folders/([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/folderview\?id=([a-zA-Z0-9_-]+)",
]

for p in patterns:
    m = re.search(p, "https://drive.google.com/drive/folders/1w7VqXy5eE-abc_123XYZ")
    if m:
        print("Matched:", m.group(1))
