import os
import json
import asyncio
import threading
import urllib.request
import urllib.parse
import urllib.error
import datetime
import re
from html import escape, unescape

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler


BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

RAVENGUARD_ACCOUNT_ID = "498590584"
ARMIN_ACCOUNT_ID = "1524674878"

MEET_ARMIN = "https://meet.google.com/gto-izfj-hmj"
MEET_ALI = "https://meet.google.com/wba-iyzm-hdu"


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


HERO_MAP_CACHE = None


def remember_user(update):
    user = update.effective_user

    if user and user.username in USERS:
        USERS[user.username] = user.id


def mention_user(username):
    user_id = USERS.get(username)

    if user_id:
        return (
            '<a href="tg://user?id='
            + str(user_id)
            + '">'
            + escape(username)
            + "</a>"
        )

    return "@" + escape(username)


def make_mentions(names):
    return " ".join(
        mention_user(name)
        for name in names
    )


def http_get(url, timeout=20):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SahebGimnet/1.0"
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:
            return response.read().decode(
                "utf-8",
                errors="ignore"
            )

    except urllib.error.HTTPError as error:
        body = ""

        try:
            body = error.read().decode(
                "utf-8",
                errors="ignore"
            )
        except Exception:
            pass

        raise Exception(
            "HTTP "
            + str(error.code)
            + ": "
            + body[:300]
        )

    except urllib.error.URLError as error:
        raise Exception(
            "Network error: "
            + str(error.reason)
        )


def get_json(url, timeout=20):
    raw = http_get(
        url,
        timeout
    )

    try:
        return json.loads(raw)

    except Exception:
        raise Exception(
            "پاسخ JSON معتبر دریافت نشد."
        )


