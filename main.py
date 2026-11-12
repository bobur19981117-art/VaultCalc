#!/usr/bin/env python3
"""
@boburchat_bot — 24/7 Cloud Edition for Render.com / Docker
Features:
- Instagram (Reels, Posts) & YouTube (Video, Shorts, MP3) Media Downloader
- Automatic sync to "МОЙ АЛЬБОМ" Channel (-1004342721043)
- «Qalbga yetib boradigan so‘zlar» Book Module (PDF, HTML, Quotes, Navigation)
- Google Gemini AI Assistant (Fast & Smart answers)
- Cloud Linux Terminal Controller (/sh)
- FastAPI Health Check (/health) for 24/7 Keep-Alive
"""

import os
import sys
import time
import json
import uuid
import shutil
import logging
import requests
import threading
import subprocess
from datetime import datetime
from html import escape as html_escape

from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse

# Book module
from book_bot_module import (
    get_main_book_menu_markup, get_toc_markup, get_chapter_nav_markup,
    format_chapter_text, format_random_quote, send_book_document,
    post_quote_to_channel, PDF_PATH, HTML_PATH, BOOK_INFO, AUTHOR_NOTE,
    FINAL_LETTER, LIFE_CONCLUSIONS, TOP_100_QUOTES, get_chapter
)

# Media downloader
from media_downloader import (
    extract_media_url, download_media, extract_audio_from_video,
    PENDING_DOWNLOADS, clean_temp_files
)

# Album Catalog & Categorization Module
from album_catalog import (
    init_catalog_db, save_media_to_catalog, get_catalog_stats,
    format_channel_caption, format_catalog_message,
    get_album_categories_markup, format_category_view,
    get_media_item_by_id
)

# Binance AI & Crypto Module
try:
    from binance_module import (
        get_account_summary_text, get_crypto_prices_text,
        get_open_orders_text, get_binance_markup
    )
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Optional Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("boburchat_bot_cloud")

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "1260991773"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1004342721043"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PORT = int(os.getenv("PORT", "8080"))

API_BASE = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
BASE_URL = f"{API_BASE}/bot{BOT_TOKEN}"
FILE_URL = f"{API_BASE}/file/bot{BOT_TOKEN}"

# Configure Gemini
ai_model = None
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        ai_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=(
                "Siz Boburning shaxsiy, yuqori malakali AI yordamchisisiz. "
                "Foydalanuvchiga o'zbek tilida aniq, tushunarli, do'stona va professional javob bering. "
                "Markdown formatidan chiroyli foydalaning."
            )
        )
        logger.info("Google Gemini AI muvaffaqiyatli ulandi.")
    except Exception as ge:
        logger.warning(f"Gemini AI sozlashda ogohlantirish: {ge}")

# Keyboard
MAIN_KEYBOARD = {
    "keyboard": [
        [
            {"text": "📱 Albom Ilovasi", "web_app": {"url": "https://boburchat-bot.onrender.com/app"}},
            {"text": "📥 Media Yuklovchi"}
        ],
        [{"text": "📁 Albom Bo‘limlari"}, {"text": "📖 Qalbga yetib boradigan so‘zlar"}],
        [{"text": "🎲 Qalb iqtibosi"}, {"text": "📊 Tizim holati"}],
        [{"text": "🟡 Binance Portfel"}, {"text": "ℹ️ Yordam"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}

# --- Telegram API Helpers ---

def send_chat_action(chat_id, action="typing"):
    try:
        requests.post(f"{BASE_URL}/sendChatAction", data={"chat_id": chat_id, "action": action}, timeout=10)
    except Exception:
        pass

def keep_typing(chat_id, stop_event, action="typing"):
    while not stop_event.is_set():
        send_chat_action(chat_id, action)
        stop_event.wait(4.5)

def send_message(chat_id, text, reply_to_id=None, reply_markup=None, parse_mode="Markdown"):
    if not text:
        return None
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": json.dumps(reply_markup or MAIN_KEYBOARD)
    }
    if reply_to_id:
        payload["reply_to_message_id"] = reply_to_id
    try:
        res = requests.post(f"{BASE_URL}/sendMessage", data=payload, timeout=20)
        if res.ok:
            return res.json().get("result", {}).get("message_id")
        # Retry without parse_mode
        payload.pop("parse_mode", None)
        res = requests.post(f"{BASE_URL}/sendMessage", data=payload, timeout=20)
        if res.ok:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
    return None

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="Markdown"):
    if not text or not message_id:
        return
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        res = requests.post(f"{BASE_URL}/editMessageText", data=payload, timeout=15)
        if not res.ok:
            payload.pop("parse_mode", None)
            requests.post(f"{BASE_URL}/editMessageText", data=payload, timeout=15)
    except Exception as e:
        logger.error(f"Error editing message: {e}")

def delete_message(chat_id, message_id):
    if not message_id:
        return
    try:
        requests.post(f"{BASE_URL}/deleteMessage", data={"chat_id": chat_id, "message_id": message_id}, timeout=10)
    except Exception:
        pass

def send_telegram_video(chat_id, video_path, caption="", reply_to_id=None, reply_markup=None, duration=0, width=0, height=0):
    url = f"{BASE_URL}/sendVideo"
    data = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML",
        "supports_streaming": True
    }
    if reply_to_id:
        data["reply_to_message_id"] = reply_to_id
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    if duration:
        data["duration"] = int(duration)
    if width and height:
        data["width"] = int(width)
        data["height"] = int(height)
    try:
        with open(video_path, "rb") as vf:
            res = requests.post(url, data=data, files={"video": vf}, timeout=240)
            return res.json()
    except Exception as e:
        logger.error(f"Error sending video: {e}")
        return {"ok": False, "error": str(e)}

