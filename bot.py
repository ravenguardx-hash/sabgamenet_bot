import os
import json
import asyncio
import threading
import urllib.request
import urllib.parse
import urllib.error
import datetime
from html import escape

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
# صاب گیمنت | Saheb Gimnet
# Telegram Gaming Group Bot
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

# ----------------------------
# Steam / OpenDota IDs
# ----------------------------

RAVENGUARD_ACCOUNT_ID = "498590584"
ARMIN_ACCOUNT_ID = "1524674878"

OPEN_DOTA_BASE = "https://api.opendota.com/api"
STEAM_NEWS_URL = (
    "https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
    "?appid=570&count=5&maxlength=600&format=json"
)

# ----------------------------
# Google Meet links
# ----------------------------

ARMIN_MEET_URL = "https://meet.google.com/gto-izfj-hmj"
ALI_MEET_URL = "https://meet.google.com/wba-iyzm-hdu"

# ----------------------------
# Known users
# IDs are learned automatically when users interact with the bot.
# They are kept in RAM and reset after restart/deploy.
# ----------------------------

USERS = {
    "AlieAhadi": None,
    "Arminsarandii": None,
    "Ballfreak": None,
    "Mojtaba_bd": None,
    "Reza_rus": None,
    "Jey_0Oj": None,
    "a_p_karimi": None,
    "alimakkiiii": None,
    "Ahmad_b78": None,
}

# ----------------------------
# Notification groups
# ----------------------------

TURBO_USERS = [
    "AlieAhadi",
    "Arminsarandii",
    "Ballfreak",
    "Mojtaba_bd",
    "Reza_rus",
    "Jey_0Oj",
]

RANKED_USERS = [
    "AlieAhadi",
    "Arminsarandii",
    "Ballfreak",
    "Mojtaba_bd",
    "Reza_rus",
    "a_p_karimi",
]

EVERYONE_USERS = [
    "AlieAhadi",
    "Arminsarandii",
    "Ballfreak",
    "Mojtaba_bd",
    "Reza_rus",
    "a_p_karimi",
    "alimakkiiii",
    "Ahmad_b78",
]

SPECTATOR_USERS = [
    "alimakkiiii",
    "Ahmad_b78",
]

# ----------------------------
# Cache
# ----------------------------

HERO_MAP_CACHE = None
HERO_MAP_CACHE_TIME = 0.0
HERO_MAP_CACHE_TTL = 60 * 60 * 6


# ============================================================
# Generic HTTP helpers
# ============================================================

def http_get_json(url: str, timeout: int = 20):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Saheb-Gimnet/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw)


