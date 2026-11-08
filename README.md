# 📱 Userbot Media Forwarder (МОЙ АЛЬБОМ) — 24/7 Cloud

Ushbu loyiha shaxsiy Telegram lichkangizga kelgan video xabarlar (krujok), rasmlar va videolarni (shu jumladan bir martalik / View Once fayllarni) **"МОЙ АЛЬБОМ"** kanaliga 24/7 avtomatik uzatish va saqlash uchun mo'ljallangan.

---

## 🚀 100% Bepul Serverga Joylash (Render.com orqali)

### 1-qadam: GitHub'da repo ochish
1. [GitHub.com](https://github.com) ga kiring.
2. **"New repository"** tugmasini bosing.
3. Nom bering (masalan: `userbot-cloud`) va **Private** qilib yarating.
4. Ushbu papkani push qiling:
   ```bash
   git remote add origin https://github.com/SIZNING_USERNAME/userbot-cloud.git
   git push -u origin main
   ```

### 2-qadam: Render.com da 24/7 ishga tushirish
1. [Render.com](https://render.com) ga kiring va GitHub orqali ro'yxatdan o'ting (bepul).
2. **New +** -> **Web Service** ni tanlang.
3. Yangi yaratgan `userbot-cloud` reponi tanlang.
4. Sozlamalar:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** `Free` (0$/oy)
5. **Environment Variables** (o'zgaruvchilar) bo'limiga quyidagilarni kiriting:
   - `TELEGRAM_STRING_SESSION`: `session_secret.txt` faylidagi maxfiy kalit
   - `TELEGRAM_API_ID`: `31163417`
   - `TELEGRAM_API_HASH`: `ef7338d736ea3037bac99ffa66e6c577`
   - `ALBUM_CHANNEL_ID`: `-1004342721043`
6. **"Deploy Web Service"** tugmasini bosing!

---

## ⚡ 24/7 Doimiy Uxlamasligi Uchun (Keep-Alive Ping)
Render bepul xizmati 15 daqiqada uxlab qolmasligi uchun, Render sizga bergan manzilga (masalan: `https://userbot-cloud.onrender.com/health`) har 10 daqiqada ping yuborib turiladi:
- [cron-job.org](https://cron-job.org) saytida bepul ro'yxatdan o'tib, shu URL ni har 10 daqiqada chaqirishga qo'ying.
- Yoki Cloudflare Cron orqali avtomatlashtiriladi.