def send_telegram_audio(chat_id, audio_path, caption="", title="", performer="", reply_to_id=None, reply_markup=None, duration=0):
    url = f"{BASE_URL}/sendAudio"
    data = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    if title:
        data["title"] = title
    if performer:
        data["performer"] = performer
    if reply_to_id:
        data["reply_to_message_id"] = reply_to_id
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    if duration:
        data["duration"] = int(duration)
    try:
        with open(audio_path, "rb") as af:
            res = requests.post(url, data=data, files={"audio": af}, timeout=180)
            return res.json()
    except Exception as e:
        logger.error(f"Error sending audio: {e}")
        return {"ok": False, "error": str(e)}

def send_telegram_photo(chat_id, photo_path, caption="", reply_to_id=None, reply_markup=None):
    url = f"{BASE_URL}/sendPhoto"
    data = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    if reply_to_id:
        data["reply_to_message_id"] = reply_to_id
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        with open(photo_path, "rb") as pf:
            res = requests.post(url, data=data, files={"photo": pf}, timeout=60)
            return res.json()
    except Exception as e:
        logger.error(f"Error sending photo: {e}")
        return {"ok": False, "error": str(e)}

def send_document(chat_id, file_path, caption=None):
    try:
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        with open(file_path, "rb") as f:
            res = requests.post(f"{BASE_URL}/sendDocument", data=data, files={"document": f}, timeout=180)
            return res.ok
    except Exception as e:
        logger.error(f"Error sending document: {e}")
        return False

def post_video_to_channel_by_id(file_id, caption, reply_markup=None):
    try:
        data = {
            "chat_id": CHANNEL_ID,
            "video": file_id,
            "caption": caption,
            "parse_mode": "HTML",
            "supports_streaming": True
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        res = requests.post(f"{BASE_URL}/sendVideo", data=data, timeout=30)
        if res.ok:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        logger.error(f"Channel video post error: {e}")
    return None

def post_audio_to_channel_by_id(file_id, caption, title="", performer="", reply_markup=None):
    try:
        data = {
            "chat_id": CHANNEL_ID,
            "audio": file_id,
            "caption": caption,
            "title": title,
            "performer": performer,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        res = requests.post(f"{BASE_URL}/sendAudio", data=data, timeout=30)
        if res.ok:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        logger.error(f"Channel audio post error: {e}")
    return None

# --- Media Download Worker ---

def process_media_url_request(chat_id, user_id, user_name, media_url, platform, orig_text, msg_id):
    lower_text = (orig_text or "").lower()
    wants_audio = any(w in lower_text for w in ["mp3", "audio", "musiqa", "qo'shiq", "musiqasini", "audiosini"])
    wants_video = any(w in lower_text for w in ["video", "klip", "videoni"])

    if platform == "youtube" and not wants_audio and not wants_video:
        task_id = uuid.uuid4().hex[:8]
        PENDING_DOWNLOADS[task_id] = {
            "url": media_url,
            "chat_id": chat_id,
            "user_id": user_id,
            "user_name": user_name,
            "platform": platform,
            "msg_id": msg_id
        }
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🎬 Video (MP4)", "callback_data": f"dl_fmt:vid:{task_id}"},
                    {"text": "🎵 Musiqa (MP3)", "callback_data": f"dl_fmt:aud:{task_id}"}
                ]
            ]
        }
        send_message(chat_id, f"🎬 *YouTube havolasi qabul qilindi!*\n\n🔗 `{media_url}`\n\nQaysi formatda yuklab olmoqchisiz?", msg_id, reply_markup=keyboard)
        return

    mode = "audio" if wants_audio else "video"
    threading.Thread(
        target=execute_media_download_task,
        args=(chat_id, user_id, user_name, media_url, mode, platform, msg_id)
    ).start()

