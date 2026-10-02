import os
import json
import asyncio
import threading
import urllib.request
import urllib.error
import datetime

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in Render Environment Variables.")

OPEN_DOTA = "https://api.opendota.com/api"

RAVENGUARD_ACCOUNT_ID = "498590584"
ARMIN_ACCOUNT_ID = "1524674878"

ARMIN_MEET = "https://meet.google.com/gto-izfj-hmj"
ALI_MEET = "https://meet.google.com/wba-iyzm-hdu"

STEAM_DOTA_NEWS = (
    "https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
    "?appid=570&count=8&maxlength=800&format=json"
)


# =========================================================
# USERS
# =========================================================

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


# =========================================================
# SIMPLE HTTP
# =========================================================

def get_json_sync(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SahebGimnet/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


async def get_json(url):
    return await asyncio.to_thread(get_json_sync, url)


# =========================================================
# TELEGRAM USERS
# =========================================================

def remember_user(user):
    if not user:
        return

    username = user.username

    if username in USERS:
        USERS[username] = user.id


def mention(username):
    user_id = USERS.get(username)

    if user_id:
        return f'<a href="tg://user?id={user_id}">@{username}</a>'

    return f"@{username}"


def mentions(usernames):
    return " ".join(mention(x) for x in usernames)


# =========================================================
# KEYBOARD
# =========================================================

def keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎮 دوتا ۲ (توربو)",
                callback_data="turbo"
            ),
            InlineKeyboardButton(
                "🎮 دوتا ۲ (رنک)",
                callback_data="ranked"
            ),
        ],
        [
            InlineKeyboardButton(
                "📢 همرو صدا کن",
                callback_data="everyone"
            ),
            InlineKeyboardButton(
                "👀 تماشاگر میخوام",
                callback_data="spectator"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔴 لینک کال آرمین سرندی",
                url=ARMIN_MEET
            ),
            InlineKeyboardButton(
                "🔵 لینک کال علی احدی",
                url=ALI_MEET
            ),
        ],
        [
            InlineKeyboardButton(
                "📰 چک کردن آپدیت دوتا ۲",
                callback_data="news"
            ),
        ],
        [
            InlineKeyboardButton(
                "🎮 نتایج اخیر RavenGuard",
                callback_data="raven"
            ),
            InlineKeyboardButton(
                "🎮 نتایج اخیر آرمین",
                callback_data="armin"
            ),
        ],
    ])


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        remember_user(update.effective_user)

    if update.message:
        await update.message.reply_text(
            "🎮🕹 <b>صاب گیمنت</b> 🎲🎱\n\n"
            "مدیریت بازی‌های گروه آماده‌ست 👇",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard(),
        )


# =========================================================
# NOTIFICATIONS
# =========================================================

async def send_notification(update, context, title, user_list):
    query = update.callback_query

    if not query or not query.message:
        return

    text = (
        f"{title}\n\n"
        f"{mentions(user_list)}\n\n"
        "🎮 بریم؟"
    )

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
    )


# =========================================================
# DOTA RECENT MATCHES
# =========================================================

def duration(seconds):
    try:
        seconds = int(seconds)
    except Exception:
        seconds = 0

    return f"{seconds // 60}:{seconds % 60:02d}"


def date_from_timestamp(timestamp):
    try:
        return datetime.datetime.fromtimestamp(
            int(timestamp)
        ).strftime("%Y-%m-%d | %H:%M")
    except Exception:
        return "نامشخص"


def result(match):
    try:
        slot = int(match.get("player_slot", 0))
        radiant = slot < 128

        if match.get("radiant_win") is None:
            return "❔ نامشخص"

        won = (
            bool(match["radiant_win"])
            if radiant
            else not bool(match["radiant_win"])
        )

        return "✅ برد" if won else "❌ باخت"

    except Exception:
        return "❔ نامشخص"


GAME_MODES = {
    1: "All Pick",
    2: "Captain's Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    11: "Mid Only",
    12: "Least Played",
    13: "Limited Heroes",
    16: "Captain's Draft",
    18: "All Draft",
    19: "Turbo",
    20: "Mutation",
    22: "Ranked All Pick",
    23: "Turbo",
}


async def get_heroes():
    try:
        data = await get_json(
            f"{OPEN_DOTA}/heroStats"
        )

        if not isinstance(data, list):
            return {}

        return {
            int(x["id"]): x.get(
                "localized_name",
                f"Hero {x['id']}"
            )
            for x in data
            if x.get("id") is not None
        }

    except Exception as error:
        print("heroStats error:", repr(error))
        return {}


async def get_recent_matches(account_id):
    # Primary endpoint
    try:
        data = await get_json(
            f"{OPEN_DOTA}/players/{account_id}/recentMatches"
        )

        if isinstance(data, list) and data:
            return data

    except Exception as error:
        print(
            f"recentMatches error for {account_id}:",
            repr(error)
        )

    # Fallback endpoint
    try:
        data = await get_json(
            f"{OPEN_DOTA}/players/{account_id}/matches?limit=5"
        )

        if isinstance(data, list) and data:
            return data

    except Exception as error:
        print(
            f"matches fallback error for {account_id}:",
            repr(error)
        )

    return []


