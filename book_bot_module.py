# -*- coding: utf-8 -*-
"""
«QALBGA YETIB BORADIGAN SO‘ZLAR»
Telegram Bot (@boburchat_bot) Integratsiya Moduli
"""

import os
import sys
import json
import random
import logging
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOK_DIR = os.getenv("BOOK_DIR", BASE_DIR)
if BOOK_DIR not in sys.path:
    sys.path.append(BOOK_DIR)

from book import BOOK_INFO, AUTHOR_NOTE, FINAL_LETTER, LIFE_CONCLUSIONS, ALL_CHAPTERS, TOP_100_QUOTES, get_chapter

PDF_PATH = os.path.join(BOOK_DIR, "qalbga_yetib_boradigan_sozlar.pdf")
HTML_PATH = os.path.join(BOOK_DIR, "qalbga_yetib_boradigan_sozlar.html")

def get_main_book_menu_markup():
    """Kitob asosiy menyusi inline klaviaturasi"""
    return {
        "inline_keyboard": [
            [
                {"text": "📚 Boblarni o‘qish (1-20)", "callback_data": "book_toc_1"},
                {"text": "🎲 Qalb iqtibosi", "callback_data": "book_random_quote"}
            ],
            [
                {"text": "📥 PDF Kitobni yuklash", "callback_data": "book_download_pdf"},
                {"text": "🌐 HTML Kitobni yuklash", "callback_data": "book_download_html"}
            ],
            [
                {"text": "💡 10 ta oltin xulosa", "callback_data": "book_conclusions"},
                {"text": "📑 100 ta sara iqtibos", "callback_data": "book_quotes_list_1"}
            ],
            [
                {"text": "✉️ Muallifdan so‘z", "callback_data": "book_author_note"},
                {"text": "💌 Yakuniy maktub", "callback_data": "book_final_letter"}
            ],
            [
                {"text": "📢 Kanalga tasodifiy iqtibos joylash", "callback_data": "book_post_to_channel"}
            ]
        ]
    }

def get_toc_markup(page=1):
    """Mundarija inline klaviaturasi (har sahifada 10 tadan bob)"""
    keyboard = []
    start_idx = (page - 1) * 10
    end_idx = min(start_idx + 10, len(ALL_CHAPTERS))

    for i in range(start_idx, end_idx, 2):
        row = []
        ch1 = ALL_CHAPTERS[i]
        title1 = f"{ch1['id']}. {ch1['title'].split(':')[-1].strip()[:18]}"
        row.append({"text": title1, "callback_data": f"book_ch_{ch1['id']}"})

        if i + 1 < end_idx:
            ch2 = ALL_CHAPTERS[i + 1]
            title2 = f"{ch2['id']}. {ch2['title'].split(':')[-1].strip()[:18]}"
            row.append({"text": title2, "callback_data": f"book_ch_{ch2['id']}"})
        keyboard.append(row)

    # Navigatsiya
    nav_row = []
    if page == 1:
        nav_row.append({"text": "Keyingisi (11-20) ➡️", "callback_data": "book_toc_2"})
    else:
        nav_row.append({"text": "⬅️ Oldingisi (1-10)", "callback_data": "book_toc_1"})
    keyboard.append(nav_row)

    keyboard.append([{"text": "🔙 Asosiy kitob menyusi", "callback_data": "book_main_menu"}])
    return {"inline_keyboard": keyboard}

def get_chapter_nav_markup(chapter_id):
    """Bob o'qish sahifasi navigatsiyasi"""
    keyboard = []
    nav_row = []
    if chapter_id > 1:
        nav_row.append({"text": "⬅️ Oldingi bob", "callback_data": f"book_ch_{chapter_id - 1}"})
    nav_row.append({"text": "📋 Mundarija", "callback_data": "book_toc_1" if chapter_id <= 10 else "book_toc_2"})
    if chapter_id < len(ALL_CHAPTERS):
        nav_row.append({"text": "Keyingi bob ➡️", "callback_data": f"book_ch_{chapter_id + 1}"})
    keyboard.append(nav_row)

    keyboard.append([
        {"text": "🎲 Tasodifiy iqtibos", "callback_data": "book_random_quote"},
        {"text": "📢 Kanalga ulashish", "callback_data": f"book_share_ch_{chapter_id}"}
    ])
    keyboard.append([{"text": "🔙 Kitob menyusi", "callback_data": "book_main_menu"}])
    return {"inline_keyboard": keyboard}

def format_chapter_text(ch):
    """Bobni Telegram uchun chiroyli qilib formatlash"""
    text = (
        f"📖 *{ch['title']}*\n"
        f"_{ch['subtitle']}_\n\n"
        f"✨ *Epigraf:*\n_{ch['epigraph']}_\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"*{ch['intro'].strip()}*\n\n"
        f"📜 *Hikoyat: {ch['story_title']}*\n"
        f"{ch['story_text'].strip()}\n\n"
        f"🧠 *Falsafiy mushohada:*\n"
        f"{ch['deep_thoughts'].strip()}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✨ *Bobning Oltin Iqtiboslari:*\n"
    )
    for q in ch['quotes'][:4]:
        text += f"• _{q}_\n"

    text += (
        f"\n❓ *Qalb savoli:*\n"
        f"«_{ch['question']}_»\n\n"
        f"💡 *Hayotiy xulosa:*\n"
        f"*{ch['conclusion']}*"
    )
    return text

def format_random_quote():
    """Tasodifiy iqtibos matni"""
    q = random.choice(TOP_100_QUOTES)
    text = (
        f"✨ *QALBGA YETIB BORADIGAN SO‘ZLAR* ✨\n\n"
        f"💎 _{q}_\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"«_Bu shunchaki o‘qiladigan kitob emas. Bu — inson o‘z qalbini tinglashni boshlaydigan kitob._»"
    )
    return text

def send_book_document(base_url, chat_id, file_path, caption=""):
    """Hujjat yuborish (PDF / HTML)"""
    if not os.path.exists(file_path):
        return False
    try:
        url = f"{base_url}/sendDocument"
        with open(file_path, "rb") as doc_file:
            files = {"document": doc_file}
            data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
            res = requests.post(url, data=data, files=files, timeout=60)
            return res.ok
    except Exception as e:
        logging.error(f"Error sending book document: {e}")
        return False

def post_quote_to_channel(base_url, channel_id, custom_text=None):
    """Kanalga iqtibos yuborish"""
    try:
        if not custom_text:
            custom_text = format_random_quote()
        url = f"{base_url}/sendMessage"
        payload = {
            "chat_id": channel_id,
            "text": custom_text,
            "parse_mode": "Markdown"
        }
        res = requests.post(url, data=payload, timeout=15)
        return res.ok
    except Exception as e:
        logging.error(f"Error posting quote to channel: {e}")
        return False