def execute_media_download_task(chat_id, user_id, user_name, media_url, mode, platform, msg_id, status_msg_id=None):
    mode_uz = "Musiqa (MP3)" if mode == "audio" else "Video (MP4)"
    status_text = f"⏳ *{platform.capitalize()} {mode_uz} yuklab olinmoqda...*\nIltimos, kuting..."

    if status_msg_id:
        edit_message(chat_id, status_msg_id, status_text)
    else:
        status_msg_id = send_message(chat_id, status_text, msg_id)

    stop_event = threading.Event()
    action = "record_voice" if mode == "audio" else "record_video"
    typing_thread = threading.Thread(target=keep_typing, args=(chat_id, stop_event, action))
    typing_thread.start()

    try:
        res = download_media(media_url, mode=mode)
        if not res.get("success"):
            err = res.get("error", "Noma'lum xatolik")
            if "login" in err.lower() or "restricted" in err.lower():
                msg = f"⚠️ *{platform.capitalize()} xatosi:*\nUshbu post/video yopiq (private) yoki login talab qiladi."
            else:
                msg = f"❌ *Yuklab olishda xatolik yuz berdi:*\n_{err[:200]}_"
            if status_msg_id:
                edit_message(chat_id, status_msg_id, msg)
            return

        file_path = res["file_path"]
        title = res.get("title", f"{platform.capitalize()} Media")
        duration = res.get("duration", 0)
        size_mb = res.get("size_mb", 0.0)
        performer = res.get("performer") or f"{platform.capitalize()}"
        width = res.get("width", 0)
        height = res.get("height", 0)
        actual_mode = res.get("mode", mode)

        user_caption = (
            f"🎬 <b>{html_escape(title)}</b>\n\n"
            f"💾 <b>Hajmi:</b> {size_mb:.1f} MB\n"
            f"🔗 <a href='{media_url}'>{platform.capitalize()} Havolasi</a>\n"
            f"🤖 @boburchat_bot"
        )

        user_reply_markup = None
        if actual_mode == "video":
            task_id = uuid.uuid4().hex[:8]
            PENDING_DOWNLOADS[task_id] = {
                "url": media_url,
                "video_path": file_path,
                "chat_id": chat_id,
                "title": title,
                "user_name": user_name,
                "platform": platform
            }
            user_reply_markup = {
                "inline_keyboard": [
                    [{"text": "🎵 Musiqasini (MP3) ajratish", "callback_data": f"dl_extract:{task_id}"}]
                ]
            }

        sent_to_user_ok = False
        uploaded_file_id = None

        if actual_mode == "video":
            send_res = send_telegram_video(
                chat_id=chat_id,
                video_path=file_path,
                caption=user_caption,
                reply_to_id=msg_id,
                reply_markup=user_reply_markup,
                duration=duration,
                width=width,
                height=height
            )
            if send_res.get("ok"):
                sent_to_user_ok = True
                uploaded_file_id = send_res.get("result", {}).get("video", {}).get("file_id")
        elif actual_mode == "photo":
            send_res = send_telegram_photo(
                chat_id=chat_id,
                photo_path=file_path,
                caption=user_caption,
                reply_to_id=msg_id
            )
            if send_res.get("ok"):
                sent_to_user_ok = True
                uploaded_file_id = send_res.get("result", {}).get("photo", [{}])[-1].get("file_id")
        else:
            send_res = send_telegram_audio(
                chat_id=chat_id,
                audio_path=file_path,
                caption=user_caption,
                title=title,
                performer=performer,
                reply_to_id=msg_id,
                duration=duration
            )
            if send_res.get("ok"):
                sent_to_user_ok = True
                uploaded_file_id = send_res.get("result", {}).get("audio", {}).get("file_id")

        if not sent_to_user_ok:
            doc_res = send_document(chat_id, file_path, caption=user_caption)
            if doc_res:
                sent_to_user_ok = True

        # Post to "МОЙ АЛЬБОМ" Channel (-1004342721043) with Categorization & Hashtags
        if uploaded_file_id:
            channel_caption, channel_tags = format_channel_caption(
                platform=platform,
                media_type=actual_mode,
                title=title,
                user_name=user_name,
                size_mb=size_mb,
                media_url=media_url
            )
            ch_keyboard = {
                "inline_keyboard": [
                    [
                        {"text": f"🔗 {platform.capitalize()} Asliga O‘tish", "url": media_url},
                        {"text": "🤖 Botga O‘tish", "url": "https://t.me/boburchat_bot"}
                    ]
                ]
            }
            ch_msg_id = None
            if actual_mode == "video":
                ch_msg_id = post_video_to_channel_by_id(uploaded_file_id, channel_caption, reply_markup=ch_keyboard)
            elif actual_mode == "photo":
                res_ph = requests.post(f"{BASE_URL}/sendPhoto", data={
                    "chat_id": CHANNEL_ID,
                    "photo": uploaded_file_id,
                    "caption": channel_caption,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(ch_keyboard)
                }, timeout=30)
                if res_ph.ok:
                    ch_msg_id = res_ph.json().get("result", {}).get("message_id")
            else:
                ch_msg_id = post_audio_to_channel_by_id(uploaded_file_id, channel_caption, title=title, performer=performer, reply_markup=ch_keyboard)

            # Save to SQLite Catalog database
            save_media_to_catalog(
                platform=platform,
                media_type=actual_mode,
                title=title,
                media_url=media_url,
                file_id=uploaded_file_id,
                size_mb=size_mb,
                duration=duration,
                channel_msg_id=ch_msg_id,
                user_id=user_id,
                user_name=user_name
            )

        if sent_to_user_ok and status_msg_id:
            delete_message(chat_id, status_msg_id)
        elif status_msg_id:
            edit_message(chat_id, status_msg_id, f"✅ *{mode_uz} muvaffaqiyatli yuklandi!*\n📂 *'МОЙ АЛЬБОМ'* kanaliga ham saqlandi.")

    except Exception as e:
        logger.error(f"Execution error in media download: {e}")
        if status_msg_id:
            edit_message(chat_id, status_msg_id, f"❌ Xatolik yuz berdi: {e}")
    finally:
        stop_event.set()

