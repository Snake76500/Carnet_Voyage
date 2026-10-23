import re
import json
import httpx

def test_drive_folder_id(url: str):
    patterns = [
        r"drive\.google\.com/drive/(?:u/\d+/)?folders/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/folderview\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)"
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

print("Pattern test 1:", test_drive_folder_id("https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J?usp=sharing"))
print("Pattern test 2:", test_drive_folder_id("https://drive.google.com/drive/u/0/folders/1xyz_ABC-123"))
