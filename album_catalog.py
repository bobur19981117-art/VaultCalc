#!/usr/bin/env python3
"""
album_catalog.py — Media Catalog & Categorization Manager for "МОЙ АЛЬБОМ"
Features:
- SQLite persistence of all downloaded media (Instagram, YouTube, etc.)
- Channel catalog pinned message generator with live stats
- Categorized Telegram hashtags (#Instagram, #Instagram_Video, #YouTube, etc.)
- Interactive bot menu navigation for categories
- Instant re-send from catalog by file_id
"""

import sqlite3
import os
import logging
from datetime import datetime
from html import escape as html_escape

logger = logging.getLogger("album_catalog")

DB_PATH = os.path.join(os.path.dirname(__file__), "album_catalog.db")

def init_catalog_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS media_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                media_type TEXT NOT NULL,
                title TEXT,
                media_url TEXT,
                file_id TEXT,
                size_mb REAL DEFAULT 0.0,
                duration INTEGER DEFAULT 0,
                channel_msg_id INTEGER,
                user_id INTEGER,
                user_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_platform_type ON media_catalog(platform, media_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON media_catalog(created_at)")
        conn.commit()
        conn.close()
        logger.info("Catalog DB initialized successfully.")
    except Exception as e:
        logger.error(f"Catalog DB init error: {e}")

def save_media_to_catalog(platform, media_type, title, media_url, file_id, size_mb, duration=0, channel_msg_id=None, user_id=None, user_name=""):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO media_catalog (platform, media_type, title, media_url, file_id, size_mb, duration, channel_msg_id, user_id, user_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            (platform or "other").lower(),
            (media_type or "video").lower(),
            title or "Nomsiz Media",
            media_url or "",
            file_id or "",
            float(size_mb or 0.0),
            int(duration or 0),
            channel_msg_id,
            user_id,
            user_name
        ))
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id
    except Exception as e:
        logger.error(f"Error saving to catalog: {e}")
        return None