# --- Callback Queries ---

def handle_callback_query(callback_query):
    query_data = callback_query.get("data", "")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    user_id = callback_query.get("from", {}).get("id")
    user_name = callback_query.get("from", {}).get("first_name", "Foydalanuvchi")
    message_id = callback_query.get("message", {}).get("message_id")
    cb_id = callback_query.get("id")

    # Format selection callback
    if query_data.startswith("dl_fmt:"):
        parts = query_data.split(":")
        if len(parts) >= 3:
            fmt = parts[1]
            task_id = parts[2]
            task_info = PENDING_DOWNLOADS.get(task_id)
            if not task_info:
                requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id, "text": "⚠️ Havola eskirgan. Qaytadan yuboring.", "show_alert": True})
                return

            requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id, "text": "Yuklab olish boshlanmoqda..."})
            mode = "video" if fmt == "vid" else "audio"
            media_url = task_info.get("url")
            platform = task_info.get("platform", "youtube")
            orig_msg_id = task_info.get("msg_id")

            threading.Thread(
                target=execute_media_download_task,
                args=(chat_id, user_id, user_name, media_url, mode, platform, orig_msg_id, message_id)
            ).start()
            return

    # Extract MP3 from already downloaded video callback
    if query_data.startswith("dl_extract:"):
        parts = query_data.split(":")
        if len(parts) >= 2:
            task_id = parts[1]
            task_info = PENDING_DOWNLOADS.get(task_id)
            if not task_info or not os.path.exists(task_info.get("video_path", "")):
                requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id, "text": "⚠️ Video fayli serverda topilmadi. Qaytadan havola yuboring.", "show_alert": True})
                return

            requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id, "text": "🎵 Musiqa ajratilmoqda..."})
            vid_path = task_info["video_path"]
            title = task_info.get("title", "Audio")
            u_name = task_info.get("user_name", "Foydalanuvchi")
            media_url = task_info.get("url", "")
            platform = task_info.get("platform", "Media")

            def do_extract():
                mp3 = extract_audio_from_video(vid_path)
                if mp3 and os.path.exists(mp3):
                    cap = f"🎵 <b>{html_escape(title)}</b>\n\n🤖 @boburchat_bot"
                    send_telegram_audio(chat_id, mp3, caption=cap, title=title, performer=platform.capitalize())
                else:
                    send_message(chat_id, "❌ Musiqa ajratishda xatolik yuz berdi.")

            threading.Thread(target=do_extract).start()
            return

    # Book Module callbacks
    if query_data == "book_toc":
        requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id})
        edit_message(chat_id, message_id, "📖 *Kitob Mundarijasi (20 ta bob):*", reply_markup=get_toc_markup())
        return

    if query_data.startswith("book_ch:"):
        ch_id = int(query_data.split(":")[1])
        ch_data = get_chapter(ch_id)
        if ch_data:
            requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id})
            text = format_chapter_text(ch_data)
            edit_message(chat_id, message_id, text, reply_markup=get_chapter_nav_markup(ch_id))
        return

    if query_data == "book_pdf":
        requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id, "text": "PDF yuborilmoqda..."})
        send_document(chat_id, PDF_PATH, caption="📖 *«QALBGA YETIB BORADIGAN SO‘ZLAR»* (A5 PDF Kitob Nashri)")
        return

    if query_data == "book_html":
        requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id, "text": "Web-Kitob yuborilmoqda..."})
        send_document(chat_id, HTML_PATH, caption="🌐 *«QALBGA YETIB BORADIGAN SO‘ZLAR»* (Luxury Dark Web-Kitob)")
        return

    if query_data == "book_quote_random":
        requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id})
        quote_text, quote_id = format_random_quote()
        markup = {
            "inline_keyboard": [
                [{"text": "🔄 Boshqa iqtibos", "callback_data": "book_quote_random"}],
                [{"text": "📢 Albom kanaliga joylash", "callback_data": f"book_post_quote:{quote_id}"}]
            ]
        }
        send_message(chat_id, quote_text, reply_markup=markup)
        return

    if query_data.startswith("book_post_quote:"):
        qid = int(query_data.split(":")[1])
        quote_obj = next((q for q in TOP_100_QUOTES if q["id"] == qid), None)
        if quote_obj:
            post_text = (
                f"«{quote_obj['quote']}»\n\n"
                f"🏷 <i>#{quote_obj['topic']}</i>\n"
                f"📖 <b>«Qalbga yetib boradigan so‘zlar»</b>\n"
                f"🤖 @boburchat_bot"
            )
            requests.post(f"{BASE_URL}/sendMessage", data={
                "chat_id": CHANNEL_ID,
                "text": post_text,
                "parse_mode": "HTML"
            }, timeout=15)
            requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id, "text": "✅ 'МОЙ АЛЬБОМ' kanaliga joylandi!", "show_alert": True})
        return

    # Album Catalog & Categorization Callbacks
    if query_data == "cat_back_main":
        requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id})
        stats = get_catalog_stats()
        total = sum(stats.values())
        albom_text = (
            f"📁 <b>«МОЙ АЛЬБОМ» — TARTIBLANGAN BO‘LIMLAR</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Kanalga yuklangan barcha fayllar toifalar bo‘yicha tartiblangan.\n\n"
            f"Qaysi bo‘limdagi fayllarni ochmoqchisiz?\n"
            f"Istalgan bo‘lim ustiga bosing:\n\n"
            f"📊 <b>Bazada saqlangan jami fayllar:</b> {total} ta"
        )
        edit_message(chat_id, message_id, albom_text, reply_markup=get_album_categories_markup())
        return

    if query_data == "cat_refresh_pinned":
        cat_text = format_catalog_message()
        res = requests.post(f"{BASE_URL}/sendMessage", data={
            "chat_id": CHANNEL_ID,
            "text": cat_text,
            "parse_mode": "HTML"
        }, timeout=20)
        if res.ok:
            pin_id = res.json().get("result", {}).get("message_id")
            requests.post(f"{BASE_URL}/pinChatMessage", data={
                "chat_id": CHANNEL_ID,
                "message_id": pin_id,
                "disable_notification": True
            }, timeout=15)
            requests.post(f"{BASE_URL}/answerCallbackQuery", data={
                "callback_query_id": cb_id,
                "text": "✅ Kanal mundarijasi yangilandi va qadaldi!",
                "show_alert": True
            })
        else:
            requests.post(f"{BASE_URL}/answerCallbackQuery", data={
                "callback_query_id": cb_id,
                "text": "Mundarijani yangilashda xatolik!",
                "show_alert": True
            })
        return

    if query_data.startswith("cat_view:"):
        parts = query_data.split(":")
        p_platform = parts[1]
        p_type = parts[2]
        p_page = int(parts[3])
        v_text, v_markup = format_category_view(p_platform, p_type, page=p_page, channel_id=CHANNEL_ID)
        edit_message(chat_id, message_id, v_text, reply_markup=v_markup)
        requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id})
        return

    if query_data.startswith("cat_resend:"):
        item_id = int(query_data.split(":")[1])
        item = get_media_item_by_id(item_id)
        if not item or not item.get("file_id"):
            requests.post(f"{BASE_URL}/answerCallbackQuery", data={
                "callback_query_id": cb_id,
                "text": "⚠️ Fayl bazada topilmadi!",
                "show_alert": True
            })
            return

        requests.post(f"{BASE_URL}/answerCallbackQuery", data={
            "callback_query_id": cb_id,
            "text": "📥 Fayl yuborilmoqda..."
        })
        resend_caption = (
            f"🎬 <b>{html_escape(item['title'])}</b>\n\n"
            f"💾 <b>Hajmi:</b> {item['size_mb']:.1f} MB\n"
            f"📁 <b>Bo‘lim:</b> #{item['platform'].capitalize()}\n"
            f"🤖 @boburchat_bot"
        )
        if item["media_type"] == "video":
            requests.post(f"{BASE_URL}/sendVideo", data={
                "chat_id": chat_id,
                "video": item["file_id"],
                "caption": resend_caption,
                "parse_mode": "HTML",
                "supports_streaming": True
            }, timeout=30)
        elif item["media_type"] == "audio":
            requests.post(f"{BASE_URL}/sendAudio", data={
                "chat_id": chat_id,
                "audio": item["file_id"],
                "caption": resend_caption,
                "title": item["title"],
                "parse_mode": "HTML"
            }, timeout=30)
        elif item["media_type"] == "photo":
            requests.post(f"{BASE_URL}/sendPhoto", data={
                "chat_id": chat_id,
                "photo": item["file_id"],
                "caption": resend_caption,
                "parse_mode": "HTML"
            }, timeout=30)
        return

    # Binance Callbacks
    if BINANCE_AVAILABLE and query_data.startswith("binance_"):
        requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id})
        if query_data in ["binance_tab_balance", "binance_refresh_balance", "binance_refresh_main"]:
            edit_message(chat_id, message_id, get_account_summary_text(), reply_markup=get_binance_markup("balance"), parse_mode="HTML")
        elif query_data in ["binance_tab_prices", "binance_refresh_prices"]:
            edit_message(chat_id, message_id, get_crypto_prices_text(), reply_markup=get_binance_markup("prices"), parse_mode="HTML")
        elif query_data in ["binance_tab_orders", "binance_refresh_orders"]:
            edit_message(chat_id, message_id, get_open_orders_text(), reply_markup=get_binance_markup("orders"), parse_mode="HTML")
        return

    requests.post(f"{BASE_URL}/answerCallbackQuery", data={"callback_query_id": cb_id})