def http_post_json(url: str, timeout: int = 20):
    request = urllib.request.Request(
        url,
        data=b"",
        method="POST",
        headers={
            "User-Agent": "Saheb-Gimnet/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        if not raw.strip():
            return {}
        return json.loads(raw)


async def get_json(url: str, timeout: int = 20):
    return await asyncio.to_thread(http_get_json, url, timeout)


async def post_json(url: str, timeout: int = 20):
    return await asyncio.to_thread(http_post_json, url, timeout)


# ============================================================
# Telegram users / mentions
# ============================================================

def remember_telegram_user(user):
    if not user:
        return

    username = user.username
    if username and username in USERS:
        USERS[username] = user.id


def mention_html(username: str) -> str:
    user_id = USERS.get(username)

    if user_id:
        return f'<a href="tg://user?id={user_id}">@{escape(username)}</a>'

    return f"@{escape(username)}"


def build_mentions(usernames):
    return " ".join(mention_html(username) for username in usernames)


def build_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎮 دوتا ۲ (توربو)", callback_data="turbo"),
            InlineKeyboardButton("🎮 دوتا ۲ (رنک)", callback_data="ranked"),
        ],
        [
            InlineKeyboardButton("📢 همرو صدا کن", callback_data="everyone"),
            InlineKeyboardButton("👀 تماشاگر میخوام", callback_data="spectator"),
        ],
        [
            InlineKeyboardButton("🔴 لینک کال آرمین سرندی", url=ARMIN_MEET_URL),
            InlineKeyboardButton("🔵 لینک کال علی احدی", url=ALI_MEET_URL),
        ],
        [
            InlineKeyboardButton(
                "📰 چک کردن آپدیت دوتا ۲",
                callback_data="dota_updates",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎮 نتایج اخیر RavenGuard",
                callback_data="raven_results",
            ),
            InlineKeyboardButton(
                "🎮 نتایج اخیر آرمین",
                callback_data="armin_results",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# /start
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        remember_telegram_user(update.effective_user)

    text = (
        "🎮 <b>صاب گیمنت</b>\n\n"
        "مدیریت بازی‌های گروه آماده‌ست.\n"
        "از دکمه‌های زیر استفاده کن:"
    )

    if update.message:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=build_main_keyboard(),
            disable_web_page_preview=True,
        )


async def remember_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        remember_telegram_user(update.effective_user)


# ============================================================
# Notification buttons
# ============================================================

async def notify_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    title: str,
    usernames,
):
    if not update.callback_query or not update.callback_query.message:
        return

    query = update.callback_query
    chat_id = query.message.chat_id

    mentions = build_mentions(usernames)

    text = (
        f"{title}\n\n"
        f"{mentions}\n\n"
        "🎮 بزن بریم!"
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ============================================================
# OpenDota
# ============================================================

async def get_recent_matches(account_id: str):
    url = f"{OPEN_DOTA_BASE}/players/{account_id}/recentMatches"
    return await get_json(url)


async def refresh_player(account_id: str):
    url = f"{OPEN_DOTA_BASE}/players/{account_id}/refresh"
    return await post_json(url)


async def get_hero_map():
    global HERO_MAP_CACHE
    global HERO_MAP_CACHE_TIME

    now = datetime.datetime.now().timestamp()

    if HERO_MAP_CACHE is not None and (now - HERO_MAP_CACHE_TIME) < HERO_MAP_CACHE_TTL:
        return HERO_MAP_CACHE

    try:
        url = f"{OPEN_DOTA_BASE}/heroStats"
        data = await get_json(url)

        hero_map = {}

        if isinstance(data, list):
            for hero in data:
                hero_id = hero.get("id")
                localized_name = hero.get("localized_name")

                if hero_id is not None and localized_name:
                    hero_map[int(hero_id)] = localized_name

        if hero_map:
            HERO_MAP_CACHE = hero_map
            HERO_MAP_CACHE_TIME = now

        return hero_map

    except Exception as exc:
        print(f"[OpenDota] heroStats failed: {exc}")
        return HERO_MAP_CACHE or {}


# ============================================================
# Dota labels / formatting
# ============================================================

GAME_MODES = {
    0: "نامشخص",
    1: "All Pick",
    2: "Captain's Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    6: "Intro",
    7: "Diretide",
    8: "Reverse Captain's Mode",
    9: "Greeviling",
    10: "Tutorial",
    11: "Mid Only",
    12: "Least Played",
    13: "Limited Heroes",
    14: "Compendium Match",
    15: "Custom",
    16: "Captain's Draft",
    17: "Random Ability",
    18: "All Draft",
    19: "Turbo",
    20: "Mutation",
    21: "Coach",
    22: "Ranked All Pick",
    23: "Turbo",
    24: "Ranked",
    25: "Event",
    26: "Ability Arena",
    27: "Universal",
    28: "Turbo+",
}


def format_duration(seconds):
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError):
        seconds = 0

    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def format_match_datetime(timestamp):
    if not timestamp:
        return "نامشخص"

    try:
        dt = datetime.datetime.fromtimestamp(int(timestamp))
        return dt.strftime("%Y-%m-%d | %H:%M")
    except (TypeError, ValueError, OverflowError, OSError):
        return "نامشخص"


def result_for_player(match):
    player_slot = int(match.get("player_slot", 0) or 0)
    radiant = player_slot < 128
    radiant_win = match.get("radiant_win")

    if radiant_win is None:
        return "❔"

    won = bool(radiant_win) if radiant else not bool(radiant_win)
    return "✅ برد" if won else "❌ باخت"


def game_mode_label(match):
    mode_id = match.get("game_mode")
    try:
        mode_id = int(mode_id)
    except (TypeError, ValueError):
        mode_id = 0

    mode = GAME_MODES.get(mode_id, f"Mode {mode_id}")

    lobby_type = match.get("lobby_type")
    try:
        lobby_type = int(lobby_type)
    except (TypeError, ValueError):
        lobby_type = None

    if lobby_type == 7 and mode not in ("Turbo", "Turbo+"):
        return f"{mode} | Ranked"

    return mode


def safe_number(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def build_match_text(match, hero_map):
    match_id = match.get("match_id", "Unknown")
    hero_id = match.get("hero_id")
    hero_name = hero_map.get(int(hero_id), f"Hero ID {hero_id}") if hero_id else "نامشخص"

    result = result_for_player(match)
    duration = format_duration(match.get("duration"))
    mode = game_mode_label(match)
    date_time = format_match_datetime(match.get("start_time"))

    kills = safe_number(match.get("kills"))
    deaths = safe_number(match.get("deaths"))
    assists = safe_number(match.get("assists"))

    gpm = safe_number(match.get("gold_per_min"))
    xpm = safe_number(match.get("xp_per_min"))
    last_hits = safe_number(match.get("last_hits"))
    hero_damage = safe_number(match.get("hero_damage"))
    tower_damage = safe_number(match.get("tower_damage"))

    details = (
        f"<b>{result}</b>\n"
        f"🦸 هیرو: <b>{escape(str(hero_name))}</b>\n"
        f"🎯 مود: {escape(str(mode))}\n"
        f"⏱ مدت: {duration}\n"
        f"🕒 تاریخ: {date_time}\n"
        f"⚔️ K/D/A: <b>{kills}/{deaths}/{assists}</b>\n"
        f"💰 GPM: {gpm} | ⭐ XPM: {xpm}\n"
        f"🎯 Last Hits: {last_hits}\n"
        f"💥 Hero Damage: {hero_damage}\n"
        f"🏰 Tower Damage: {tower_damage}\n"
        f"🔎 <a href=\"https://www.opendota.com/matches/{match_id}\">جزئیات کامل بازی</a>"
    )

    return details


async def get_matches_with_retry(account_id: str):
    # First attempt
    try:
        data = await get_recent_matches(account_id)

        if isinstance(data, list) and data:
            return data, None

    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return None, "rate_limit"
        print(f"[OpenDota] recentMatches HTTP error: {exc}")
    except urllib.error.URLError as exc:
        print(f"[OpenDota] recentMatches URL error: {exc}")
    except Exception as exc:
        print(f"[OpenDota] recentMatches error: {exc}")

    # Refresh OpenDota cache once
    try:
        await refresh_player(account_id)
    except urllib.error.HTTPError as exc:
        print(f"[OpenDota] refresh HTTP error: {exc}")
    except urllib.error.URLError as exc:
        print(f"[OpenDota] refresh URL error: {exc}")
    except Exception as exc:
        print(f"[OpenDota] refresh error: {exc}")

    await asyncio.sleep(2)

    # Second attempt
    try:
        data = await get_recent_matches(account_id)

        if isinstance(data, list) and data:
            return data, None

        return [], "empty"

    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return None, "rate_limit"
        print(f"[OpenDota] second recentMatches HTTP error: {exc}")
        return None, "http"
    except urllib.error.URLError as exc:
        print(f"[OpenDota] second recentMatches URL error: {exc}")
        return None, "network"
    except Exception as exc:
        print(f"[OpenDota] second recentMatches error: {exc}")
        return None, "unknown"


async def show_player_results(
    update: Update,
    account_id: str,
    display_name: str,
):
    if not update.callback_query or not update.callback_query.message:
        return

    query = update.callback_query
    message = query.message

    waiting_text = (
        f"🎮 <b>در حال گرفتن ۵ بازی اخیر {escape(display_name)}...</b>\n\n"
        "⏳ یک لحظه صبر کن..."
    )

    await message.reply_text(
        waiting_text,
        parse_mode=ParseMode.HTML,
    )

    matches, status = await get_matches_with_retry(account_id)

    if status == "rate_limit":
        await message.reply_text(
            "⚠️ OpenDota فعلاً درخواست‌های زیادی دریافت کرده.\n"
            "چند لحظه بعد دوباره همین دکمه را بزن.",
        )
        return

    if matches is None:
        await message.reply_text(
            "❌ ارتباط با OpenDota برقرار نشد.\n"
            "این خطا از سرویس آمار بازی است، نه از منوی ربات.",
        )
        return

    if not matches:
        await message.reply_text(
            f"❌ اطلاعاتی از بازی‌های اخیر <b>{escape(display_name)}</b> پیدا نشد.\n\n"
            "ممکن است OpenDota هنوز اطلاعات حساب را به‌روزرسانی نکرده باشد.",
            parse_mode=ParseMode.HTML,
        )
        return

    # Sort newest first and keep exactly 5
    matches = sorted(
        matches,
        key=lambda item: safe_number(item.get("start_time")),
        reverse=True,
    )[:5]

    hero_map = await get_hero_map()

    parts = [
        f"🎮 <b>۵ بازی اخیر {escape(display_name)}</b>",
        "",
    ]

    for index, match in enumerate(matches, start=1):
        parts.append(f"<b>━━ بازی {index} ━━</b>")
        parts.append(build_match_text(match, hero_map))
        parts.append("")

    result_text = "\n".join(parts)

    await message.reply_text(
        result_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ============================================================
# RavenGuard / Armin callbacks
# ============================================================

async def handle_raven_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_player_results(
        update,
        RAVENGUARD_ACCOUNT_ID,
        "RavenGuard",
    )


async def handle_armin_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_player_results(
        update,
        ARMIN_ACCOUNT_ID,
        "آرمین",
    )


# ============================================================
# Dota 2 news / updates
# ============================================================

async def get_dota_news():
    data = await get_json(STEAM_NEWS_URL)

    appnews = data.get("appnews", {})
    news_items = appnews.get("newsitems", {}).get("newsitem", [])

    if not isinstance(news_items, list):
        news_items = []

    return news_items


async def handle_dota_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.callback_query or not update.callback_query.message:
        return

    message = update.callback_query.message

    try:
        news = await get_dota_news()
    except urllib.error.HTTPError as exc:
        await message.reply_text(
            f"❌ سرویس اخبار استیم خطای HTTP {exc.code} برگرداند."
        )
        return
    except urllib.error.URLError:
        await message.reply_text(
            "❌ فعلاً به سرویس اخبار استیم دسترسی ندارم."
        )
        return
    except Exception as exc:
        print(f"[Steam News] error: {exc}")
        await message.reply_text(
            "❌ هنگام گرفتن آپدیت‌های دوتا ۲ خطایی رخ داد."
        )
        return

    if not news:
        await message.reply_text(
            "📰 فعلاً خبر جدیدی از دوتا ۲ پیدا نشد."
        )
        return

    lines = ["📰 <b>آخرین اخبار دوتا ۲</b>", ""]

    for item in news[:5]:
        title = escape(item.get("title", "بدون عنوان"))
        url = item.get("url", "")

        if url:
            lines.append(f'• <a href="{escape(url)}">{title}</a>')
        else:
            lines.append(f"• {title}")

    await message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ============================================================
# Callback handler
# ============================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return

    if query.from_user:
        remember_telegram_user(query.from_user)

    # Telegram shows a loading state until answer() is called.
    await query.answer()

    data = query.data or ""

    if data == "turbo":
        await notify_group(
            update,
            context,
            "🎮 <b>دوتا ۲ توربو</b>",
            TURBO_USERS,
        )
        return

    if data == "ranked":
        await notify_group(
            update,
            context,
            "🎮 <b>دوتا ۲ رنک</b>",
            RANKED_USERS,
        )
        return

    if data == "everyone":
        await notify_group(
            update,
            context,
            "📢 <b>همه جمع بشید!</b>",
            EVERYONE_USERS,
        )
        return

    if data == "spectator":
        await notify_group(
            update,
            context,
            "👀 <b>تماشاگر لازم دارم!</b>",
            SPECTATOR_USERS,
        )
        return

    if data == "dota_updates":
        await handle_dota_updates(update, context)
        return

    if data == "raven_results":
        await handle_raven_results(update, context)
        return

    if data == "armin_results":
        await handle_armin_results(update, context)
        return


# ============================================================
# Telegram error handler
# ============================================================

async def telegram_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("[Telegram] Unhandled error:")
    print(repr(context.error))


# ============================================================
# Flask server for Render
# ============================================================

flask_app = Flask(__name__)


@flask_app.get("/")
def home():
    return "Saheb Gimnet bot is running."


@flask_app.get("/health")
def health():
    return {"status": "ok"}


def run_flask():
    port = int(os.getenv("PORT", "10000"))
    flask_app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ============================================================
# Main
# ============================================================

def main():
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
    )
    flask_thread.start()

    application: Application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(
        MessageHandler(
            filters.ALL,
            remember_user_message,
        )
    )

    application.add_error_handler(telegram_error_handler)

    print("Saheb Gimnet bot started successfully.")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
