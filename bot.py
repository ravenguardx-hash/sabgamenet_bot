import os
import re
import json
import asyncio
import threading
import urllib.request
import urllib.parse
import datetime
from html import escape, unescape

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

RAVENGUARD_STEAM_ID64 = "76561198957446896"
ARMIN_STEAM_ID64 = "76561199484940606"

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


def remember_user(update):
    user = update.effective_user

    if user is None:
        return

    username = user.username

    if username in USERS:
        USERS[username] = user.id


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


def make_mentions(user_list):
    return " ".join(
        mention_user(name)
        for name in user_list
    )


def http_get(url, timeout=20):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SahebGimnet/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="ignore"
        )


def get_json(url, timeout=20):
    data = http_get(
        url,
        timeout
    )

    return json.loads(data)


def format_duration(seconds):
    try:
        seconds = int(seconds)

        minutes = seconds // 60
        remaining = seconds % 60

        return (
            str(minutes)
            + ":"
            + str(remaining).zfill(2)
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


def html_to_text(value):
    if not value:
        return ""

    value = re.sub(
        r"(?is)<script.*?</script>",
        " ",
        value
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
        r"(?is)</(p|div|li|h1|h2|h3|h4|h5|tr)>",
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


def translate_to_persian(text):
    if not text:
        return ""

    try:
        query = urllib.parse.quote(
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
            + query
        )

        data = get_json(
            url,
            15
        )

        result = ""

        if (
            isinstance(data, list)
            and len(data) > 0
        ):
            translations = data[0]

            if isinstance(
                translations,
                list
            ):
                for item in translations:
                    if (
                        isinstance(item, list)
                        and len(item) > 0
                    ):
                        result += str(
                            item[0]
                        )

        return result.strip()

    except Exception:
        return text


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
                "🎮 نتایج اخیر Armin",
                callback_data="armin_results"
            )
        ]
    ]

    return InlineKeyboardMarkup(
        keyboard
    )