# --- Message Handler ---

def handle_message(message):
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    user_id = message.get("from", {}).get("id")
    first_name = message.get("from", {}).get("first_name", "")
    last_name = message.get("from", {}).get("last_name", "")
    user_name = f"{first_name} {last_name}".strip() or message.get("from", {}).get("username", "Foydalanuvchi")
    msg_id = message.get("message_id")
    caption = message.get("caption", "").strip()
    text = message.get("text", "").strip()

    # Priority 1: Media Downloader (Instagram, YouTube, TikTok, etc.)
    media_url, platform = extract_media_url(text or caption)
    if media_url:
        logger.info(f"Media URL detected: {media_url} from {user_name} ({user_id})")
        process_media_url_request(chat_id, user_id, user_name, media_url, platform, text or caption, msg_id)
        return

    # Non-admin users can only use media downloader
    if user_id != ADMIN_CHAT_ID:
        send_message(chat_id, (
            "👋 *Salom! Men Instagram va YouTube Media Yuklovchi botman.*\n\n"
            "Menga *Instagram* (Reel, Video) yoki *YouTube* (Video, Shorts, Musiqa) havolasini yuboring — "
            "men uni eng yuqori sifatda sizga yuklab beraman!"
        ), msg_id)
        return

    # Commands & Buttons
    if text in ["/start", "/help", "ℹ️ Yordam"]:
        help_text = (
            "🤖 *Salom, Bobur! @boburchat_bot (24/7 Cloud Edition)*\n\n"
            "⚡ Bot hozirda Render.com bulutli serverida uzluksiz 24/7 ishlamoqda.\n\n"
            "📥 *Media Yuklovchi:*\n"
            "• Istalgan Instagram (Reels, Video) yoki YouTube havolasini yuboring.\n"
            "• Video yoki MP3 musiqani yuklab beradi va avtomatik 'МОЙ АЛЬБОМ' kanaliga saqlaydi!\n\n"
            "📖 *Kitob («Qalbga yetib boradigan so‘zlar»):*\n"
            "• `/kitob` — 20 bobli interaktiv falsafiy kitob\n"
            "• `/iqtibos` — Tasodifiy qalb iqtibosi\n\n"
            "💻 *Cloud Terminal:*\n"
            "• `/sh <buyruq>` — Serverda buyruq bajarish\n"
            "• `/status` — Server va bot holati\n\n"
            "🟡 *Binance & Kripto:*\n"
            "• `/binance` — Portfel, hisob holati va hamyon balansi\n"
            "• `/price <coin>` — Istalgan kripto narxi (masalan: `/price ton` yoki `/price btc`)\n\n"
            "💬 *AI Savol-Javob:* Istalgan savolingizni yozing, Google Gemini AI bir zumda javob beradi!"
        )
        send_message(chat_id, help_text, msg_id)
        return

    if text in ["📥 Media Yuklovchi", "📥 Media Yuklovchi (Instagram/YouTube)", "/download", "yuklovchi"]:
        send_message(chat_id, (
            "📥 *Instagram va YouTube Media Yuklovchi (24/7 Cloud)*\n\n"
            "Menga *Instagram* (Reel, Video, Post) yoki *YouTube* (Video, Shorts, Musiqa) havolasini yuboring.\n\n"
            "✨ *Imkoniyatlar:*\n"
            "• 🎬 Videoni eng sifatli MP4 formatida yuklab berish\n"
            "• 🎵 Faqat musiqasini (MP3) ajratib olish\n"
            "• 📂 Barcha yuklangan fayllar avtomatik *'МОЙ АЛЬБОМ'* kanaliga toifalab saqlanadi!"
        ), msg_id)
        return

    if text in ["📁 Albom Bo‘limlari", "📁 Albom Bo'limlari", "/album", "/albom", "/catalog", "/mundarija"]:
        stats = get_catalog_stats()
        total = sum(stats.values())
        albom_text = (
            f"📁 <b>«МОЙ АЛЬБОМ» — TARTIBLANGAN BO‘LIMLAR</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Kanalga yuklangan barcha fayllar toifalar bo‘yicha tartiblangan.\n\n"
            f"Qaysi bo‘limdagi fayllarni ochmoqchisiz?\n"
            f"Istalgan bo‘lim ustiga bosing:\n\n"
            f"📊 <b>Bazada saqlangan jami fayllar:</b> {total} ta"
        )
        send_message(chat_id, albom_text, msg_id, reply_markup=get_album_categories_markup())
        return

    if text in ["/kitob", "📖 Qalbga yetib boradigan so‘zlar"]:
        send_message(chat_id, (
            f"📖 <b>«{BOOK_INFO['title']}»</b>\n\n"
            f"<i>{BOOK_INFO['subtitle']}</i>\n\n"
            f"✍️ <b>Muallif:</b> {BOOK_INFO['author']}\n"
            f"📜 <b>Tarkibi:</b> 20 ta bob, 100 ta sara hikmat, 10 ta hayotiy xulosa.\n\n"
            "Quyidagi tugmalar orqali kitobni o‘qishingiz yoki to‘liq formatda yuklab olishingiz mumkin:"
        ), msg_id, reply_markup=get_main_book_menu_markup())
        return

    if text in ["/iqtibos", "🎲 Qalb iqtibosi"]:
        quote_text, quote_id = format_random_quote()
        markup = {
            "inline_keyboard": [
                [{"text": "🔄 Boshqa iqtibos", "callback_data": "book_quote_random"}],
                [{"text": "📢 Albom kanaliga joylash", "callback_data": f"book_post_quote:{quote_id}"}]
            ]
        }
        send_message(chat_id, quote_text, msg_id, reply_markup=markup)
        return

    if text in ["/status", "📊 Tizim holati"]:
        try:
            free_proc = subprocess.run(["free", "-m"], capture_output=True, text=True)
            df_proc = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
            status_text = (
                "☁️ *Server Holati (Render.com Cloud):*\n"
                f"• Python: `{sys.version.split()[0]}`\n"
                f"• Node.js: `{shutil.which('node') or 'Yo\'q'}`\n"
                f"• FFmpeg: `{shutil.which('ffmpeg') or 'Yo\'q'}`\n"
                f"• Gemini AI: `{'Faol ✅' if ai_model else 'O\'chiq ❌'}`\n"
                f"• Status: 24/7 Online\n\n"
                f"```\n{free_proc.stdout[:300]}\n```\n"
                f"```\n{df_proc.stdout[:300]}\n```"
            )
        except Exception as se:
            status_text = f"☁️ *Server Holati:* 24/7 Online ({se})"
        send_message(chat_id, status_text, msg_id)
        return

    # Binance & Crypto handlers
    if BINANCE_AVAILABLE and text in ["/binance", "/crypto", "🟡 Binance Portfel", "🟡 Binance", "💰 Binance Balans", "📈 Kripto"]:
        send_message(chat_id, get_account_summary_text(), msg_id, reply_markup=get_binance_markup("balance"), parse_mode="HTML")
        return

    if BINANCE_AVAILABLE and (text.startswith("/price ") or text.startswith("/narx ")):
        coin_sym = text.split(maxsplit=1)[1]
        send_message(chat_id, get_crypto_prices_text(coin_sym), msg_id, reply_markup=get_binance_markup("prices"), parse_mode="HTML")
        return

    # Shell Command execution
    if text.startswith("/sh "):
        cmd_str = text[4:].strip()
        status_id = send_message(chat_id, f"⚡ *Bajarilmoqda:* `{cmd_str}`", msg_id)
        try:
            res = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=60)
            out = res.stdout.strip()
            err = res.stderr.strip()
            result_text = f"💻 *Natija:*\n```text\n{(out or err or 'Bajarildi (javob bo\'sh)')[:3900]}\n```"
            edit_message(chat_id, status_id, result_text)
        except Exception as e:
            edit_message(chat_id, status_id, f"❌ *Xatolik:* `{e}`")
        return

    # AI Chat via Google Gemini
    if ai_model:
        stop_event = threading.Event()
        typing_thread = threading.Thread(target=keep_typing, args=(chat_id, stop_event))
        typing_thread.start()
        try:
            response = ai_model.generate_content(text)
            reply = response.text if response else "(Javob bo'sh)"
            send_message(chat_id, reply, msg_id)
        except Exception as aie:
            logger.error(f"Gemini AI error: {aie}")
            send_message(chat_id, f"⚠️ *AI Xatosi:* {aie}", msg_id)
        finally:
            stop_event.set()
    else:
        send_message(chat_id, f"Siz yozdingiz: {text}\n\n💡 Instagram yoki YouTube havolasini yuborsangiz, videoni yuklab beraman!", msg_id)

