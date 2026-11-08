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

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
        [{"text": "📥 Media Yuklovchi"}, {"text": "📖 Qalbga yetib boradigan so‘zlar"}],
        [{"text": "🎲 Qalb iqtibosi"}, {"text": "📊 Tizim holati"}],
        [{"text": "ℹ️ Yordam"}]
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

def send_message(chat_id, text, reply_to_id=None, reply_markup=None):
    if not text:
        return None
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(reply_markup or MAIN_KEYBOARD)
    }
    if reply_to_id:
        payload["reply_to_message_id"] = reply_to_id
    try:
        res = requests.post(f"{BASE_URL}/sendMessage", data=payload, timeout=20)
        if res.ok:
            return res.json().get("result", {}).get("message_id")
        # Retry without markdown
        payload.pop("parse_mode", None)
        res = requests.post(f"{BASE_URL}/sendMessage", data=payload, timeout=20)
        if res.ok:
            return res.json().get("result", {}).get("message_id")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
    return None

def edit_message(chat_id, message_id, text, reply_markup=None):
    if not text or not message_id:
        return
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
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

def post_video_to_channel_by_id(file_id, caption):
    try:
        res = requests.post(f"{BASE_URL}/sendVideo", data={
            "chat_id": CHANNEL_ID,
            "video": file_id,
            "caption": caption,
            "parse_mode": "HTML",
            "supports_streaming": True
        }, timeout=30)
        return res.ok
    except Exception as e:
        logger.error(f"Channel video post error: {e}")
        return False

def post_audio_to_channel_by_id(file_id, caption, title="", performer=""):
    try:
        res = requests.post(f"{BASE_URL}/sendAudio", data={
            "chat_id": CHANNEL_ID,
            "audio": file_id,
            "caption": caption,
            "title": title,
            "performer": performer,
            "parse_mode": "HTML"
        }, timeout=30)
        return res.ok
    except Exception as e:
        logger.error(f"Channel audio post error: {e}")
        return False

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
        args=(chat_id, user_name, media_url, mode, platform, msg_id)
    ).start()

def execute_media_download_task(chat_id, user_name, media_url, mode, platform, msg_id, status_msg_id=None):
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

        # Post to "МОЙ АЛЬБОМ" Channel (-1004342721043)
        if uploaded_file_id:
            channel_caption = (
                f"📥 <b>{html_escape(title)}</b>\n\n"
                f"👤 <b>Yuboruvchi:</b> {html_escape(user_name)}\n"
                f"💾 <b>Hajmi:</b> {size_mb:.1f} MB\n"
                f"🔗 <a href='{media_url}'>{platform.capitalize()}</a>\n"
                f"🤖 @boburchat_bot orqali yuklandi (24/7 Cloud)"
            )
            if actual_mode == "video":
                post_video_to_channel_by_id(uploaded_file_id, channel_caption)
            elif actual_mode == "photo":
                requests.post(f"{BASE_URL}/sendPhoto", data={
                    "chat_id": CHANNEL_ID,
                    "photo": uploaded_file_id,
                    "caption": channel_caption,
                    "parse_mode": "HTML"
                }, timeout=30)
            else:
                post_audio_to_channel_by_id(uploaded_file_id, channel_caption, title=title, performer=performer)

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
                args=(chat_id, user_name, media_url, mode, platform, orig_msg_id, message_id)
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
            "• 📂 Barcha yuklangan fayllar avtomatik *'МОЙ АЛЬБОМ'* kanaliga saqlanadi!"
        ), msg_id)
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

app = FastAPI(title="@boburchat_bot Cloud Service")

@app.on_event("startup")
def startup_event():
    # Start polling loop in daemon background thread
    t = threading.Thread(target=telegram_polling_loop, daemon=True)
    t.start()
    logger.info(f"Bot polling thread started. HTTP Web server listening on port {PORT}")

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

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "bot_online": True
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