async def start(update, context):
    remember_user(update)

    text = (
        "🎮 <b>صاب گیمنت</b>\n\n"
        "مدیریت بازی و هماهنگی بچه‌های گیمنت 🎯\n\n"
        "یکی از گزینه‌های زیر رو انتخاب کن:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


async def menu_command(update, context):
    remember_user(update)

    text = (
        "🎮 <b>صاب گیمنت</b>\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


async def handle_turbo(query):
    text = (
        "🎮 <b>دوتا ۲ - توربو</b>\n\n"
        "🔥 بازیکن‌های مورد نیاز:\n\n"
        + make_mentions(TURBO_USERS)
        + "\n\n"
        "بچه‌ها بریم توربو؟ 😎"
    )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


async def handle_ranked(query):
    text = (
        "🎮 <b>دوتا ۲ - رنک</b>\n\n"
        "🏆 بازیکن‌های مورد نیاز:\n\n"
        + make_mentions(RANKED_USERS)
        + "\n\n"
        "بریم رنک؟ 🔥"
    )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


async def handle_everyone(query):
    text = (
        "📢 <b>همرو صدا کن!</b>\n\n"
        + make_mentions(EVERYONE_USERS)
        + "\n\n"
        "🎮 بچه‌هاااااااااااااااا\n"
        "بریم بازی؟ 🔥"
    )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


async def handle_spectator(query):
    text = (
        "👀 <b>تماشاگر میخوام!</b>\n\n"
        + make_mentions(SPECTATOR_USERS)
        + "\n\n"
        "🎥 اگه بیکارید بیاید تماشا!"
    )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


async def handle_armin_call(query):
    keyboard = [
        [
            InlineKeyboardButton(
                "🔴 ورود به کال آرمین",
                url=MEET_ARMIN
            )
        ]
    ]

    await query.message.reply_text(
        "🔴 <b>کال آرمین سرندی</b>\n\n"
        "برای ورود روی دکمه زیر بزن:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


async def handle_ali_call(query):
    keyboard = [
        [
            InlineKeyboardButton(
                "🔵 ورود به کال علی",
                url=MEET_ALI
            )
        ]
    ]

    await query.message.reply_text(
        "🔵 <b>کال علی احدی</b>\n\n"
        "برای ورود روی دکمه زیر بزن:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


def get_hero_map():
    heroes = get_json(
        "https://api.opendota.com/api/heroStats",
        20
    )

    result = {}

    for hero in heroes:
        hero_id = hero.get("id")

        if hero_id is not None:
            result[int(hero_id)] = hero.get(
                "localized_name",
                "Unknown Hero"
            )

    return result


def get_recent_matches(account_id):
    url = (
        "https://api.opendota.com/api/players/"
        + account_id
        + "/matches?limit=5"
    )

    return get_json(
        url,
        30
    )


def request_account_refresh(account_id):
    url = (
        "https://api.opendota.com/api/players/"
        + account_id
        + "/refresh"
    )

    try:
        request = urllib.request.Request(
            url,
            method="POST",
            headers={
                "User-Agent": "SahebGimnet/1.0"
            }
        )

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
            "Account refresh error:",
            error
        )

        return None


def build_match_text(match, hero_map):
    match_id = match.get(
        "match_id"
    )

    player_slot = match.get(
        "player_slot",
        0
    )

    radiant = player_slot < 128

    radiant_win = match.get(
        "radiant_win"
    )

    if radiant_win is None:
        result_text = "❔ نتیجه نامشخص"

    elif radiant_win == radiant:
        result_text = "🟢 برد"

    else:
        result_text = "🔴 باخت"

    hero_id = match.get(
        "hero_id"
    )

    hero_name = "نامشخص"

    if hero_id:
        try:
            hero_name = hero_map.get(
                int(hero_id),
                "نامشخص"
            )
        except Exception:
            hero_name = "نامشخص"

    modes = {
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

    game_mode = modes.get(
        match.get("game_mode"),
        "Unknown"
    )

    duration = format_duration(
        match.get(
            "duration",
            0
        )
    )

    date_text = "نامشخص"

    start_time = match.get(
        "start_time"
    )

    if start_time:
        try:
            date_value = datetime.datetime.fromtimestamp(
                int(start_time)
            )

            date_text = date_value.strftime(
                "%Y-%m-%d %H:%M"
            )

        except Exception:
            pass

    kills = match.get(
        "kills",
        0
    )

    deaths = match.get(
        "deaths",
        0
    )

    assists = match.get(
        "assists",
        0
    )

    gpm = match.get(
        "gold_per_min",
        0
    )

    xpm = match.get(
        "xp_per_min",
        0
    )

    last_hits = match.get(
        "last_hits",
        0
    )

    hero_damage = match.get(
        "hero_damage",
        0
    )

    tower_damage = match.get(
        "tower_damage",
        0
    )

    text = (
        "<b>"
        + escape(result_text)
        + "</b>\n"
        "🦸 Hero: <b>"
        + escape(str(hero_name))
        + "</b>\n"
        "🎮 Mode: "
        + escape(str(game_mode))
        + "\n"
        "⏱ Duration: "
        + escape(str(duration))
        + "\n"
        "📅 Date: "
        + escape(str(date_text))
        + "\n\n"
        "⚔️ K/D/A: "
        + str(kills)
        + "/"
        + str(deaths)
        + "/"
        + str(assists)
        + "\n"
        "💰 GPM: "
        + format_number(gpm)
        + "\n"
        "⭐ XPM: "
        + format_number(xpm)
        + "\n"
        "🎯 Last Hits: "
        + format_number(last_hits)
        + "\n"
        "💥 Hero Damage: "
        + format_number(hero_damage)
        + "\n"
        "🏰 Tower Damage: "
        + format_number(tower_damage)
    )

    if match_id:
        text += (
            "\n\n"
            "🔗 <a href=\"https://www.opendota.com/matches/"
            + str(match_id)
            + "\">مشاهده جزئیات مچ</a>"
        )

    return text


async def handle_recent_results(query, account_id, player_name):
    loading = await query.message.reply_text(
        "🎮 <b>در حال گرفتن ۵ بازی اخیر " + escape(player_name) + "...</b>\\n"
        "⏳ یک لحظه صبر کن...",
        parse_mode="HTML"
    )

    try:
        hero_map = await asyncio.to_thread(
            get_hero_map
        )

        matches = await asyncio.to_thread(
            get_recent_matches,
            account_id
        )

        if not matches:
            await loading.edit_text(
                "🔄 بازی‌های " + escape(player_name) + " هنوز در OpenDota پیدا نشد.\\n"
                "⏳ دارم اطلاعات پروفایل را Refresh می‌کنم...",
                parse_mode="HTML"
            )

            await asyncio.to_thread(
                request_account_refresh,
                account_id
            )

            await asyncio.sleep(7)

            matches = await asyncio.to_thread(
                get_recent_matches,
                account_id
            )

        if not matches:
            await loading.edit_text(
                "❌ هنوز بازی‌های اخیر " + escape(player_name) + " پیدا نشد.\\n\\n"
                "OpenDota هنوز اطلاعات این اکانت را ندارد.\\n"
                "چند دقیقه بعد دوباره روی همین دکمه بزن.",
                parse_mode="HTML"
            )
            return

        await loading.edit_text(
            "🎮 <b>۵ بازی اخیر " + escape(player_name) + "</b>\\n\\n"
            "━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML"
        )

        for index, match in enumerate(matches[:5], 1):
            try:
                match_text = build_match_text(match, hero_map)

                await query.message.reply_text(
                    "🎮 <b>Match #" + str(index) + "</b>\\n\\n" + match_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )

            except Exception as error:
                print(
                    player_name + " match error:",
                    error
                )

                await query.message.reply_text(
                    "⚠️ خطا در نمایش Match #" + str(index) + "\\n" + escape(str(error)),
                    parse_mode="HTML"
                )

    except Exception as error:
        print(
            player_name + " error:",
            error
        )

        await loading.edit_text(
            "❌ خطا هنگام دریافت بازی‌های " + escape(player_name) + ".\\n\\n"
            "خطا:\\n" + escape(str(error)),
            parse_mode="HTML"
        )


async def handle_raven_results(query):
    await handle_recent_results(
        query,
        RAVENGUARD_ACCOUNT_ID,
        "RavenGuard"
    )


async def handle_armin_results(query):
    await handle_recent_results(
        query,
        ARMIN_ACCOUNT_ID,
        "Armin"
    )


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

        if "Gameplay Update" in title:
            patch_item = item
            break

        if "Gameplay Patch" in title:
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

    contents = patch_item.get(
        "contents",
        ""
    )

    official_url = patch_item.get(
        "url",
        ""
    )

    version = ""

    match = re.search(
        r"\b\d+\.\d+[a-z]?\b",
        title
    )

    if match:
        version = match.group(0)

    return {
        "title": title,
        "contents": contents,
        "url": official_url,
        "version": version
    }


def extract_patch_changes(contents):
    clean = html_to_text(
        contents
    )

    lines = [
        line.strip()
        for line in clean.splitlines()
        if line.strip()
    ]

    useful = []

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

    for line in lines:
        lower = line.lower()

        if len(line) < 20:
            continue

        if any(
            word in lower
            for word in keywords
        ):
            useful.append(line)

    if not useful:
        useful = lines

    result = []
    seen = set()

    for line in useful:
        normalized = line.lower()

        if normalized in seen:
            continue

        seen.add(normalized)

        if len(line) > 500:
            line = line[:500] + "..."

        result.append(line)

        if len(result) >= 10:
            break

    return result


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

        title = patch.get(
            "title",
            "Dota 2 Update"
        )

        version = patch.get(
            "version",
            ""
        )

        contents = patch.get(
            "contents",
            ""
        )

        changes = await asyncio.to_thread(
            extract_patch_changes,
            contents
        )

        if not changes:
            changes = [
                "تغییرات این آپدیت از منبع رسمی دریافت نشد."
            ]

        text = (
            "📰 <b>آخرین آپدیت Dota 2</b>\n\n"
            "📌 "
            + escape(title)
        )

        if version:
            text += (
                "\n🔢 Version: <b>"
                + escape(version)
                + "</b>"
            )

        text += (
            "\n\n"
            "🔥 <b>تغییرات مهم:</b>\n\n"
        )

        for index, change in enumerate(
            changes,
            1
        ):
            translated = await asyncio.to_thread(
                translate_to_persian,
                change
            )

            if not translated:
                translated = change

            text += (
                "▫️ <b>"
                + str(index)
                + ".</b> "
                + escape(translated)
                + "\n\n"
            )

            if len(text) > 3800:
                break

        official_url = patch.get(
            "url"
        )

        keyboard = []

        if official_url:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🌐 مشاهده منبع آپدیت",
                        url=official_url
                    )
                ]
            )

        await loading.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
                if keyboard
                else None
            ),
            disable_web_page_preview=True
        )

    except Exception as error:
        print(
            "Dota update error:",
            error
        )

        await loading.edit_text(
            "❌ <b>در دریافت آپدیت Dota 2 خطایی رخ داد.</b>\n\n"
            "خطا:\n"
            + escape(str(error)),
            parse_mode="HTML"
        )


async def button_handler(
    update,
    context
):
    query = update.callback_query

    await query.answer()

    remember_user(update)

    if query.data == "turbo":
        await handle_turbo(
            query
        )

    elif query.data == "ranked":
        await handle_ranked(
            query
        )

    elif query.data == "everyone":
        await handle_everyone(
            query
        )

    elif query.data == "spectator":
        await handle_spectator(
            query
        )

    elif query.data == "armin_call":
        await handle_armin_call(
            query
        )

    elif query.data == "ali_call":
        await handle_ali_call(
            query
        )

    elif query.data == "dota_update":
        await handle_dota_update(
            query
        )

    elif query.data == "raven_results":
        await handle_raven_results(
            query
        )

    elif query.data == "armin_results":
        await handle_armin_results(
            query
        )


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