# --- Telegram Polling Loop ---

def telegram_polling_loop():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not configured! Telegram polling skipped.")
        return
    logger.info("Starting Telegram Bot Polling (24/7 Cloud)...")
    # Delete webhook if set
    try:
        requests.get(f"{BASE_URL}/deleteWebhook", timeout=10)
    except Exception:
        pass

    offset = 0
    while True:
        try:
            res = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 25}, timeout=35)
            if res.ok:
                updates = res.json().get("result", [])
                for u in updates:
                    offset = u["update_id"] + 1
                    if "message" in u:
                        threading.Thread(target=handle_message, args=(u["message"],)).start()
                    elif "callback_query" in u:
                        threading.Thread(target=handle_callback_query, args=(u["callback_query"],)).start()
            else:
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Polling loop notice: {e}")
            time.sleep(3)

# --- FastAPI Web Service (for Render keep-alive & health check) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_catalog_db()
    t = threading.Thread(target=telegram_polling_loop, daemon=True)
    t.start()
    logger.info("Bot polling thread started in background (Catalog DB initialized).")
    yield

app = FastAPI(title="@boburchat_bot Cloud Service", lifespan=lifespan)

@app.get("/")
def index():
    return {
        "bot": "@boburchat_bot",
        "status": "online",
        "server": "Render.com Cloud",
        "features": [
            "Instagram & YouTube Media Downloader",
            "Auto sync to 'МОЙ АЛЬБОМ' Channel (-1004342721043)",
            "«Qalbga yetib boradigan so‘zlar» Book Module",
            "Google Gemini AI Assistant"
        ]
    }

