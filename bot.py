import os
import threading

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

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Saheb Gimnet Bot is running!"


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


async def save_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user is None:
        return

    if user.username:
        username = user.username.lower()

        for wanted in USERS:
            if username == wanted.lower():
                USERS[wanted] = user.id
                print(f"Registered @{wanted}: {user.id}")


def mention(username):
    user_id = USERS.get(username)

    if user_id is None:
        return f"@{username}"

    return f'<a href="tg://user?id={user_id}">@{username}</a>'


def make_mentions(usernames):
    return "\n".join(mention(username) for username in usernames)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
            "👀 تماشاچی میخوام",
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
]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "درخواست از اعضا برای بازی:",
        reply_markup=reply_markup
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "turbo":

        users = [
            "AlieAhadi",
            "Arminsarandii",
            "Ballfreak",
            "Mojtaba_bd",
            "Reza_rus",
            "Jey_0Oj",
        ]

        text = "توربو میاید؟\n\n" + make_mentions(users)

    elif query.data == "rank":

        users = [
            "AlieAhadi",
            "Arminsarandii",
            "Ballfreak",
            "Mojtaba_bd",
            "Reza_rus",
            "a_p_karimi",
        ]

        text = "رنک میاید؟\n\n" + make_mentions(users)

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

        text = "اقا سلام بر همگی\n\n" + make_mentions(users)

    elif query.data == "spectator":

        users = [
            "alimakkiiii",
            "Ahmad_b78",
        ]

        text = "تماشاگرا چخبر؟\n\n" + make_mentions(users)

    else:
        return

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode="HTML",
    )


def main():

    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing!")

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            save_users
        )
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(button_click)
    )

    print("Saheb Gimnet Bot started!")

    application.run_polling()


if __name__ == "__main__":
    main()
