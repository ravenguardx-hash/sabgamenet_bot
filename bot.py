import os
import threading
import asyncio
import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from datetime import datetime

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application,
CommandHandler,
CallbackQueryHandler,
MessageHandler,
ContextTypes,
filters,
)

TOKEN = os.environ.get("BOT_TOKEN")

# =========================================================

# شناسه کاربران

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

# =========================================================

# RavenGuard - Steam / Dota 2

# =========================================================

RAVENGUARD_NAME = "RavenGuard"

# SteamID64:

# 76561198957446896

#

# Dota 2 Account ID:

# 498590584

RAVENGUARD_ACCOUNT_ID = 498590584

# =========================================================

# Flask برای Render

# =========================================================

web_app = Flask(__name__)

@web_app.route("/")
def home():
return "Saheb Gimnet Bot is running!"

def run_web_server():
port = int(os.environ.get("PORT", 10000))
web_app.run(host="0.0.0.0", port=port)

# =========================================================

# ثبت کاربران

# =========================================================

async def save_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

```
user = update.effective_user

if user is None:
    return

if user.username:

    username = user.username.lower()

    for wanted in USERS:

        if username == wanted.lower():

            USERS[wanted] = user.id

            print(
                f"Registered @{wanted}: {user.id}"
            )
```

# =========================================================

# ساخت منشن واقعی

# =========================================================

def mention(username):

```
user_id = USERS.get(username)

if user_id is None:
    return f"@{username}"

return f'<a href="tg://user?id={user_id}">@{username}</a>'
```

def make_mentions(usernames):

```
return "\n".join(
    mention(username)
    for username in usernames
)
```

# =========================================================

# HTML Parser

# =========================================================

class SimpleHTMLParser(HTMLParser):

```
def __init__(self):

    super().__init__()

    self.text_parts = []

    self.skip = False

def handle_starttag(self, tag, attrs):

    if tag in [
        "script",
        "style",
        "noscript",
        "svg"
    ]:
        self.skip = True

    if tag in [
        "br",
        "p",
        "div",
        "li",
        "h1",
        "h2",
        "h3",
        "h4"
    ]:

        self.text_parts.append("\n")

def handle_endtag(self, tag):

    if tag in [
        "script",
        "style",
        "noscript",
        "svg"
    ]:
        self.skip = False

    if tag in [
        "p",
        "div",
        "li",
        "h1",
        "h2",
        "h3",
        "h4"
    ]:

        self.text_parts.append("\n")

def handle_data(self, data):

    if not self.skip:

        text = data.strip()

        if text:
            self.text_parts.append(text)

def get_text(self):

    text = " ".join(self.text_parts)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()
```

def html_to_text(html):

```
parser = SimpleHTMLParser()

parser.feed(html)

return parser.get_text()
```

# =========================================================

# دریافت URL

# =========================================================

def fetch_url(url, timeout=25):

```
request = urllib.request.Request(
    url,
    headers={
        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/154.0 Safari/537.36"
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
```

# =========================================================

# پیدا کردن آخرین Gameplay Patch

# =========================================================

def get_latest_patch():

```
steam_api = (
    "https://api.steampowered.com/"
    "ISteamNews/GetNewsForApp/v0002/"
    "?appid=570"
    "&count=30"
    "&maxlength=100000"
    "&format=json"
)

raw = fetch_url(steam_api)

data = json.loads(raw)

news_items = (
    data
    .get("appnews", {})
    .get("newsitems", [])
)

for item in news_items:

    title = item.get(
        "title",
        ""
    )

    if "Gameplay Patch" in title:

        match = re.search(
            r"(\d+\.\d+[a-z]?)",
            title
        )

        if not match:
            continue

        version = match.group(1)

        return {
            "title": title,
            "version": version,
            "url": item.get(
                "url",
                ""
            )
        }

return None
```

# =========================================================

# دریافت Patch Notes رسمی

# =========================================================

def get_patch_notes(version):

```
url = (
    f"https://www.dota2.com/"
    f"patches/{version}?l=english"
)

html = fetch_url(url)

text = html_to_text(html)

return {
    "url": url,
    "text": text
}
```

# =========================================================

# پیدا کردن تغییرات مهم

# =========================================================

CHANGE_PATTERNS = [
"increased",
"decreased",
"reduced",
"increased from",
"decreased from",
"changed from",
"changed to",
"replaced with",
"replaced",
"now",
"removed",
"added",
"damage",
"cooldown",
"cost",
"duration",
"health",
"mana",
"armor",
"movement speed",
"attack speed",
"range",
"radius",
"lifesteal",
"gold",
"experience",
]

