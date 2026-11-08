import os
import sys
import json
import time
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==========================================================
# SOZLAMALAR VA ENVIRONMENT VARIABLES
# ==========================================================
API_ID = int(os.getenv("TELEGRAM_API_ID", "31163417"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "ef7338d736ea3037bac99ffa66e6c577")
SESSION_STRING = os.getenv("TELEGRAM_STRING_SESSION", "").strip()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "allowed_contacts.json")

# Telethon Mijozini yaratish (StringSession yoki fayl orqali)
if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
else:
    session_path = os.path.join(BASE_DIR, "my_userbot")
    client = TelegramClient(session_path, API_ID, API_HASH)

# ==========================================================
# KONFIGURATSIYA BOSHQARUVI
# ==========================================================
DEFAULT_CONFIG = {
    "allowed_users": [],
    "auto_reply": False,
    "custom_persona": "",
    "album_settings": {
        "enabled": True,
        "channel_id": int(os.getenv("ALBUM_CHANNEL_ID", "-1004342721043")),
        "allowed_users": [
            {"id": 8577897810, "name": "Bobur Men", "username": "Bobur19981117"},
            {"id": 7531752464, "name": "❤️❤️❤️", "username": ""},
            {"id": 7820432591, "name": "Onam", "username": ""},
            {"id": 8909974827, "name": "Baxodir", "username": "bahodir7975"},
            {"id": 1041716231, "name": "OTABEK", "username": ""},
            {"id": 6377510094, "name": "Otajonim", "username": ""}
        ],
        "include_all_allowed": False
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        env_contacts = os.getenv("ALLOWED_CONTACTS_JSON")
        if env_contacts:
            try:
                cfg = json.loads(env_contacts)
                save_config(cfg)
                return cfg
            except Exception:
                pass
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if "album_settings" not in cfg:
                cfg["album_settings"] = DEFAULT_CONFIG["album_settings"]
            return cfg
    except Exception as e:
        print(f"Config o'qish xatosi: {e}")
        return DEFAULT_CONFIG

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Config saqlash xatosi: {e}")

# ==========================================================
# MEDIA VA BIR MARTALIK (VIEW ONCE) TEKSHIRUVI
# ==========================================================
def check_media_type(message):
    is_photo = bool(message.photo)
    is_video_note = False
    is_video = False
    is_voice = bool(getattr(message, 'voice', False))
    is_audio = bool(getattr(message, 'audio', False))

    if getattr(message, 'video_note', False):
        is_video_note = True
    elif message.media and hasattr(message.media, 'document'):
        doc = message.media.document
        for attr in getattr(doc, 'attributes', []):
            if attr.__class__.__name__ == 'DocumentAttributeVideo':
                if getattr(attr, 'round_message', False):
                    is_video_note = True
                else:
                    is_video = True

    if not is_video_note and bool(message.video) and not is_voice and not is_audio:
        is_video = True

    ttl_seconds = None
    if message.media:
        ttl_seconds = getattr(message.media, 'ttl_seconds', None)
    if not ttl_seconds:
        ttl_seconds = getattr(message, 'ttl_period', None)

    is_view_once = bool(ttl_seconds)
    return is_photo, is_video, is_video_note, is_view_once, ttl_seconds

# ==========================================================
# ALBOMGA UZATISH (AVTOMATIK KANALGA YUKLASH)
# ==========================================================
async def forward_to_album(event, sender, channel_id):
    is_photo, is_video, is_video_note, is_view_once, ttl_seconds = check_media_type(event.message)
    sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or str(sender.id)

    if is_video_note:
        media_name = "dumaloq video xabar (krujok)"
    elif is_photo:
        media_name = "rasm"
    elif is_video:
        media_name = "video"
    else:
        media_name = "media"

    tag = f" ⏱ [Bir martalik / View Once ({ttl_seconds}s)]" if is_view_once else ""

    try:
        try:
            target = await client.get_entity(channel_id)
        except Exception:
            target = None
            async for dialog in client.iter_dialogs(limit=50):
                if dialog.id == channel_id:
                    target = dialog.entity
                    break
            if not target:
                target = channel_id

        temp_dir = os.path.join(BASE_DIR, "temp_downloads")
        os.makedirs(temp_dir, exist_ok=True)

        if is_view_once:
            temp_file = os.path.join(temp_dir, f"viewonce_{int(time.time())}_{event.id}")
            downloaded = await client.download_media(event.message, file=temp_file)
            if downloaded and os.path.exists(downloaded):
                try:
                    caption = f"⏱ [Bir martalik {media_name}] {sender_name} dan"
                    if is_video_note:
                        await client.send_file(target, downloaded, video_note=True)
                    elif is_video:
                        await client.send_file(target, downloaded, video_note=False, caption=caption)
                    else:
                        await client.send_file(target, downloaded, caption=caption)
                    print(f"🔥 [МОЙ АЛЬБОМ] {sender_name} dan kelgan BIR MARTALIK {media_name} saqlandi!")
                finally:
                    if os.path.exists(downloaded):
                        try:
                            os.remove(downloaded)
                        except Exception:
                            pass
                return

        # Oddiy media: avval forward qilib ko'ramiz
        try:
            await client.forward_messages(target, event.message)
            print(f"✅ [МОЙ АЛЬБОМ] {sender_name} dan kelgan {media_name}{tag} uzatildi.")
        except Exception as forward_err:
            print(f"⚠️ Forward taqiqlangan ({forward_err}), yuklab olib yuborilmoqda...")
            temp_file = os.path.join(temp_dir, f"media_{int(time.time())}_{event.id}")
            downloaded = await client.download_media(event.message, file=temp_file)
            if downloaded and os.path.exists(downloaded):
                try:
                    if is_video_note:
                        await client.send_file(target, downloaded, video_note=True)
                    elif is_video:
                        await client.send_file(target, downloaded, video_note=False)
                    else:
                        await client.send_file(target, downloaded)
                    print(f"✅ [МОЙ АЛЬБОМ] {sender_name} dan kelgan {media_name} kanalga yuklandi.")
                finally:
                    if os.path.exists(downloaded):
                        try:
                            os.remove(downloaded)
                        except Exception:
                            pass
            else:
                raise forward_err

    except Exception as e:
        print(f"❌ [МОЙ АЛЬБОМ] Xatolik: {e}")

# ==========================================================
# TELETHON HANDLERLARI
# ==========================================================
@client.on(events.NewMessage(incoming=True))
async def incoming_messages_handler(event):
    if not event.is_private:
        return

    sender = await event.get_sender()
    if not sender or getattr(sender, 'bot', False) or getattr(sender, 'is_self', False):
        return

    cfg = load_config()
    album_cfg = cfg.get("album_settings", {})
    if album_cfg.get("enabled", True):
        album_allowed = album_cfg.get("allowed_users", [])
        is_album_allowed = any(u.get("id") == sender.id for u in album_allowed)
        if not is_album_allowed and sender.username:
            is_album_allowed = any(u.get("username", "").lower() == sender.username.lower() for u in album_allowed)

        if is_album_allowed:
            is_photo, is_video, is_video_note, _, _ = check_media_type(event.message)
            if is_photo or is_video or is_video_note:
                ch_id = album_cfg.get("channel_id", -1004342721043)
                asyncio.create_task(forward_to_album(event, sender, ch_id))

@client.on(events.NewMessage(outgoing=True))
async def outgoing_handler(event):
    text = (event.raw_text or "").strip()
    me = await client.get_me()
    is_saved = (event.chat_id == me.id)
    text_lower = text.lower()

    is_cmd = False
    cmd = ""
    args = ""

    if text.startswith("!"):
        is_cmd = True
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""
    elif text_lower.startswith("agent ") or text_lower == "agent":
        is_cmd = True
        cmd = "!agent"
        args = text[5:].strip() if len(text) > 5 else "menyu"
    elif text_lower in ["ruxsat"] and event.is_private and not is_saved:
        is_cmd = True
        cmd = "!agent"
        args = "ruxsat"
    elif text_lower in ["stop", "toxtat", "to'xtat"] and event.is_private and not is_saved:
        is_cmd = True
        cmd = "!agent"
        args = "stop"
    elif text_lower in ["jadval", "royxat", "ro'yxat"]:
        is_cmd = True
        cmd = "!agent"
        args = "jadval"
    elif text_lower in ["menyu", "menu"]:
        is_cmd = True
        cmd = "!agent"
        args = "menyu"

    if not is_cmd:
        return

    async def respond(msg_text, auto_delete=True, delay=4):
        await event.edit(msg_text)
        if auto_delete and not is_saved:
            await asyncio.sleep(delay)
            try:
                await event.delete(revoke=True)
            except Exception:
                pass

    if cmd in ["!agent", "!ag"]:
        subargs = args.split(maxsplit=1)
        action = subargs[0].lower() if subargs else "menyu"
        subarg = subargs[1].strip() if len(subargs) > 1 else ""

        cfg = load_config()
        album_cfg = cfg.setdefault("album_settings", DEFAULT_CONFIG["album_settings"])
        album_allowed = album_cfg.setdefault("allowed_users", [])

        if action in ["ruxsat", "start", "allow", "yoq", "qosh"]:
            target_user = None
            if subarg:
                try:
                    target_user = await client.get_entity(int(subarg) if subarg.isdigit() else subarg)
                except Exception as e:
                    await respond(f"❌ Foydalanuvchi topilmadi: `{subarg}`", auto_delete=True, delay=4)
                    return
            else:
                if event.is_private and not is_saved:
                    target_user = await event.get_chat()

            if not target_user or getattr(target_user, 'is_self', False):
                await respond("ℹ️ Kontakt chatida turib `agent ruxsat` deb yozing.", auto_delete=True, delay=4)
                return

            name = f"{target_user.first_name or ''} {target_user.last_name or ''}".strip() or "Noma'lum"
            if any(u.get("id") == target_user.id for u in album_allowed):
                await respond(f"ℹ️ **{name}** allaqachon ro'yxatda bor.", auto_delete=True, delay=4)
                return

            album_allowed.append({"id": target_user.id, "name": name, "username": target_user.username or ""})
            save_config(cfg)
            await respond(f"✅ **Ruxsat berildi!**\n👤 {name} dan video, rasm va krujoklar **МОЙ АЛЬБОМ**ga uzatiladi.", auto_delete=True, delay=4)

        elif action in ["stop", "toxtat", "to'xtat", "ochir", "o'chir"]:
            target_user = None
            if event.is_private and not is_saved:
                target_user = await event.get_chat()

            if not target_user or getattr(target_user, 'is_self', False):
                await respond("ℹ️ Kontakt chatida turib `agent stop` deb yozing.", auto_delete=True, delay=4)
                return

            name = f"{target_user.first_name or ''} {target_user.last_name or ''}".strip() or "Noma'lum"
            new_allowed = [u for u in album_allowed if u.get("id") != target_user.id]
            album_cfg["allowed_users"] = new_allowed
            save_config(cfg)
            await respond(f"🛑 **Agent to'xtatildi!**\n👤 {name} dan media uzatish to'xtatildi.", auto_delete=True, delay=4)

        elif action in ["jadval", "royxat", "ro'yxat", "list"]:
            status_str = "🟢 Yoniq" if album_cfg.get("enabled", True) else "🔴 O'chiq"
            ch_id = album_cfg.get("channel_id", -1004342721043)
            msg = f"📊 **МОЙ АЛЬБОМ — Ruxsat berilgan kontaktlar:**\n• Holat: {status_str} | Kanal: `{ch_id}`\n\n"
            if not album_allowed:
                msg += "Hozircha hech kimga ruxsat berilmagan."
            else:
                for idx, u in enumerate(album_allowed, 1):
                    uname = f"@{u['username']}" if u.get('username') else "yo'q"
                    msg += f"{idx}. **{u.get('name', 'Noma`lum')}** ({uname}) — `{u.get('id')}`\n"
                msg += f"\nJami: {len(album_allowed)} ta kontakt"
            await respond(msg, auto_delete=True, delay=10)

        elif action in ["menyu", "menu", "help"]:
            menu_msg = (
                "📱 **USERBOT CLOUD (МОЙ АЛЬБОМ) — 24/7 BULUTDA:**\n\n"
                "• `agent ruxsat` — Kontakt chatida ruxsat berish (4s da o'chadi)\n"
                "• `agent stop` — Kontakt chatida to'xtatish (4s da o'chadi)\n"
                "• `agent jadval` — Ruxsat berilganlar ro'yxatini ko'rish\n"
                "• `agent menyu` — Qo'llanmani ko'rish\n"
                "📌 Faqat Video, Krujok va Rasm uzatiladi (View Once ham qo'llab-quvvatlanadi)."
            )
            await respond(menu_msg, auto_delete=True, delay=10)

# ==========================================================
# FASTAPI WEB-SERVER (24/7 KEEP-ALIVE VA HEALTHCHECK UCHUN)
# ==========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Telethon mijozini ishga tushirish
    print("🚀 Telethon Userbot ulanmoqda...")
    await client.start()
    me = await client.get_me()
    print(f"✅ Telethon muvaffaqiyatli ulandi: {me.first_name} (@{me.username or 'username_yoq'})")
    yield
    print("🛑 Telethon uzilmoqda...")
    await client.disconnect()

app = FastAPI(title="Userbot Cloud Media Forwarder", lifespan=lifespan)

@app.get("/")
@app.get("/health")
async def health_check():
    cfg = load_config()
    allowed_count = len(cfg.get("album_settings", {}).get("allowed_users", []))
    is_connected = client.is_connected()
    return {
        "status": "online" if is_connected else "connecting",
        "service": "МОЙ АЛЬБОМ Avtomatik Forwarder (24/7 Cloud)",
        "allowed_contacts_count": allowed_count,
        "channel_id": cfg.get("album_settings", {}).get("channel_id", -1004342721043),
        "timestamp": time.time()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
