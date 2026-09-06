import re
from typing import Dict, Any, Optional
import markdown

DRIVE_FILE_ID_PATTERNS = [
    r"drive\.google\.com/file/(?:u/\d+/)?d/([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/uc\?(?:.*&)?id=([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/thumbnail\?(?:.*&)?id=([a-zA-Z0-9_-]+)",
    r"lh3\.googleusercontent\.com/d/([a-zA-Z0-9_-]+)",
]

YOUTUBE_PATTERNS = [
    r"(?:youtube\.com/watch\?(?:.*&)?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
]

def extract_google_drive_id(url: str) -> Optional[str]:
    if not url:
        return None
    for pattern in DRIVE_FILE_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def process_photo_url(url: str) -> Dict[str, Any]:
    url = url.strip() if url else ""
    drive_id = extract_google_drive_id(url)
    
    if drive_id:
        return {
            "is_drive": True,
            "file_id": drive_id,
            # lh3.googleusercontent.com is Google's CDN direct link for public files
            "display_url": f"https://lh3.googleusercontent.com/d/{drive_id}",
            "fallback_url": f"https://drive.google.com/file/d/{drive_id}/view?usp=sharing",
            "raw_url": url,
        }
    
    # Generic direct image URL
    return {
        "is_drive": False,
        "file_id": None,
        "display_url": url,
        "fallback_url": url,
        "raw_url": url,
    }

def extract_youtube_id(url: str) -> Optional[str]:
    if not url:
        return None
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def process_video_url(url: str) -> Dict[str, Any]:
    url = url.strip() if url else ""
    video_id = extract_youtube_id(url)
    
    if video_id:
        return {
            "is_youtube": True,
            "video_id": video_id,
            "embed_url": f"https://www.youtube.com/embed/{video_id}?rel=0",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "fallback_url": f"https://www.youtube.com/watch?v={video_id}",
            "raw_url": url,
        }
    
    return {
        "is_youtube": False,
        "video_id": None,
        "embed_url": url,
        "thumbnail_url": None,
        "fallback_url": url,
        "raw_url": url,
    }

def process_media_item(media) -> Dict[str, Any]:
    res = {
        "id": getattr(media, "id", None),
        "type": getattr(media, "type", "photo"),
        "url": getattr(media, "url", ""),
        "caption": getattr(media, "caption", None),
        "order_index": getattr(media, "order_index", 0),
    }
    if res["type"] == "photo":
        photo_info = process_photo_url(res["url"])
        res.update(photo_info)
    elif res["type"] == "video":
        video_info = process_video_url(res["url"])
        res.update(video_info)
    return res

def render_markdown(text: Optional[str]) -> str:
    if not text:
        return ""
    return markdown.markdown(
        text,
        extensions=[
            "extra",
            "nl2br",
            "sane_lists",
            "smarty",
        ]
    )