def extract_changes(text):

```
pieces = re.split(
    r"(?<=[.!?])\s+|(?=Hero Updates)|(?=Item Updates)|(?=General Updates)",
    text
)

candidates = []

for piece in pieces:

    piece = piece.strip()

    if len(piece) < 20:
        continue

    lower = piece.lower()

    if not any(
        pattern in lower
        for pattern in CHANGE_PATTERNS
    ):
        continue

    if "dota 2" in lower and len(piece) > 300:
        continue

    if len(piece) > 350:
        piece = piece[:347] + "..."

    if piece not in candidates:
        candidates.append(piece)

return candidates
```

# =========================================================

# امتیازدهی برای تغییرات مهم‌تر

# =========================================================

def importance_score(text):

```
lower = text.lower()

score = 0

important_words = {

    "damage": 3,
    "cooldown": 3,
    "cost": 3,
    "gold": 3,
    "lifesteal": 3,
    "mana": 2,
    "health": 2,
    "armor": 2,
    "movement speed": 2,
    "attack speed": 2,
    "range": 2,
    "duration": 2,
    "talent": 3,
    "ability": 2,
    "hero": 2,
    "item": 2,

}

for word, value in important_words.items():

    if word in lower:
        score += value

if re.search(
    r"\d+%|\d+\.\d+|\d+",
    text
):
    score += 2

if "increased" in lower:
    score += 1

if "decreased" in lower:
    score += 1

if "replaced" in lower:
    score += 2

return score
```

# =========================================================

# ترجمه انگلیسی به فارسی

# =========================================================

def translate_to_persian(text):

```
try:

    encoded = urllib.parse.quote(text)

    url = (
        "https://translate.googleapis.com/"
        "translate_a/single"
        "?client=gtx"
        "&sl=en"
        "&tl=fa"
        "&dt=t"
        f"&q={encoded}"
    )

    raw = fetch_url(
        url,
        timeout=15
    )

    data = json.loads(raw)

    translated = ""

    for part in data[0]:

        if part[0]:
            translated += part[0]

    if translated.strip():

        return translated.strip()

except Exception as error:

    print(
        "Translation error:",
        error
    )

return text
```

# =========================================================

# ساخت خلاصه آپدیت

# =========================================================

async def create_dota_update():

```
try:

    latest = await asyncio.to_thread(
        get_latest_patch
    )

    if not latest:

        return (
            "❌ نتونستم آخرین آپدیت رسمی "
            "Dota 2 رو پیدا کنم."
        )

    version = latest["version"]

    patch = await asyncio.to_thread(
        get_patch_notes,
        version
    )

    changes = extract_changes(
        patch["text"]
    )

    if not changes:

        return (
            "📰 <b>آخرین آپدیت Dota 2</b>\n\n"
            f"🎮 Patch <b>{version}</b>\n\n"
            "❌ تغییرات آپدیت از صفحه رسمی "
            "قابل استخراج نبود.\n\n"
            f'<a href="{patch["url"]}">'
            "🔗 مشاهده Patch Notes کامل"
            "</a>"
        )

    changes.sort(
        key=importance_score,
        reverse=True
    )

    important_changes = changes[:8]

    translated_changes = []

    for change in important_changes:

        translated = await asyncio.to_thread(
            translate_to_persian,
            change
        )

        translated_changes.append(
            translated
        )

    message = (
        "📰 <b>آخرین آپدیت Dota 2</b>\n\n"
        f"🎮 <b>Patch {version}</b>\n\n"
        "🔥 <b>مهم‌ترین تغییرات:</b>\n\n"
    )

    for change in translated_changes:

        message += (
            "• "
            + change
            + "\n\n"
        )

    message += (
        "━━━━━━━━━━━━━━\n"
        "📌 این خلاصه به‌صورت خودکار "
        "از آخرین Patch رسمی تهیه شده.\n\n"
        f'<a href="{patch["url"]}">'
        "🔗 Patch Notes کامل"
        "</a>"
    )

    return message

except Exception as error:

    print(
        "Dota update error:",
        error
    )

    return (
        "❌ هنگام بررسی آخرین آپدیت Dota 2 "
        "مشکلی پیش اومد.\n\n"
        "چند لحظه بعد دوباره امتحان کن."
    )
```

# =========================================================

# RavenGuard - دریافت 5 بازی آخر

# =========================================================

def get_recent_matches():

```
url = (
    "https://api.opendota.com/api/players/"
    f"{RAVENGUARD_ACCOUNT_ID}/matches"
    "?limit=5"
)

raw = fetch_url(
    url,
    timeout=30
)

data = json.loads(raw)

return data[:5]
```