def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 دوتا ۲ (توربو)",
                callback_data="turbo"
            ),
            InlineKeyboardButton(
                "🎮 دوتا ۲ (رنک)",
                callback_data="ranked"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 همرو صدا کن",
                callback_data="everyone"
            ),
            InlineKeyboardButton(
                "👀 تماشاگر میخوام",
                callback_data="spectator"
            )
        ],
        [
            InlineKeyboardButton(
                "🔴 لینک کال آرمین سرندی",
                callback_data="armin_call"
            ),
            InlineKeyboardButton(
                "🔵 لینک کال علی احدی",
                callback_data="ali_call"
            )
        ],
        [
            InlineKeyboardButton(
                "📰 چک کردن آپدیت دوتا ۲",
                callback_data="dota_update"
            )
        ],
        [
            InlineKeyboardButton(
                "🎮 نتایج اخیر RavenGuard",
                callback_data="raven_results"
            )
        ],
        [
            InlineKeyboardButton(
                "🎮 نتایج اخیر آرمین",
                callback_data="armin_results"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update, context):
    remember_user(update)

    await update.message.reply_text(
        "🎮 <b>صاب گیمنت</b>\n\n"
        "مدیریت بازی و هماهنگی بچه‌های گیمنت 🎯\n\n"
        "یکی از گزینه‌های زیر رو انتخاب کن:",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


async def menu_command(update, context):
    remember_user(update)

    await update.message.reply_text(
        "🎮 <b>صاب گیمنت</b>\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


async def handle_turbo(query):
    await query.message.reply_text(
        "🎮 <b>دوتا ۲ - توربو</b>\n\n"
        "🔥 بازیکن‌های مورد نیاز:\n\n"
        + make_mentions(TURBO_USERS)
        + "\n\n"
        "بچه‌ها بریم توربو؟ 😎",
        parse_mode="HTML"
    )


async def handle_ranked(query):
    await query.message.reply_text(
        "🎮 <b>دوتا ۲ - رنک</b>\n\n"
        "🏆 بازیکن‌های مورد نیاز:\n\n"
        + make_mentions(RANKED_USERS)
        + "\n\n"
        "بریم رنک؟ 🔥",
        parse_mode="HTML"
    )


async def handle_everyone(query):
    await query.message.reply_text(
        "📢 <b>همرو صدا کن!</b>\n\n"
        + make_mentions(EVERYONE_USERS)
        + "\n\n"
        "🎮 بچه‌هاااااااااااااااا\n"
        "بریم بازی؟ 🔥",
        parse_mode="HTML"
    )


async def handle_spectator(query):
    await query.message.reply_text(
        "👀 <b>تماشاگر میخوام!</b>\n\n"
        + make_mentions(SPECTATOR_USERS)
        + "\n\n"
        "🎥 اگه بیکارید بیاید تماشا!",
        parse_mode="HTML"
    )


async def handle_armin_call(query):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔴 ورود به کال آرمین",
                url=MEET_ARMIN
            )
        ]
    ])

    await query.message.reply_text(
        "🔴 <b>کال آرمین سرندی</b>\n\n"
        "برای ورود روی دکمه زیر بزن:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_ali_call(query):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔵 ورود به کال علی",
                url=MEET_ALI
            )
        ]
    ])

    await query.message.reply_text(
        "🔵 <b>کال علی احدی</b>\n\n"
        "برای ورود روی دکمه زیر بزن:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


def get_recent_matches(account_id):
    url = (
        "https://api.opendota.com/api/players/"
        + str(account_id)
        + "/recentMatches"
    )

    data = get_json(
        url,
        30
    )

    if not isinstance(data, list):
        raise Exception(
            "OpenDota پاسخ نامعتبر داد."
        )

    return data


def get_player_profile(account_id):
    url = (
        "https://api.opendota.com/api/players/"
        + str(account_id)
    )

    return get_json(
        url,
        20
    )


def refresh_player(account_id):
    url = (
        "https://api.opendota.com/api/players/"
        + str(account_id)
        + "/refresh"
    )

    request = urllib.request.Request(
        url,
        method="POST",
        headers={
            "User-Agent": "SahebGimnet/1.0"
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            return response.read().decode(
                "utf-8",
                errors="ignore"
            )

    except Exception as error:
        print(
            "OpenDota refresh error:",
            error
        )

        return None


def get_hero_map():
    global HERO_MAP_CACHE

    if HERO_MAP_CACHE is not None:
        return HERO_MAP_CACHE

    data = get_json(
        "https://api.opendota.com/api/heroStats",
        20
    )

    HERO_MAP_CACHE = {}

    for hero in data:
        hero_id = hero.get("id")

        if hero_id is not None:
            HERO_MAP_CACHE[int(hero_id)] = hero.get(
                "localized_name",
                "Unknown"
            )

    return HERO_MAP_CACHE


DOTA_MODES = {
    1: "All Pick",
    2: "Captain's Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    6: "Intro",
    7: "Diretide",
    8: "Reverse Captain's Mode",
    9: "The Greeviling",
    10: "Tutorial",
    11: "Mid Only",
    12: "Least Played",
    13: "New Player Pool",
    14: "Compendium Matchmaking",
    15: "Custom",
    16: "Captain's Draft",
    17: "Balanced Draft",
    18: "Ability Draft",
    19: "Event",
    20: "All Random Deathmatch",
    21: "1v1 Mid",
    22: "Ranked All Pick",
    23: "Turbo",
    24: "Mutation",
    25: "Co-op Bots",
    26: "Ranked Turbo",
    27: "Ranked Ability Draft",
    28: "Ranked All Pick"
}


def format_duration(seconds):
    try:
        seconds = int(seconds)

        return (
            str(seconds // 60)
            + ":"
            + str(seconds % 60).zfill(2)
        )

    except Exception:
        return "-"


def format_number(number):
    try:
        return "{:,}".format(
            int(number)
        )

    except Exception:
        return "-"


def build_match_text(match, heroes):
    player_slot = match.get(
        "player_slot",
        0
    )

    radiant = player_slot < 128

    radiant_win = match.get(
        "radiant_win"
    )

    if radiant_win is None:
        result = "❔ نتیجه نامشخص"

    elif bool(radiant_win) == radiant:
        result = "🟢 برد"

    else:
        result = "🔴 باخت"

    hero_id = match.get(
        "hero_id"
    )

    if hero_id:
        try:
            hero = heroes.get(
                int(hero_id),
                "Hero ID " + str(hero_id)
            )
        except Exception:
            hero = "Hero ID " + str(hero_id)
    else:
        hero = "نامشخص"

    start_time = match.get(
        "start_time"
    )

    date_text = "نامشخص"

    if start_time:
        try:
            date_text = datetime.datetime.fromtimestamp(
                int(start_time)
            ).strftime(
                "%Y-%m-%d %H:%M"
            )
        except Exception:
            pass

    text = (
        "<b>"
        + escape(result)
        + "</b>\n"
        "🦸 Hero: <b>"
        + escape(str(hero))
        + "</b>\n"
        "🎮 Mode: "
        + escape(
            str(
                DOTA_MODES.get(
                    match.get("game_mode"),
                    "Unknown"
                )
            )
        )
        + "\n"
        "⏱ Duration: "
        + format_duration(
            match.get(
                "duration",
                0
            )
        )
        + "\n"
        "📅 Date: "
        + escape(date_text)
        + "\n\n"
        "⚔️ K/D/A: "
        + str(match.get("kills", 0))
        + "/"
        + str(match.get("deaths", 0))
        + "/"
        + str(match.get("assists", 0))
        + "\n"
        "💰 GPM: "
        + format_number(
            match.get("gold_per_min", 0)
        )
        + "\n"
        "⭐ XPM: "
        + format_number(
            match.get("xp_per_min", 0)
        )
        + "\n"
        "🎯 Last Hits: "
        + format_number(
            match.get("last_hits", 0)
        )
        + "\n"
        "💥 Hero Damage: "
        + format_number(
            match.get("hero_damage", 0)
        )
        + "\n"
        "🏰 Tower Damage: "
        + format_number(
            match.get("tower_damage", 0)
        )
    )

    match_id = match.get(
        "match_id"
    )

    if match_id:
        text += (
            "\n\n"
            "🔗 <a href=\"https://www.opendota.com/matches/"
            + str(match_id)
            + "\">مشاهده جزئیات مچ</a>"
        )

    return text


async def show_player_results(
    query,
    account_id,
    player_name
):
    loading = await query.message.reply_text(
        "🎮 <b>در حال گرفتن بازی‌های اخیر "
        + escape(player_name)
        + "...</b>\n\n"
        "⏳ یک لحظه صبر کن...",
        parse_mode="HTML"
    )

    try:
        matches = []

        first_error = None

        try:
            matches = await asyncio.to_thread(
                get_recent_matches,
                account_id
            )

        except Exception as error:
            first_error = str(error)

            print(
                player_name,
                "first OpenDota error:",
                error
            )

        if not matches:
            await loading.edit_text(
                "🔄 بازی‌های اخیر "
                + escape(player_name)
                + " پیدا نشد.\n\n"
                "⏳ در حال Refresh کردن OpenDota...",
                parse_mode="HTML"
            )

            await asyncio.to_thread(
                refresh_player,
                account_id
            )

            await asyncio.sleep(
                5
            )

            try:
                matches = await asyncio.to_thread(
                    get_recent_matches,
                    account_id
                )

            except Exception as error:
                print(
                    player_name,
                    "second OpenDota error:",
                    error
                )

        if not matches:
            profile_note = ""

            try:
                profile = await asyncio.to_thread(
                    get_player_profile,
                    account_id
                )

                if isinstance(profile, dict):
                    profile_data = profile.get(
                        "profile",
                        {}
                    )

                    profile_name = profile_data.get(
                        "personaname"
                    )

                    if profile_name:
                        profile_note = (
                            "\n\n👤 پروفایل OpenDota پیدا شد: "
                            "<b>"
                            + escape(
                                str(profile_name)
                            )
                            + "</b>"
                        )

            except Exception as error:
                print(
                    player_name,
                    "profile error:",
                    error
                )

            error_note = ""

            if first_error:
                error_note = (
                    "\n\n🔎 خطای اولیه:\n"
                    "<code>"
                    + escape(
                        first_error[:500]
                    )
                    + "</code>"
                )

            await loading.edit_text(
                "❌ بازی‌های اخیر "
                + escape(player_name)
                + " پیدا نشد."
                + profile_note
                + error_note
                + "\n\n"
                "ممکنه OpenDota هنوز Match History این اکانت را دریافت نکرده باشد.",
                parse_mode="HTML"
            )

            return

        try:
            heroes = await asyncio.to_thread(
                get_hero_map
            )

        except Exception as error:
            print(
                "Hero API error:",
                error
            )

            heroes = {}

        await loading.edit_text(
            "🎮 <b>۵ بازی اخیر "
            + escape(player_name)
            + "</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML"
        )

        for index, match in enumerate(
            matches[:5],
            1
        ):
            try:
                await query.message.reply_text(
                    "🎮 <b>Match #"
                    + str(index)
                    + "</b>\n\n"
                    + build_match_text(
                        match,
                        heroes
                    ),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )

            except Exception as error:
                print(
                    player_name,
                    "match display error:",
                    error
                )

    except Exception as error:
        print(
            player_name,
            "fatal results error:",
            error
        )

        await loading.edit_text(
            "❌ خطا هنگام دریافت بازی‌های "
            + escape(player_name)
            + ".\n\n"
            "<code>"
            + escape(str(error))
            + "</code>",
            parse_mode="HTML"
        )


async def handle_raven_results(query):
    await show_player_results(
        query,
        RAVENGUARD_ACCOUNT_ID,
        "RavenGuard"
    )


async def handle_armin_results(query):
    await show_player_results(
        query,
        ARMIN_ACCOUNT_ID,
        "آرمین"
    )


def html_to_text(value):
    value = re.sub(
        r"(?is)<script.*?</script>",
        " ",
        value or ""
    )

    value = re.sub(
        r"(?is)<style.*?</style>",
        " ",
        value
    )

    value = re.sub(
        r"(?is)<br\s*/?>",
        "\n",
        value
    )

    value = re.sub(
        r"(?is)</(p|div|li|h1|h2|h3|h4|tr)>",
        "\n",
        value
    )

    value = re.sub(
        r"(?is)<[^>]+>",
        " ",
        value
    )

    value = unescape(value)

    value = re.sub(
        r"[ \t]+",
        " ",
        value
    )

    value = re.sub(
        r"\n\s*\n+",
        "\n",
        value
    )

    return value.strip()


def get_latest_gameplay_patch():
    url = (
        "https://api.steampowered.com/"
        "ISteamNews/GetNewsForApp/v0002/"
        "?appid=570"
        "&count=30"
        "&maxlength=100000"
        "&format=json"
    )

    data = get_json(
        url,
        20
    )

    items = (
        data.get(
            "appnews",
            {}
        ).get(
            "newsitems",
            []
        )
    )

    patch_item = None

    for item in items:
        title = str(
            item.get(
                "title",
                ""
            )
        )

        if (
            "Gameplay Update" in title
            or "Gameplay Patch" in title
        ):
            patch_item = item
            break

    if patch_item is None and items:
        patch_item = items[0]

    if patch_item is None:
        return None

    title = patch_item.get(
        "title",
        "Dota 2 Update"
    )

    version_match = re.search(
        r"\b\d+\.\d+[a-z]?\b",
        title
    )

    version = ""

    if version_match:
        version = version_match.group(0)

    return {
        "title": title,
        "contents": patch_item.get(
            "contents",
            ""
        ),
        "url": patch_item.get(
            "url",
            ""
        ),
        "version": version
    }


def extract_patch_changes(contents):
    lines = [
        line.strip()
        for line in html_to_text(
            contents
        ).splitlines()
        if line.strip()
    ]

    keywords = [
        "hero",
        "heroes",
        "item",
        "items",
        "neutral",
        "talent",
        "damage",
        "armor",
        "health",
        "mana",
        "cooldown",
        "gold",
        "experience",
        "xp",
        "ability",
        "spell",
        "map",
        "tower",
        "roshan",
        "facet",
        "innate"
    ]

    useful = []

    for line in lines:
        if len(line) < 20:
            continue

        if any(
            keyword in line.lower()
            for keyword in keywords
        ):
            useful.append(line)

    if not useful:
        useful = lines

    result = []
    seen = set()

    for line in useful:
        key = line.lower()

        if key in seen:
            continue

        seen.add(key)

        if len(line) > 500:
            line = line[:500] + "..."

        result.append(line)

        if len(result) >= 10:
            break

    return result


def translate_to_persian(text):
    try:
        encoded = urllib.parse.quote(
            text[:1800]
        )

        url = (
            "https://translate.googleapis.com/"
            "translate_a/single"
            "?client=gtx"
            "&sl=en"
            "&tl=fa"
            "&dt=t"
            "&q="
            + encoded
        )

        data = get_json(
            url,
            15
        )

        result = ""

        if (
            isinstance(data, list)
            and data
            and isinstance(data[0], list)
        ):
            for item in data[0]:
                if (
                    isinstance(item, list)
                    and item
                ):
                    result += str(
                        item[0]
                    )

        return result.strip() or text

    except Exception:
        return text


async def handle_dota_update(query):
    loading = await query.message.reply_text(
        "📰 <b>در حال بررسی آخرین آپدیت Dota 2...</b>\n"
        "⏳ لطفاً چند ثانیه صبر کن.",
        parse_mode="HTML"
    )

    try:
        patch = await asyncio.to_thread(
            get_latest_gameplay_patch
        )

        if not patch:
            await loading.edit_text(
                "❌ آخرین آپدیت Dota 2 پیدا نشد.",
                parse_mode="HTML"
            )

            return

        changes = await asyncio.to_thread(
            extract_patch_changes,
            patch["contents"]
        )

        text = (
            "📰 <b>آخرین آپدیت Dota 2</b>\n\n"
            "📌 "
            + escape(patch["title"])
        )

        if patch["version"]:
            text += (
                "\n🔢 Version: <b>"
                + escape(patch["version"])
                + "</b>"
            )

        text += (
            "\n\n"
            "🔥 <b>تغییرات مهم:</b>\n\n"
        )

        if not changes:
            changes = [
                "تغییرات دریافت نشد."
            ]

        for index, change in enumerate(
            changes,
            1
        ):
            translated = await asyncio.to_thread(
                translate_to_persian,
                change
            )

            text += (
                "▫️ <b>"
                + str(index)
                + ".</b> "
                + escape(translated)
                + "\n\n"
            )

            if len(text) > 3800:
                break

        keyboard = None

        if patch["url"]:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🌐 مشاهده منبع آپدیت",
                        url=patch["url"]
                    )
                ]
            ])

        await loading.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    except Exception as error:
        await loading.edit_text(
            "❌ خطا در دریافت آپدیت:\n\n"
            "<code>"
            + escape(str(error))
            + "</code>",
            parse_mode="HTML"
        )


async def button_handler(
    update,
    context
):
    query = update.callback_query

    await query.answer()

    remember_user(update)

    handlers = {
        "turbo": handle_turbo,
        "ranked": handle_ranked,
        "everyone": handle_everyone,
        "spectator": handle_spectator,
        "armin_call": handle_armin_call,
        "ali_call": handle_ali_call,
        "dota_update": handle_dota_update,
        "raven_results": handle_raven_results,
        "armin_results": handle_armin_results,
    }

    handler = handlers.get(
        query.data
    )

    if handler:
        await handler(query)


web_app = Flask(
    "saheb_gimnet"
)


@web_app.route("/")
def home():
    return "Saheb Gimnet Bot is running."


@web_app.route("/health")
def health():
    return "OK"


def run_web_server():
    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )


async def post_init(application):
    print(
        "Saheb Gimnet bot started successfully."
    )


def main():
    if not BOT_TOKEN:
        print(
            "ERROR: BOT_TOKEN is not set."
        )

        return

    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "menu",
            menu_command
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    print(
        "Bot is starting..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


main()
```
