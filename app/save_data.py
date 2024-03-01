import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from dotenv import load_dotenv
from telegram.ext import CallbackContext

load_dotenv()


def get_order_datetime() -> str:
    return datetime.now(ZoneInfo("Europe/Kiev")).strftime("%H:%M %d-%m-%Y")


google_client = gspread.service_account_from_dict(
    json.loads(os.getenv("GOOGLE_SHEET_CREDENTIALS"))
)
sheet = google_client.open("Skeemans Cafe таблиця самопокупок")
work_sheet = sheet.worksheet("Аркуш1")


def save_client_data_to_google_sheet(context: CallbackContext) -> None:
    work_sheet.insert_rows(
        values=[
            [
                context.user_data["client_full_name"],
                context.user_data["product_name"],
                context.user_data["amount_of_product"],
                get_order_datetime(),
                context.user_data["payment_method"],
                context.user_data["amount_of_money"],
            ]
        ],
        row=2,
    )
    logging.info("✅ Google SpreadSheet has been filled!")