@app.api_route("/health", methods=["GET", "HEAD"])
def health(request: Request):
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "bot_online": bool(BOT_TOKEN)
    })

@app.get("/api/binance_debug")
def binance_debug():
    import traceback
    result = {}
    try:
        import binance_module
        result["base_url"] = binance_module.BASE_URL
        result["api_key_prefix"] = binance_module.API_KEY[:8] + "..." if binance_module.API_KEY else "EMPTY"
        result["secret_key_len"] = len(binance_module.SECRET_KEY) if binance_module.SECRET_KEY else 0
        
        # Test 1: server time
        try:
            t = binance_module.get_server_time()
            result["server_time"] = t
        except Exception as te:
            result["server_time_err"] = str(te)

        # Test 2: direct ping to binance.com
        try:
            d_res = requests.get("https://api.binance.com/api/v3/ping", timeout=5)
            result["direct_binance_ping"] = {"status": d_res.status_code, "text": d_res.text}
        except Exception as de:
            result["direct_binance_ping_err"] = str(de)

        # Test 3: worker ping
        try:
            w_res = requests.get("https://binance-proxy.boburjonnushonov.workers.dev/api/v3/ping", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            result["worker_binance_ping"] = {"status": w_res.status_code, "text": w_res.text}
        except Exception as we:
            result["worker_binance_ping_err"] = str(we)

        # Test 4: account call with details
        acc_call = binance_module.binance_api_call("/api/v3/account", signed=True)
        result["account_result"] = acc_call
        result["last_error"] = getattr(binance_module, "LAST_ERROR", None)
    except Exception as e:
        result["fatal"] = str(e)
        result["traceback"] = traceback.format_exc()
    return JSONResponse(content=result)

# --- Telegram Mini App & Catalog API Routes ---

WEBAPP_HTML_PATH = os.path.join(os.path.dirname(__file__), "album_webapp.html")

@app.get("/app", response_class=HTMLResponse)
@app.get("/album", response_class=HTMLResponse)
def serve_webapp():
    if os.path.exists(WEBAPP_HTML_PATH):
        with open(WEBAPP_HTML_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>Albom Ilovasi yuklanmadi</h1>", status_code=404)

@app.get("/api/catalog")
def api_catalog(platform: str = None, media_type: str = None, search: str = None, limit: int = 80, offset: int = 0):
    stats = get_catalog_stats()
    items = get_media_items(platform=platform, media_type=media_type, search=search, limit=limit, offset=offset)
    return JSONResponse(content={
        "status": "ok",
        "stats": stats,
        "items": items,
        "quotes": TOP_100_QUOTES
    })

@app.post("/api/action/resend")
async def api_action_resend(request: Request):
    try:
        body = await request.json()
        item_id = body.get("item_id")
        chat_id = body.get("chat_id") or ADMIN_CHAT_ID

        item = get_media_item_by_id(item_id)
        if not item or not item.get("file_id"):
            return JSONResponse(content={"ok": False, "error": "Fayl topilmadi"}, status_code=404)

        caption = (
            f"🎬 <b>{html_escape(item['title'])}</b>\n\n"
            f"💾 <b>Hajmi:</b> {item['size_mb']:.1f} MB\n"
            f"📁 <b>Bo‘lim:</b> #{item['platform'].capitalize()}\n"
            f"🤖 @boburchat_bot (Albom Ilovasi)"
        )

        sent_ok = False
        if item["media_type"] == "video":
            res = requests.post(f"{BASE_URL}/sendVideo", data={
                "chat_id": chat_id,
                "video": item["file_id"],
                "caption": caption,
                "parse_mode": "HTML",
                "supports_streaming": True
            }, timeout=30)
            sent_ok = res.ok
        elif item["media_type"] == "audio":
            res = requests.post(f"{BASE_URL}/sendAudio", data={
                "chat_id": chat_id,
                "audio": item["file_id"],
                "caption": caption,
                "title": item["title"],
                "parse_mode": "HTML"
            }, timeout=30)
            sent_ok = res.ok
        elif item["media_type"] == "photo":
            res = requests.post(f"{BASE_URL}/sendPhoto", data={
                "chat_id": chat_id,
                "photo": item["file_id"],
                "caption": caption,
                "parse_mode": "HTML"
            }, timeout=30)
            sent_ok = res.ok

        return JSONResponse(content={"ok": sent_ok})
    except Exception as e:
        logger.error(f"Error in api_action_resend: {e}")
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