# =========================================================

# گرفتن اطلاعات هیرو

# =========================================================

def get_heroes():

```
url = "https://api.opendota.com/api/heroStats"

raw = fetch_url(
    url,
    timeout=30
)

return json.loads(raw)
```

# =========================================================

# تبدیل نام هیرو

# =========================================================

def hero_name(hero_id, heroes):

```
for hero in heroes:

    if hero.get("id") == hero_id:

        return hero.get(
            "localized_name",
            "Unknown Hero"
        )

return "Unknown Hero"
```

# =========================================================

# نوع بازی

# =========================================================

def game_mode_name(game_mode):

```
modes = {

    1: "All Pick",
    2: "Captains Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    6: "Intro",
    7: "Diretide",
    8: "Reverse Captains Mode",
    9: "Greeviling",
    10: "Tutorial",
    11: "Mid Only",
    12: "Least Played",
    13: "Limited Heroes",
    14: "Compendium",
    15: "Custom",
    16: "Captain's Draft",
    17: "Balanced Draft",
    18: "Ability Draft",
    19: "Event",
    20: "All Random Death Match",
    21: "1v1 Solo Mid",
    22: "Ranked All Pick",
    23: "Turbo",
    24: "Mutation",
    25: "Co-op Bots",
    26: "Ranked Turbo",
    27: "Ranked Ability Draft",

}

return modes.get(
    game_mode,
    "Unknown"
)
```

# =========================================================

# تبدیل زمان بازی

# =========================================================

def format_duration(seconds):

```
if not seconds:
    return "نامشخص"

minutes = seconds // 60
remaining_seconds = seconds % 60

return (
    f"{minutes}:{remaining_seconds:02d}"
)
```

# =========================================================

# تبدیل زمان تاریخ

# =========================================================

def format_date(timestamp):

```
if not timestamp:
    return "نامشخص"

try:

    date = datetime.fromtimestamp(
        timestamp
    )

    return date.strftime(
        "%Y/%m/%d - %H:%M"
    )

except Exception:

    return "نامشخص"
```

# =========================================================

# ساخت خروجی 5 بازی اخیر RavenGuard

# =========================================================

async def create_recent_results():

```
try:

    matches = await asyncio.to_thread(
        get_recent_matches
    )

    if not matches:

        return (
            "❌ برای RavenGuard "
            "بازی اخیری پیدا نشد."
        )

    heroes = await asyncio.to_thread(
        get_heroes
    )

    message = (
        "🎮 <b>نتایج اخیر RavenGuard</b>\n\n"
    )

    for index, match in enumerate(
        matches[:5],
        start=1
    ):

        player_slot = match.get(
            "player_slot",
            0
        )

        radiant = player_slot < 128

        radiant_win = match.get(
            "radiant_win"
        )

        if radiant_win is None:

            result = "❔"

        else:

            won = (
                radiant == radiant_win
            )

            if won:
                result = "🟢 <b>WIN</b>"
            else:
                result = "🔴 <b>LOSS</b>"

        hero = hero_name(
            match.get("hero_id"),
            heroes
        )

        mode = game_mode_name(
            match.get("game_mode")
        )

        duration = format_duration(
            match.get("duration")
        )

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

        date = format_date(
            match.get("start_time")
        )

        match_id = match.get(
            "match_id"
        )

        match_url = (
            f"https://www.opendota.com/matches/"
            f"{match_id}"
        )

        message += (
            f"<b>{index}️⃣ {result}</b>\n"
            f"🦸 هیرو: <b>{hero}</b>\n"
            f"🎮 مود: <b>{mode}</b>\n"
            f"⏱ مدت: <b>{duration}</b>\n"
            f"📅 تاریخ: <b>{date}</b>\n\n"

            f"⚔️ K/D/A: "
            f"<b>{kills}/{deaths}/{assists}</b>\n"
            f"💰 GPM: <b>{gpm}</b>\n"
            f"⭐ XPM: <b>{xpm}</b>\n"
            f"🎯 Last Hits: <b>{last_hits}</b>\n"
            f"💥 Hero Damage: <b>{hero_damage:,}</b>\n"
            f"🏰 Tower Damage: <b>{tower_damage:,}</b>\n\n"

            f'<a href="{match_url}">'
            "🔗 مشاهده جزئیات بازی"
            "</a>\n"

            "━━━━━━━━━━━━━━\n\n"
        )

    return message

except Exception as error:

    print(
        "Recent matches error:",
        error
    )

    return (
        "❌ هنگام دریافت نتایج اخیر "
        "RavenGuard مشکلی پیش اومد.\n\n"
        "چند لحظه بعد دوباره امتحان کن."
    )
```

