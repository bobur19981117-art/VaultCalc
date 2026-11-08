#!/data/data/com.termux/files/usr/bin/python3
"""
Media Downloader Module for @boburchat_bot & "МОЙ АЛЬБОМ" Channel.
Handles downloading:
- Instagram: Reels, Videos, Posts (with fallback & cookie support)
- YouTube: Videos (MP4 up to 1080p), Shorts, Audio (MP3 192kbps)
- TikTok, Pinterest, Twitter/X, Facebook (via yt-dlp)
"""

import os
import re
import time
import glob
import json
import uuid
import logging
import subprocess
from html import escape as html_escape

import shutil

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    import parth_dl
except ImportError:
    parth_dl = None

try:
    import instaloader
except ImportError:
    instaloader = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.getenv("MEDIA_DIR", os.path.join(BASE_DIR, "downloads", "media_bot"))
os.makedirs(MEDIA_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(BASE_DIR, "instagram_cookies.txt")
NODE_BIN = shutil.which("node") or "/usr/bin/node"
NODE_AVAILABLE = bool(shutil.which("node") or os.path.exists(NODE_BIN))

# Regex patterns
INSTAGRAM_REGEX = re.compile(
    r'https?://(?:www\.)?(?:instagram\.com|instagr\.am)/(?:(?:share/)?(?:p|reel|reels|tv)|share)/([a-zA-Z0-9_\-]+)',
    re.IGNORECASE
)
YOUTUBE_REGEX = re.compile(
    r'https?://(?:www\.|m\.|music\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/|live/)|youtu\.be/)([a-zA-Z0-9_\-]+)',
    re.IGNORECASE
)
GENERIC_MEDIA_REGEX = re.compile(
    r'https?://(?:www\.)?(?:tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com|twitter\.com|x\.com|pinterest\.com|pin\.it|facebook\.com|fb\.watch)/[^\s]+',
    re.IGNORECASE
)
ANY_HTTP_URL = re.compile(r'https?://[^\s]+', re.IGNORECASE)

# In-memory download task cache for inline buttons
# { task_id: {"url": str, "chat_id": int, "user_id": int, "user_name": str, "title": str, "platform": str} }
PENDING_DOWNLOADS = {}


def extract_media_url(text: str):
    """Finds first media URL in message text and normalizes it."""
    if not text:
        return None, None

    # Priority 1: Instagram
    m_ig = INSTAGRAM_REGEX.search(text)
    if m_ig:
        shortcode = m_ig.group(1)
        return f"https://www.instagram.com/reel/{shortcode}/", "instagram"

    # Priority 2: YouTube
    m_yt = YOUTUBE_REGEX.search(text)
    if m_yt:
        vid_id = m_yt.group(1)
        return f"https://www.youtube.com/watch?v={vid_id}", "youtube"

    # Priority 3: TikTok / Twitter / Facebook / Pinterest
    m_gen = GENERIC_MEDIA_REGEX.search(text)
    if m_gen:
        return m_gen.group(0).split("?")[0], "generic"

    return None, None


def clean_temp_files(max_age_seconds=1800):
    """Deletes old media files and subdirs in MEDIA_DIR to save disk space."""
    now = time.time()
    try:
        import shutil
        for item in glob.glob(os.path.join(MEDIA_DIR, "*")):
            try:
                mtime = os.path.getmtime(item)
                if (now - mtime) > max_age_seconds:
                    if os.path.isdir(item):
                        shutil.rmtree(item, ignore_errors=True)
                    elif os.path.isfile(item):
                        os.remove(item)
            except Exception:
                pass
    except Exception:
        pass


def compress_video_if_needed(video_path: str, target_size_mb: float = 48.0) -> str:
    """Uses ffmpeg to compress video under Telegram 50MB limit if needed."""
    if not os.path.exists(video_path):
        return video_path

    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    if size_mb <= target_size_mb:
        return video_path

    logging.info(f"Video {video_path} is {size_mb:.2f}MB, compressing to under {target_size_mb}MB...")
    out_path = video_path.rsplit(".", 1)[0] + "_compressed.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-c:v", "libx264", "-crf", "28", "-preset", "faster",
        "-c:a", "aac", "-b:a", "128k",
        "-maxrate", "1.5M", "-bufsize", "3M",
        out_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            try:
                os.remove(video_path)
            except Exception:
                pass
            return out_path
    except Exception as e:
        logging.error(f"Compression error: {e}")

    return video_path


def extract_audio_from_video(video_path: str) -> str:
    """Extracts MP3 from existing video file using ffmpeg."""
    out_path = video_path.rsplit(".", 1)[0] + ".mp3"
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-c:a", "libmp3lame", "-q:a", "2",
        out_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path
    except Exception as e:
        logging.error(f"Error extracting audio: {e}")
    return None


def download_media(url: str, mode: str = "video") -> dict:
    """
    Downloads media from URL.
    mode: 'video' or 'audio'
    """
    clean_temp_files()
    uid = uuid.uuid4().hex[:8]
    task_dir = os.path.join(MEDIA_DIR, uid)
    os.makedirs(task_dir, exist_ok=True)

    # Special optimized path for Instagram:
    is_instagram = "instagram.com" in url or "instagr.am" in url
    if is_instagram and parth_dl:
        try:
            logging.info(f"Downloading Instagram media via parth-dl to {task_dir}...")
            parth_dl.download(url, output_path=task_dir)
            found_files = glob.glob(os.path.join(task_dir, "*.mp4")) + glob.glob(os.path.join(task_dir, "*.mov"))
            if found_files:
                latest_file = max(found_files, key=os.path.getctime)
                base_name = os.path.basename(latest_file).rsplit(".", 1)[0].replace("_", " ")

                if mode == "audio":
                    # Extract audio directly from downloaded Instagram video
                    mp3_path = extract_audio_from_video(latest_file)
                    if mp3_path and os.path.exists(mp3_path):
                        size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
                        return {
                            "success": True,
                            "mode": "audio",
                            "file_path": mp3_path,
                            "title": base_name or "Instagram Audio",
                            "performer": "Instagram",
                            "duration": 0,
                            "size_mb": size_mb,
                            "error": None
                        }
                else:
                    latest_file = compress_video_if_needed(latest_file)
                    size_mb = os.path.getsize(latest_file) / (1024 * 1024)
                    return {
                        "success": True,
                        "mode": "video",
                        "file_path": latest_file,
                        "title": base_name or "Instagram Video",
                        "performer": "Instagram",
                        "duration": 0,
                        "width": 720,
                        "height": 1280,
                        "size_mb": size_mb,
                        "error": None
                    }
            else:
                # Check if it was an image
                found_images = glob.glob(os.path.join(task_dir, "*.jpg")) + glob.glob(os.path.join(task_dir, "*.png")) + glob.glob(os.path.join(task_dir, "*.webp"))
                if found_images:
                    latest_img = max(found_images, key=os.path.getctime)
                    size_mb = os.path.getsize(latest_img) / (1024 * 1024)
                    return {
                        "success": True,
                        "mode": "photo",
                        "file_path": latest_img,
                        "title": base_name or "Instagram Photo",
                        "performer": "Instagram",
                        "duration": 0,
                        "size_mb": size_mb,
                        "error": None
                    }
        except Exception as pe:
            logging.warning(f"parth-dl failed: {pe}, falling back to yt-dlp...")

    # Mode Audio via yt-dlp:
    if mode == "audio":
        outtmpl = os.path.join(task_dir, "audio.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        if NODE_AVAILABLE:
            ydl_opts['js_runtimes'] = {'node': {}}
            ydl_opts['remote_components'] = {'ejs:github'}
        if os.path.exists(COOKIES_FILE):
            ydl_opts['cookiefile'] = COOKIES_FILE

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Audio Track')
                duration = int(info.get('duration') or 0)
                performer = info.get('uploader') or info.get('artist') or "YouTube / Instagram"

                found_files = glob.glob(os.path.join(task_dir, "*.mp3"))
                if found_files:
                    final_path = found_files[0]
                    size_mb = os.path.getsize(final_path) / (1024 * 1024)
                    return {
                        "success": True,
                        "mode": "audio",
                        "file_path": final_path,
                        "title": title,
                        "performer": performer,
                        "duration": duration,
                        "size_mb": size_mb,
                        "error": None
                    }
                else:
                    return {"success": False, "error": "MP3 fayli yaratilmadi."}
        except Exception as e:
            err_msg = str(e)
            logging.error(f"yt-dlp audio download error: {err_msg}")
            return {"success": False, "error": err_msg}

    # Mode Video via yt-dlp:
    outtmpl = os.path.join(task_dir, "video.%(ext)s")
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }
    if NODE_AVAILABLE:
        ydl_opts['js_runtimes'] = {'node': {}}
        ydl_opts['remote_components'] = {'ejs:github'}
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')
            duration = int(info.get('duration') or 0)
            width = int(info.get('width') or 0)
            height = int(info.get('height') or 0)
            performer = info.get('uploader') or ""

            found_files = glob.glob(os.path.join(task_dir, "*.mp4")) + glob.glob(os.path.join(task_dir, "*.mkv"))
            if found_files:
                final_path = found_files[0]
                final_path = compress_video_if_needed(final_path)
                size_mb = os.path.getsize(final_path) / (1024 * 1024)
                return {
                    "success": True,
                    "mode": "video",
                    "file_path": final_path,
                    "title": title,
                    "performer": performer,
                    "duration": duration,
                    "width": width,
                    "height": height,
                    "size_mb": size_mb,
                    "error": None
                }
    except Exception as e:
        err_msg = str(e)
        logging.warning(f"yt-dlp video error: {err_msg}")
        return {"success": False, "error": err_msg}

    return {"success": False, "error": "Video yuklanmadi."}
