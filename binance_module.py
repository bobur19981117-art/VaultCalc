"""
Binance AI & Crypto Module for @boburchat_bot (24/7 Cloud Edition)
"""

import os
import sys
import time
import json
import hmac
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import logging

logger = logging.getLogger("binance_module")

API_KEY = os.environ.get("BINANCE_API_KEY", "UZ2Q1papdNj6lfYRqvWdb9oRCKyBuzEozojkbBedctcV8GxFJ7M3tstzCgOFDY0N")
SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "FtVOgHUJZLlqEPg1gqmbg9BJKfqXfKhSM7QP7Z85GcLtvJLs4qLXmG5KezwmfbNd")
BASE_URL = os.environ.get("BINANCE_BASE_URL", "https://binance-proxy.boburjonnushonov.workers.dev")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-MBX-APIKEY": API_KEY
}

LAST_ERROR = None

def get_server_time(base=None):
    """Binance server vaqtini sinxronlash."""
    b = base or BASE_URL
    try:
        url = f"{b}/api/v3/time"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read())["serverTime"]
    except Exception:
        return int(time.time() * 1000)

def sign_query(params: dict, base=None) -> str:
    """HMAC-SHA256 imzosi."""
    params["timestamp"] = get_server_time(base)
    params["recvWindow"] = 60000
    query_str = urllib.parse.urlencode(params)
    signature = hmac.new(SECRET_KEY.encode("utf-8"), query_str.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{query_str}&signature={signature}"

def binance_api_call(endpoint: str, params: dict = None, method: str = "GET", signed: bool = False):
    """Binance API so'rovlarini xavfsiz yuborish (avto-fallback bilan)."""
    global LAST_ERROR, BASE_URL
    LAST_ERROR = None
    
    # Try candidate base URLs (direct + proxy)
    candidate_bases = [BASE_URL]
    alt = "https://api.binance.com" if "workers.dev" in BASE_URL else "https://binance-proxy.boburjonnushonov.workers.dev"
    if alt not in candidate_bases:
        candidate_bases.append(alt)

    for base in candidate_bases:
        p = dict(params or {})
        if signed:
            query_str = sign_query(p, base)
        else:
            query_str = urllib.parse.urlencode(p) if p else ""
        
        url = f"{base}{endpoint}"
        if method in ("GET", "DELETE") and query_str:
            url = f"{url}?{query_str}"
            data = None
        elif method in ("POST", "PUT"):
            data = query_str.encode("utf-8") if query_str else b""
        else:
            data = None

        headers = dict(HEADERS)
        if method in ("POST", "PUT") and data:
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                res_data = json.loads(res.read())
                BASE_URL = base
                return res_data
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            LAST_ERROR = f"HTTP {e.code}: {err_body}"
            logger.error(f"Binance [{base}] HTTP {e.code}: {err_body}")
        except Exception as e:
            LAST_ERROR = f"Network [{base}]: {e}"
            logger.error(f"Binance [{base}] Error: {e}")

    return None

def get_account_summary_text():
    """Hisob va balans haqida to'liq xabar matni (HTML)."""
    from html import escape as html_escape
    acc_data = binance_api_call("/api/v3/account", signed=True)
    if not acc_data:
        err_detail = LAST_ERROR or "Tarmoq javob bermadi."
        return (
            "⚠️ <b>Binance hisobiga ulanishda xatolik yuz berdi.</b>\n\n"
            f"🔍 <b>Tafsilot:</b> <code>{html_escape(str(err_detail))}</code>\n\n"
            "💡 <i>Iltimos, API kalit ruxsatlari yoki IP cheklovlarini tekshiring.</i>"
        )

    account_type = acc_data.get("accountType", "SPOT")
    can_trade = "✅ Faol" if acc_data.get("canTrade") else "❌ Taqiqlangan"
    can_withdraw = "✅ Ruxsat" if acc_data.get("canWithdraw") else "❌ Taqiqlangan"

    # Spot balances
    active_spot = []
    for b in acc_data.get("balances", []):
        free = float(b.get("free", 0))
        locked = float(b.get("locked", 0))
        if free > 0 or locked > 0:
            active_spot.append((b["asset"], free, locked))

    # Funding balances
    funding_data = binance_api_call("/sapi/v1/asset/get-funding-asset", method="POST", signed=True)
    active_funding = []
    if funding_data and isinstance(funding_data, list):
        for f in funding_data:
            free = float(f.get("free", 0))
            locked = float(f.get("freeze", 0))
            if free > 0 or locked > 0:
                active_funding.append((f["asset"], free, locked))

    text = (
        "🟡 <b>BINANCE HISOB VA PORTFEL BOSHQARUVI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Hisob turi:</b> <code>{account_type}</code>\n"
        f"⚡ <b>Savdo ruxsati:</b> {can_trade}\n"
        f"💳 <b>Yechish ruxsati:</b> {can_withdraw}\n"
        f"🛡️ <b>Shlyuz:</b> Cloudflare 24/7 Serverless\n\n"
        "💼 <b>AKTIULAR BALANSI:</b>\n"
    )

    if not active_spot and not active_funding:
        text += "<i>Hamyoningizda hozircha aktivlar mavjud emas (0.00).</i>\n"
    else:
        if active_spot:
            text += "<b>📊 Spot Hamyon:</b>\n"
            for asset, free, locked in active_spot:
                total = free + locked
                text += f"• <b>{asset}:</b> <code>{total:.6f}</code> (Erkin: {free:.4f})\n"
        if active_funding:
            text += "\n<b>🏦 Funding Hamyon:</b>\n"
            for asset, free, locked in active_funding:
                total = free + locked
                text += f"• <b>{asset}:</b> <code>{total:.6f}</code> (Erkin: {free:.4f})\n"

    text += "\n💡 <i>Tugmalar orqali narxlarni yoki buyurtmalarni tekshirishingiz mumkin:</i>"
    return text

def get_crypto_prices_text(custom_symbol=None):
    """Kripto narxlari ro'yxati (HTML)."""
    if custom_symbol:
        sym = custom_symbol.upper().strip()
        if not sym.endswith("USDT") and "/" not in sym:
            sym = f"{sym}USDT"
        data = binance_api_call(f"/api/v3/ticker/24hr?symbol={sym}")
        if data:
            data = [data]
    else:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "TONUSDT", "XRPUSDT"]
        sym_param = urllib.parse.quote(json.dumps(symbols, separators=(",", ":")))
        data = binance_api_call(f"/api/v3/ticker/24hr?symbols={sym_param}")

    if not data or not isinstance(data, list):
        return "⚠️ <b>Bozor narxlarini olish imkoni bo‘lmadi.</b>"

    text = (
        "📈 <b>JONLI KRIPTO BOZOR NARXLARI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    for item in data:
        pair = item["symbol"]
        price = float(item["lastPrice"])
        change = float(item["priceChangePercent"])
        vol = float(item.get("quoteVolume", 0))
        sign = "+" if change >= 0 else ""
        icon = "🟢" if change >= 0 else "🔴"

        if price >= 1.0:
            p_str = f"${price:,.2f}"
        else:
            p_str = f"${price:.6f}"

        text += (
            f"{icon} <b>{pair}</b>: <code>{p_str}</code> ({sign}{change:.2f}%)\n"
            f"   <i>24s hajm: ${vol:,.0f}</i>\n\n"
        )

    text += f"⏱ <i>Yangilangan vaqt: {time.strftime('%H:%M:%S')}</i>"
    return text

def get_open_orders_text():
    """Ochiq buyurtmalar matni."""
    data = binance_api_call("/api/v3/openOrders", signed=True)
    if data is None:
        return "⚠️ <b>Buyurtmalarni tekshirishda xatolik.</b>"

    text = (
        "📊 <b>OCHIQ BUYURTMALAR (OPEN ORDERS)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    if not data:
        text += "<i>Hozirda hech qanday ochiq buyurtma (order) yo‘q.</i>"
    else:
        for o in data[:10]:
            text += (
                f"• <b>{o['symbol']}</b> ({o['side']}): {o['origQty']} ta @ ${o['price']}\n"
                f"  <i>Status: {o['status']} | ID: {o['orderId']}</i>\n"
            )
    return text

def get_binance_markup(current_tab="main"):
    """Binance inline klaviaturasi."""
    buttons = [
        [
            {"text": "💰 Balans & Hisob", "callback_data": "binance_tab_balance"},
            {"text": "📈 Kripto Narxlar", "callback_data": "binance_tab_prices"}
        ],
        [
            {"text": "📊 Ochiq Orderlar", "callback_data": "binance_tab_orders"},
            {"text": "🔄 Yangilash", "callback_data": f"binance_refresh_{current_tab}"}
        ]
    ]
    return {"inline_keyboard": buttons}