# =========================================================

# منوی اصلی

# =========================================================

async def start(
update: Update,
context: ContextTypes.DEFAULT_TYPE
):

```
keyboard = [

    [
        InlineKeyboardButton(
            "🎮 دوتا ۲ (توربو)",
            callback_data="turbo"
        )
    ],

    [
        InlineKeyboardButton(
            "🎮 دوتا ۲ (رنک)",
            callback_data="rank"
        )
    ],

    [
        InlineKeyboardButton(
            "📢 همرو صدا کن",
            callback_data="everyone"
        )
    ],

    [
        InlineKeyboardButton(
            "👀 تماشاگر میخوام",
            callback_data="spectator"
        )
    ],

    [
        InlineKeyboardButton(
            "🔴 لینک کال آرمین سرندی",
            url="https://meet.google.com/gto-izfj-hmj"
        )
    ],

    [
        InlineKeyboardButton(
            "🔵 لینک کال علی احدی",
            url="https://meet.google.com/wba-iyzm-hdu"
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
]

reply_markup = InlineKeyboardMarkup(
    keyboard
)

await update.message.reply_text(
    "درخواست از اعضا برای بازی:",
    reply_markup=reply_markup
)
```

# =========================================================

# عملکرد دکمه‌ها

# =========================================================

async def button_click(
update: Update,
context: ContextTypes.DEFAULT_TYPE
):

```
query = update.callback_query

await query.answer()


# =====================================================
# توربو
# =====================================================

if query.data == "turbo":

    users = [
        "AlieAhadi",
        "Arminsarandii",
        "Ballfreak",
        "Mojtaba_bd",
        "Reza_rus",
        "Jey_0Oj",
    ]

    text = (
        "توربو میاید؟\n\n"
        + make_mentions(users)
    )

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode="HTML",
    )

    return


# =====================================================
# رنک
# =====================================================

elif query.data == "rank":

    users = [
        "AlieAhadi",
        "Arminsarandii",
        "Ballfreak",
        "Mojtaba_bd",
        "Reza_rus",
        "a_p_karimi",
    ]

    text = (
        "رنک میاید؟\n\n"
        + make_mentions(users)
    )

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode="HTML",
    )

    return


# =====================================================
# همرو صدا کن
# =====================================================

elif query.data == "everyone":

    users = [
        "AlieAhadi",
        "Arminsarandii",
        "Ballfreak",
        "Mojtaba_bd",
        "Reza_rus",
        "a_p_karimi",
        "alimakkiiii",
        "Ahmad_b78",
    ]

    text = (
        "اقا سلام بر همگی\n\n"
        + make_mentions(users)
    )

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode="HTML",
    )

    return


# =====================================================
# تماشاگر
# =====================================================

elif query.data == "spectator":

    users = [
        "alimakkiiii",
        "Ahmad_b78",
    ]

    text = (
        "تماشاگرا چخبر؟\n\n"
        + make_mentions(users)
    )

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode="HTML",
    )

    return


# =====================================================
# آپدیت دوتا ۲
# =====================================================

elif query.data == "dota_update":

    chat_id = query.message.chat_id

    loading_message = (
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🔎 دارم آخرین آپدیت "
                "Dota 2 رو بررسی می‌کنم..."
            )
        )
    )

    result = await create_dota_update()

    try:

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=loading_message.message_id,
            text=result,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as error:

        print(
            "Edit message error:",
            error
        )

    return


# =====================================================
# نتایج اخیر RavenGuard
# =====================================================

elif query.data == "raven_results":

    chat_id = query.message.chat_id

    loading_message = (
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🔎 دارم ۵ بازی آخر "
                "RavenGuard رو بررسی می‌کنم..."
            )
        )
    )

    result = await create_recent_results()

    try:

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=loading_message.message_id,
            text=result,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as error:

        print(
            "RavenGuard edit error:",
            error
        )

    return
```

# =========================================================

# اجرای ربات

# =========================================================

def main():

```
if not TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is missing!"
    )

threading.Thread(
    target=run_web_server,
    daemon=True
).start()

application = (
    Application
    .builder()
    .token(TOKEN)
    .build()
)

application.add_handler(
    MessageHandler(
        filters.ALL & ~filters.COMMAND,
        save_users
    )
)

application.add_handler(
    CommandHandler(
        "start",
        start
    )
)

application.add_handler(
    CallbackQueryHandler(
        button_click
    )
)

print(
    "Saheb Gimnet Bot started!"
)

application.run_polling()
```

if **name** == "**main**":
main()
