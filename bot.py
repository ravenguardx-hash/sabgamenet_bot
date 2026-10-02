import os
import threading
import asyncio
import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

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


# =========================================================
# ساخت منشن واقعی
# =========================================================

def mention(username):

    user_id = USERS.get(username)

    if user_id is None:
        return f"@{username}"

    return f'<a href="tg://user?id={user_id}">@{username}</a>'


def make_mentions(usernames):

    return "\n".join(
        mention(username)
        for username in usernames
    )


# =========================================================
# HTML Parser
# برای خواندن Patch Notes
# =========================================================

class SimpleHTMLParser(HTMLParser):

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


def html_to_text(html):

    parser = SimpleHTMLParser()

    parser.feed(html)

    return parser.get_text()


# =========================================================
# دریافت URL
# =========================================================

def fetch_url(url, timeout=25):

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


# =========================================================
# پیدا کردن آخرین Gameplay Patch
# =========================================================

def get_latest_patch():

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


# =========================================================
# دریافت Patch Notes رسمی
# =========================================================

def get_patch_notes(version):

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

    # متن را به جمله‌های تقریبی تقسیم می‌کنیم
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

        # حذف موارد مربوط به منوی سایت
        if "dota 2" in lower and len(piece) > 300:
            continue

        # طول مناسب برای تلگرام
        if len(piece) > 350:
            piece = piece[:347] + "..."

        if piece not in candidates:
            candidates.append(piece)

    return candidates


# =========================================================
# امتیازدهی برای پیدا کردن تغییرات مهم‌تر
# =========================================================

def importance_score(text):

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

    # تغییرات عددی معمولاً مهم‌تر هستند
    if re.search(
        r"\d+%|\d+\.\d+|\d+",
        text
    ):
        score += 2

    # تغییرات بزرگ‌تر
    if "increased" in lower:
        score += 1

    if "decreased" in lower:
        score += 1

    if "replaced" in lower:
        score += 2

    return score


# =========================================================
# ترجمه انگلیسی به فارسی
# از سرویس عمومی Google Translate استفاده می‌شود.
# اگر در دسترس نباشد، متن انگلیسی نمایش داده می‌شود.
# =========================================================

def translate_to_persian(text):

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


# =========================================================
# ساخت خلاصه آپدیت
# =========================================================

async def create_dota_update():

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
                f'🔗 <a href="{patch["url"]}">'
                "مشاهده Patch Notes کامل"
                "</a>"
            )

        # مرتب کردن بر اساس اهمیت
        changes.sort(
            key=importance_score,
            reverse=True
        )

        # فقط مهم‌ترین‌ها
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
            f'🔗 <a href="{patch["url"]}">'
            "Patch Notes کامل"
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


# =========================================================
# منوی اصلی
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(
        "درخواست از اعضا برای بازی:",
        reply_markup=reply_markup
    )


# =========================================================
# عملکرد دکمه‌ها
# =========================================================

async def button_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    # -----------------------------------------
    # توربو
    # -----------------------------------------

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

    # -----------------------------------------
    # رنک
    # -----------------------------------------

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

    # -----------------------------------------
    # همرو صدا کن
    # -----------------------------------------

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

    # -----------------------------------------
    # تماشاگر
    # -----------------------------------------

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

    # -----------------------------------------
    # آپدیت دوتا ۲
    # -----------------------------------------

    elif query.data == "dota_update":

        chat_id = query.message.chat_id

        # پیام موقت
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


# =========================================================
# اجرای ربات
# =========================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN is missing!"
        )

    # اجرای Flask برای Render
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # ساخت ربات
    application = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # ثبت کاربران گروه
    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            save_users
        )
    )

    # دستور /start
    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # دکمه‌ها
    application.add_handler(
        CallbackQueryHandler(
            button_click
        )
    )

    print(
        "Saheb Gimnet Bot started!"
    )

    application.run_polling()


if __name__ == "__main__":
    main()
