import os
import re
from typing import List, Dict, Any
import httpx

DRIVE_FOLDER_PATTERNS = [
    r"drive\.google\.com/drive/(?:u/\d+/)?folders/([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/folderview\?id=([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
]

def extract_google_drive_folder_id(url: str):
    if not url:
        return None
    url = url.strip().strip("'\"")
    for pattern in DRIVE_FOLDER_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_google_drive_folder_photos(folder_id: str) -> List[Dict[str, Any]]:
    results = []
    seen_ids = set()
    seen_ids.add(folder_id)

    # 1. Try embeddedfolderview
    urls_to_try = [
        f"https://drive.google.com/embeddedfolderview?id={folder_id}#grid",
        f"https://drive.google.com/drive/folders/{folder_id}"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as client:
        for u in urls_to_try:
            try:
                resp = client.get(u)
                if resp.status_code == 200:
                    html = resp.text
                    # Extract file IDs from URLs like /file/d/{id} or /open?id={id} or ["{id}",
                    # Pattern 1: explicit file/d links
                    matches = re.findall(r"drive\.google\.com/file/d/([a-zA-Z0-9_-]{25,50})", html)
                    for fid in matches:
                        if fid not in seen_ids:
                            seen_ids.add(fid)
                            results.append({
                                "file_id": fid,
                                "url": f"https://lh3.googleusercontent.com/d/{fid}",
                                "fallback_url": f"https://drive.google.com/file/d/{fid}/view?usp=sharing",
                                "caption": f"Photo {len(results)+1}",
                                "type": "photo"
                            })
                    
                    # Pattern 2: embedded drive items ["id", "filename.jpg"]
                    raw_pairs = re.findall(r'\[\s*"([a-zA-Z0-9_-]{25,50})"\s*,\s*\[\s*"([^"]+?\.(?:jpg|jpeg|png|webp|gif|JPG|JPEG|PNG|WEBP))"', html)
                    for fid, fname in raw_pairs:
                        if fid not in seen_ids:
                            seen_ids.add(fid)
                            results.append({
                                "file_id": fid,
                                "url": f"https://lh3.googleusercontent.com/d/{fid}",
                                "fallback_url": f"https://drive.google.com/file/d/{fid}/view?usp=sharing",
                                "caption": fname,
                                "type": "photo"
                            })

                    # Pattern 3: general drive item JSON matches
                    item_matches = re.findall(r'\["([a-zA-Z0-9_-]{28,45})",\["([^"]+)"', html)
                    for fid, fname in item_matches:
                        if fid not in seen_ids and any(fname.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                            seen_ids.add(fid)
                            results.append({
                                "file_id": fid,
                                "url": f"https://lh3.googleusercontent.com/d/{fid}",
                                "fallback_url": f"https://drive.google.com/file/d/{fid}/view?usp=sharing",
                                "caption": fname,
                                "type": "photo"
                            })
                    
                    if results:
                        break
            except Exception as e:
                print(f"Error fetching {u}: {e}")

    return results

print("Folder ID test:", extract_google_drive_folder_id("https://drive.google.com/drive/folders/1w7VqXy5eE_abc1234567890"))
