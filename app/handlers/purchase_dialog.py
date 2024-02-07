import os
from enum import auto, IntEnum

import emoji
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)

from app.message import Message, escape
from app.save_data import save_client_data_to_google_sheet

load_dotenv()
BANK_LINK = os.getenv("BANK_LINK")

# callbacks_id
CARD = "Карта"
CASH = "Готівка"
CANCEL = "Відмінити"

# Emoji
HELLO = emoji.emojize(":vulcan_salute_medium-light_skin_tone:")
SAVORING_FOOD = emoji.emojize(":face_savoring_food:")
OK_HAND = emoji.emojize(":OK_hand_medium-light_skin_tone:")
THUMBS_UP = emoji.emojize(":thumbs_up_medium-light_skin_tone:")
CREDIT_CARD = emoji.emojize(":credit_card:")
MONEY = emoji.emojize(":money_with_wings:")
MONEY_BAG = emoji.emojize(":money_bag:")
CHECK_MARK = emoji.emojize(":check_mark_button:")
THUMBS_POINTING_DOWN = emoji.emojize(":backhand_index_pointing_down_medium-light_skin_tone:")
PRAYING_HANDS = emoji.emojize(":folded_hands_medium-light_skin_tone:")
NUMBERS = emoji.emojize(":input_numbers:")
KISSING_SMILE = emoji.emojize(":face_blowing_a_kiss:")


class NewPurchase(IntEnum):
    PRODUCT_AMOUNT = auto()
    PAYMENT_METHOD = auto()
    AMOUNT_OF_MONEY = auto()
    CLIENT_NAME = auto()
    SAVE_TO_GOOGLE_SHEET = auto()


def create_cancel_inline_button(message: Message) -> Message:
    cancel_button = message.create_inline_button(text=CANCEL, callback_id=CANCEL)
    return message.add_inline_buttons([cancel_button])


async def new_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> NewPurchase:
    message = Message(update=update, context=context)
    message.add(
        f"{SAVORING_FOOD} Зголоднів? Напиши назву смаколика, "
        f"що ти хочеш придбати (ОБОВ'ЯЗКОВО вказати об'єм і смак)",
        formatters=[escape],
    )
    await create_cancel_inline_button(message).send()

    return NewPurchase.PRODUCT_AMOUNT


async def get_product_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> NewPurchase:
    context.user_data["product_name"] = update.message.text
    # save product`s name & get product amount
    message = Message(update=update, context=context)
    message.add(
        f"{OK_HAND} Добре. Тепер напиши кількість товару будь ласка! {THUMBS_POINTING_DOWN}", formatters=[escape]
    )
    await create_cancel_inline_button(message).send()

    return NewPurchase.PAYMENT_METHOD


async def get_clients_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> NewPurchase:
    context.user_data["amount_of_product"] = update.message.text
    # save product amount & get client`s payment method
    message = Message(update=update, context=context)
    message.add(f"{THUMBS_UP} Чудово. Далі обери спосіб оплати!", formatters=[escape])

    card_button = message.create_inline_button(f"{CARD} {CREDIT_CARD}", callback_id=CARD)
    cash_button = message.create_inline_button(f"{CASH} {MONEY}", callback_id=CASH)
    message.add_inline_buttons([card_button, cash_button])
    await create_cancel_inline_button(message).send()

    return NewPurchase.AMOUNT_OF_MONEY


async def get_amount_of_money(update: Update, context: ContextTypes.DEFAULT_TYPE) -> NewPurchase:
    context.user_data["payment_method"] = update.callback_query.data
    # save clients payment method & get amount of money
    message = Message(update=update, context=context)

    if update.callback_query.data in CARD:
        payment_message = Message(update=update, context=context)
        payment_message.add("Номер карти для оплати покупки: ", formatters=[escape])
        await payment_message.send()

        message.add(BANK_LINK, formatters=[escape])
    else:
        message.add(f"Покладіть готівку у касу будь ласка! {MONEY_BAG}", formatters=[escape])
    await message.send()

    second_message = Message(update=update, context=context)
    second_message.add(f"Введіть внесену суму {NUMBERS}:")

    await create_cancel_inline_button(second_message).send()

    return NewPurchase.CLIENT_NAME


async def get_client_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> NewPurchase:
    context.user_data["amount_of_money"] = update.message.text
    # save amount of money & get client`s fullname here
    message = Message(update=update, context=context)
    message.add(f"Введіть своє прізвище та ім'я {THUMBS_POINTING_DOWN}: ")

    await create_cancel_inline_button(message).send()

    return NewPurchase.SAVE_TO_GOOGLE_SHEET


async def save_to_google_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["client_full_name"] = update.message.text

    save_client_data_to_google_sheet(context=context)

    message = Message(update=update, context=context)
    await message.add(
        f"{CHECK_MARK} Покупка успішно записана! А вам смачного! {KISSING_SMILE}", formatters=[escape]
    ).send()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = Message(update=update, context=context)
    await message.add(f"До зустрічі! {PRAYING_HANDS}", formatters=[escape]).edit_message_text()

    return ConversationHandler.END


new_purchase_conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^Купити.*") & ~filters.COMMAND, new_purchase)],
    states={
        NewPurchase.PRODUCT_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_amount),
        ],
        NewPurchase.PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_clients_payment_method)],
        NewPurchase.AMOUNT_OF_MONEY: [
            CallbackQueryHandler(get_amount_of_money, pattern=f"{CARD}|{CASH}"),
        ],
        NewPurchase.CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_fullname)],
        NewPurchase.SAVE_TO_GOOGLE_SHEET: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_to_google_sheet)],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern=CANCEL),
    ],
)
