from telegram import Update
from telegram.ext import ContextTypes

from app.message import Message, escape


async def show_menu(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = Message(update=update, context=context)
    message.add("Ось будь ласочка наше меню", formatters=[escape])
    await message.add_photo(open("pics/menu.jpg", "rb")).send()


async def start(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = Message(update=update)
    message.add("Зроби свій вибір: ", formatters=[escape])

    menu_button = message.create_reply_button(text="Меню")
    buy_button = message.create_reply_button(text="Купити")
    message.add_reply_buttons(
        [menu_button, buy_button],
        one_time_keyboard=False,
        resize_keyboard=True,
    )
    await message.send()