def match_text(match, heroes):
    hero_id = match.get("hero_id")

    try:
        hero_id = int(hero_id)
    except Exception:
        hero_id = 0

    hero = heroes.get(
        hero_id,
        f"Hero ID {hero_id}"
    )

    mode_id = match.get("game_mode")

    try:
        mode_id = int(mode_id)
    except Exception:
        mode_id = 0

    mode = GAME_MODES.get(
        mode_id,
        f"Mode {mode_id}"
    )

    match_id = match.get("match_id", "?")

    kills = match.get("kills", 0)
    deaths = match.get("deaths", 0)
    assists = match.get("assists", 0)

    gpm = match.get("gold_per_min", 0)
    xpm = match.get("xp_per_min", 0)

    last_hits = match.get("last_hits", 0)
    hero_damage = match.get("hero_damage", 0)
    tower_damage = match.get("tower_damage", 0)

    return (
        f"{result(match)}\n"
        f"🦸 هیرو: <b>{hero}</b>\n"
        f"🎯 مود: {mode}\n"
        f"⏱ مدت: {duration(match.get('duration', 0))}\n"
        f"🕒 تاریخ: {date_from_timestamp(match.get('start_time'))}\n"
        f"⚔️ K/D/A: <b>{kills}/{deaths}/{assists}</b>\n"
        f"💰 GPM: {gpm} | ⭐ XPM: {xpm}\n"
        f"🎯 Last Hits: {last_hits}\n"
        f"💥 Hero Damage: {hero_damage}\n"
        f"🏰 Tower Damage: {tower_damage}\n"
        f'🔎 <a href="https://www.opendota.com/matches/{match_id}">جزئیات بازی</a>'
    )


async def show_recent(update, account_id, name):
    query = update.callback_query

    if not query or not query.message:
        return

    await query.message.reply_text(
        f"🎮 <b>در حال گرفتن بازی‌های اخیر {name}...</b>\n"
        "⏳ یک لحظه صبر کن...",
        parse_mode=ParseMode.HTML,
    )

    matches = await get_recent_matches(account_id)

    if not matches:
        await query.message.reply_text(
            f"❌ اطلاعاتی از بازی‌های اخیر {name} پیدا نشد.\n\n"
            "ممکن است OpenDota فعلاً اطلاعات این بازیکن را در دسترس نداشته باشد.",
        )
        return

    matches = sorted(
        matches,
        key=lambda x: int(x.get("start_time", 0) or 0),
        reverse=True,
    )[:5]

    heroes = await get_heroes()

    output = [
        f"🎮 <b>۵ بازی اخیر {name}</b>",
        "",
    ]

    for i, match in enumerate(matches, 1):
        output.append(f"<b>━━━━ بازی {i} ━━━━</b>")
        output.append(match_text(match, heroes))
        output.append("")

    await query.message.reply_text(
        "\n".join(output),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# =========================================================
# DOTA NEWS
# =========================================================

async def dota_news(update):
    query = update.callback_query

    if not query or not query.message:
        return

    try:
        data = await get_json(STEAM_DOTA_NEWS)

        items = (
            data
            .get("appnews", {})
            .get("newsitems", {})
            .get("newsitem", [])
        )

        if not isinstance(items, list):
            items = []

        if not items:
            await query.message.reply_text(
                "📰 فعلاً آپدیت یا خبر جدیدی از دوتا ۲ پیدا نشد."
            )
            return

        lines = [
            "📰 <b>آخرین اخبار دوتا ۲</b>",
            "",
        ]

        for item in items[:5]:
            title = item.get(
                "title",
                "بدون عنوان"
            )

            url = item.get("url")

            if url:
                lines.append(
                    f'• <a href="{url}">{title}</a>'
                )
            else:
                lines.append(f"• {title}")

        await query.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    except Exception as error:
        print(
            "Steam Dota news error:",
            repr(error)
        )

        await query.message.reply_text(
            "❌ سرویس اخبار دوتا ۲ فعلاً پاسخ نمی‌دهد.\n"
            "خود ربات سالم است."
        )


# =========================================================
# CALLBACKS
# =========================================================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not query:
        return

    remember_user(query.from_user)

    await query.answer()

    if query.data == "turbo":
        await send_notification(
            update,
            context,
            "🎮 <b>دوتا ۲ توربو</b>",
            TURBO_USERS,
        )

    elif query.data == "ranked":
        await send_notification(
            update,
            context,
            "🎮 <b>دوتا ۲ رنک</b>",
            RANKED_USERS,
        )

    elif query.data == "everyone":
        await send_notification(
            update,
            context,
            "📢 <b>همه جمع بشید!</b>",
            EVERYONE_USERS,
        )

    elif query.data == "spectator":
        await send_notification(
            update,
            context,
            "👀 <b>تماشاگر میخوام!</b>",
            SPECTATOR_USERS,
        )

    elif query.data == "raven":
        await show_recent(
            update,
            RAVENGUARD_ACCOUNT_ID,
            "RavenGuard",
        )

    elif query.data == "armin":
        await show_recent(
            update,
            ARMIN_ACCOUNT_ID,
            "آرمین",
        )

    elif query.data == "news":
        await dota_news(update)


# =========================================================
# FLASK FOR RENDER
# =========================================================

flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "Saheb Gimnet is running."


@flask_app.route("/health")
def health():
    return "OK"


def run_flask():
    port = int(os.getenv("PORT", "10000"))

    flask_app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# =========================================================
# MAIN
# =========================================================

def main():
    threading.Thread(
        target=run_flask,
        daemon=True,
    ).start()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", start)
    )

    app.add_handler(
        CallbackQueryHandler(callbacks)
    )

    print("Saheb Gimnet bot started successfully.")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