def get_catalog_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT platform, media_type, COUNT(*) 
            FROM media_catalog 
            GROUP BY platform, media_type
        """)
        rows = cur.fetchall()
        conn.close()
        stats = {}
        for p, t, cnt in rows:
            stats[f"{p}_{t}"] = cnt
        return stats
    except Exception as e:
        logger.error(f"Error getting catalog stats: {e}")
        return {}

def get_media_items(platform=None, media_type=None, limit=6, offset=0):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        query = "SELECT * FROM media_catalog WHERE 1=1"
        params = []
        if platform:
            query += " AND platform = ?"
            params.append(platform.lower())
        if media_type:
            query += " AND media_type = ?"
            params.append(media_type.lower())
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Error getting media items: {e}")
        return []

def get_media_item_by_id(item_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM media_catalog WHERE id = ?", (item_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting media item: {e}")
        return None

def format_channel_caption(platform, media_type, title, user_name, size_mb, media_url):
    platform_lower = (platform or "other").lower()
    type_lower = (media_type or "video").lower()

    if platform_lower == "instagram":
        if type_lower == "audio":
            badge = "🎵 <b>INSTAGRAM AUDIO / MP3</b>"
            tags = "#Instagram #Instagram_Audio #Audio #Musiqa"
        elif type_lower == "photo":
            badge = "🖼 <b>INSTAGRAM RASM / POST</b>"
            tags = "#Instagram #Instagram_Photo #Rasm"
        else:
            badge = "📸 <b>INSTAGRAM REELS / VIDEO</b>"
            tags = "#Instagram #Instagram_Video #Video"
    elif platform_lower == "youtube":
        if type_lower == "audio":
            badge = "🎧 <b>YOUTUBE AUDIO / MP3</b>"
            tags = "#YouTube #YouTube_Music #Audio #Musiqa"
        else:
            badge = "🔴 <b>YOUTUBE VIDEO / SHORTS</b>"
            tags = "#YouTube #YouTube_Video #Video"
    else:
        if type_lower == "audio":
            badge = "🎵 <b>AUDIO / MP3</b>"
            tags = "#Audio #Musiqa"
        else:
            badge = "🎬 <b>MEDIA VIDEO</b>"
            tags = "#Video"

    caption = (
        f"{badge}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 <b>{html_escape(title)}</b>\n\n"
        f"👤 <b>Yuboruvchi:</b> {html_escape(user_name)}\n"
        f"💾 <b>Hajmi:</b> {size_mb:.1f} MB\n"
        f"🔗 <a href='{media_url}'>{platform.capitalize()} asliga o‘tish</a>\n\n"
        f"🏷 <b>Bo‘lim:</b> {tags}\n"
        f"🤖 @boburchat_bot (24/7 Cloud)"
    )
    return caption, tags

def format_catalog_message(stats=None):
    if stats is None:
        stats = get_catalog_stats()

    ig_vid = stats.get("instagram_video", 0)
    ig_aud = stats.get("instagram_audio", 0)
    ig_pic = stats.get("instagram_photo", 0)
    yt_vid = stats.get("youtube_video", 0)
    yt_aud = stats.get("youtube_audio", 0)
    total = sum(stats.values())

    msg = (
        f"📁 <b>«МОЙ АЛЬБОМ» — BO‘LIMLAR VA KATALOG</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Istalgan bo‘lim tegi ustiga bosing — Telegram o‘sha bo‘limdagi barcha video va audiolarni ajratib ochib beradi:</i>\n\n"
        f"📸 <b>INSTAGRAM BO‘LIMI:</b>\n"
        f"  • #Instagram — Barcha Instagram fayllari ({ig_vid + ig_aud + ig_pic})\n"
        f"  • #Instagram_Video — Reels va videolar ({ig_vid})\n"
        f"  • #Instagram_Audio — Musiqa va MP3 lar ({ig_aud})\n"
        f"  • #Instagram_Photo — Rasmlar va postlar ({ig_pic})\n\n"
        f"🔴 <b>YOUTUBE BO‘LIMI:</b>\n"
        f"  • #YouTube — Barcha YouTube fayllari ({yt_vid + yt_aud})\n"
        f"  • #YouTube_Video — Videolar va Shorts ({yt_vid})\n"
        f"  • #YouTube_Music — Qo‘shiqlar va MP3 lar ({yt_aud})\n\n"
        f"📖 <b>HIKMATLAR & KITOB:</b>\n"
        f"  • #Hikmatlar — «Qalbga yetib boradigan so‘zlar»\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Jami tartiblangan fayllar:</b> {total} ta\n"
        f"💡 <i>Har bir yangi yuklangan fayl avtomatik o‘z bo‘limiga joylanadi.</i>\n"
        f"🤖 @boburchat_bot orqali boshqariladi"
    )
    return msg

def get_album_categories_markup():
    stats = get_catalog_stats()
    ig_vid = stats.get("instagram_video", 0)
    ig_aud = stats.get("instagram_audio", 0)
    yt_vid = stats.get("youtube_video", 0)
    yt_aud = stats.get("youtube_audio", 0)

    return {
        "inline_keyboard": [
            [
                {"text": f"📸 Instagram Video ({ig_vid})", "callback_data": "cat_view:instagram:video:0"},
                {"text": f"🎵 Instagram Audio ({ig_aud})", "callback_data": "cat_view:instagram:audio:0"}
            ],
            [
                {"text": f"🔴 YouTube Video ({yt_vid})", "callback_data": "cat_view:youtube:video:0"},
                {"text": f"🎧 YouTube Musiqa ({yt_aud})", "callback_data": "cat_view:youtube:audio:0"}
            ],
            [
                {"text": "📌 Kanal Mundarijasini Yangilash", "callback_data": "cat_refresh_pinned"}
            ],
            [
                {"text": "🔗 'МОЙ АЛЬБОМ' Kanaliga O‘tish", "url": "https://t.me/+bZUlidVcv8UxMDJi"}
            ]
        ]
    }

def format_category_view(platform, media_type, page=0, channel_id=-1004342721043):
    limit = 5
    offset = page * limit
    items = get_media_items(platform=platform, media_type=media_type, limit=limit, offset=offset)

    clean_ch_id = str(abs(channel_id))[3:] if str(channel_id).startswith("-100") else str(abs(channel_id))

    title_map = {
        ("instagram", "video"): ("📸 Instagram Videolar / Reels", "#Instagram_Video"),
        ("instagram", "audio"): ("🎵 Instagram Audio / MP3 lar", "#Instagram_Audio"),
        ("youtube", "video"): ("🔴 YouTube Videolar / Shorts", "#YouTube_Video"),
        ("youtube", "audio"): ("🎧 YouTube Musiqa / MP3 lar", "#YouTube_Music"),
    }
    cat_title, cat_tag = title_map.get((platform, media_type), (f"{platform.capitalize()} {media_type.capitalize()}", f"#{platform.capitalize()}"))

    if not items and page == 0:
        text = (
            f"<b>{cat_title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Hozircha ushbu bo‘limda yangi saqlangan fayllar yo‘q.\n\n"
            f"💡 <i>{platform.capitalize()} havolasini yuborsangiz, bot uni yuklab avtomatik tarzda mana shu bo‘limga tartib bilan joylaydi!</i>"
        )
        markup = {
            "inline_keyboard": [
                [{"text": f"🏷 Kanalda {cat_tag} bilan ochish", "url": "https://t.me/+bZUlidVcv8UxMDJi"}],
                [{"text": "🔙 Bo‘limlar Menyusi", "callback_data": "cat_back_main"}]
            ]
        }
        return text, markup

    text = f"<b>{cat_title}</b> (Sahifa {page + 1})\n━━━━━━━━━━━━━━━━━━━━\n\n"
    keyboard = []

    for i, it in enumerate(items, 1):
        idx = offset + i
        t = html_escape(it['title'][:40])
        sz = it['size_mb']
        msg_id = it.get('channel_msg_id')
        dt = it.get('created_at', '')[:10]

        link_str = f"<a href='https://t.me/c/{clean_ch_id}/{msg_id}'>Kanalda ko‘rish ↗️</a>" if msg_id else "<i>Kanalda saqlangan</i>"
        icon = "🎵" if media_type == "audio" else "🎬"
        text += f"<b>{idx}.</b> {icon} <b>{t}</b> ({sz:.1f} MB)\n   📅 {dt} | {link_str}\n\n"

        keyboard.append([{"text": f"📥 #{idx} ni botda qayta olish", "callback_data": f"cat_resend:{it['id']}"}])

    nav_row = []
    if page > 0:
        nav_row.append({"text": "⬅️ Oldingi", "callback_data": f"cat_view:{platform}:{media_type}:{page-1}"})
    if len(items) == limit:
        nav_row.append({"text": "Keyingi ➡️", "callback_data": f"cat_view:{platform}:{media_type}:{page+1}"})
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([{"text": f"🏷 Kanalda {cat_tag} tegi bilan ochish", "url": "https://t.me/+bZUlidVcv8UxMDJi"}])
    keyboard.append([{"text": "🔙 Bo‘limlar Menyusi", "callback_data": "cat_back_main"}])

    return text, {"inline_keyboard": keyboard}
