text = (
            "تماشاگرا چخبر؟\n\n"
            + make_mentions(users)
        )

    else:
        return

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode="HTML",
    )


# =========================
# اجرای ربات
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing!"
        )

    # وب‌سرور Render
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # ثبت اعضایی که در گروه پیام می‌دهند
    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            save_users
        )
    )

    # /start
    application.add_handler(
        CommandHandler("start", start)
    )

    # دکمه‌ها
    application.add_handler(
        CallbackQueryHandler(button_click)
    )

    print("Saheb Gimnet Bot started!")

    application.run_polling()


if name == "main":
    main()
