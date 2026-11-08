# 🤖 @boburchat_bot — 24/7 Cloud Server Edition (Render.com)

Ushbu loyiha `@boburchat_bot` ni telefon yoki Termux o'chiq bo'lsa ham **Render.com** bulutli platformasida Docker konteynerida 24/7 uzluksiz ishlatish uchun to'liq tayyorlangan.

---

## ✨ Imkoniyatlari:
1. **Instagram & YouTube Media Downloader:**
   - Instagram (Reels, Post, Video) va YouTube (Video, Shorts, Musiqa)
   - Avtomatik **"МОЙ АЛЬБОМ"** kanaliga (`-1004342721043`) sarlavhasi bilan saqlash
2. **«Qalbga yetib boradigan so‘zlar»:**
   - 20 ta to'liq bob, 100 ta original hikmat, PDF va Luxury Dark Web-Kitob
3. **Google Gemini AI:**
   - Bobur uchun tezkor, aqlli va professional AI yordamchisi
4. **FastAPI Keep-Alive:**
   - `/health` va `/` endpointlari orqali Render xizmati 24/7 uyg'oq turadi

---

## 🚀 Render.com da Ishga Tushirish (1-Click Setup)

1. [Render.com Dashboard](https://dashboard.render.com/) ga kiring.
2. **"New +"** -> **"Web Service"** tugmasini bosing.
3. GitHub-dan `VaultCalc` reposini tanlang.
4. **Branch:** `boburchat-bot` ni tanlang.
5. **Runtime:** `Docker`
6. **Plan:** `Free` ($0/month)
7. **Environment Variables** bo'limiga quyidagilarni kiriting:
   - `BOT_TOKEN`: Telegram bot tokeningiz
   - `ADMIN_CHAT_ID`: `1260991773`
   - `CHANNEL_ID`: `-1004342721043`
   - `GEMINI_API_KEY`: Google Gemini API kalitingiz
   - `PORT`: `8080`
8. **"Deploy Web Service"** tugmasini bosing!

---

## ⚡ 24/7 Doimiy Ishlashi Uchun (Keep-Alive)
Render bepul xizmati 15 daqiqa ichida uxlab qolmasligi uchun:
- Render sizga bergan manzilni oling (masalan: `https://boburchat-bot.onrender.com/health`)
- [cron-job.org](https://cron-job.org) saytida bepul ro'yxatdan o'tib, shu URL ga har 10 daqiqada `GET` so'rov jo'natishni sozlab qo'ying.
