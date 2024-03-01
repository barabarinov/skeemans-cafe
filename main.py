import os
import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.handlers.buttons import start, show_menu
from app.handlers.purchase_dialog import new_purchase_conversation_handler

from dotenv import load_dotenv

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


if __name__ == "__main__":
    load_dotenv()

    IS_HEROKU = os.getenv("IS_HEROKU", "true").lower() == "true"
    PORT = int(os.environ.get("PORT", 5000))
    TOKEN = os.getenv("TOKEN")

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.Regex("^Меню.*") & ~filters.COMMAND, show_menu)
    )
    application.add_handler(new_purchase_conversation_handler)

    if IS_HEROKU:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"https://skeemans-cafe-telegram-bot-c181abfcfd34.herokuapp.com/{TOKEN}",
        )
    else:
        application.run_polling()
