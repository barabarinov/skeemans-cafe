import logging
from typing import Callable, Any, Self

import telegram.error
from telegram import (
    User,
    Update,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Message as TelegramMessage,
)
from telegram.ext import CallbackContext
from telegram.constants import ParseMode

FORMATTER = Callable[[str], str]
FORMATTERS = list[FORMATTER]

logger = logging.getLogger(__name__)


class Message:
    def __init__(
        self,
        update: Update | None = None,
        context: CallbackContext | None = None,
        parse_mode: str = ParseMode.MARKDOWN_V2,
    ):
        self._update = update
        self._context = context
        self._parse_mode = parse_mode
        self._photo_path: str | None = None
        self._parts: list[str] = []
        self._reply_keyboard: list[list[str | KeyboardButton | InlineKeyboardButton]] = []
        self._reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None

    def add(self, message: str, *args: Any, formatters: FORMATTERS | None = None, **kwargs: Any) -> Self:
        formatters = formatters or []
        formatted_message = message.format(*args, **kwargs)
        for formatter in formatters:
            formatted_message = formatter(formatted_message)
        self._parts.append(formatted_message)

        return self

    def add_title(self, title: str, *args: Any, formatters: FORMATTERS | None = None, **kwargs: Any) -> Self:
        return self.add(title, *args, formatters=[escape, bold] + (formatters or []), **kwargs).add_newline()

    def add_line(self, message: str, *args: Any, formatters: FORMATTERS | None = None, **kwargs: Any) -> Self:
        return self.add_newline().add(message, *args, formatters=formatters, **kwargs)

    def add_newline(self, number: int = 1) -> Self:
        for i in range(number):
            self.add("\n")
        return self

    @staticmethod
    def create_inline_button(text: str, callback_id: str | None = None, **kwargs) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=text,
            callback_data=callback_id or text,
            **kwargs,
        )
    
    def add_inline_buttons(self, *buttons: list[InlineKeyboardButton]) -> Self:
        for button in buttons:
            self._reply_keyboard.append(button)
        self._reply_markup = InlineKeyboardMarkup(self._reply_keyboard)
        return self

    @staticmethod
    def create_reply_button(text: str, **kwargs) -> KeyboardButton:
        return KeyboardButton(text=text, **kwargs)

    def add_reply_buttons(self, *buttons: list[str | KeyboardButton], **keyboard_kwargs) -> Self:
        for button_list in buttons:
            self._reply_keyboard.append(button_list)
        self._reply_markup = ReplyKeyboardMarkup(self._reply_keyboard, **keyboard_kwargs)
        return self

    def reply_keyboard_remove(self) -> Self:
        self._reply_markup = ReplyKeyboardRemove()
        return self

    async def send(self, **kwargs) -> TelegramMessage | None:
        if self._photo_path:
            return await self.send_photo()

        await self._update.effective_message.reply_text(
            text="".join(self._parts),
            parse_mode=self._parse_mode,
            reply_markup=self._reply_markup,
            **kwargs,
        )

    def add_photo(self, photo) -> Self:
        self._photo_path = photo
        return self

    async def send_photo(self) -> TelegramMessage:
        try:
            return await self._context.bot.send_photo(
                chat_id=self._update.effective_user.id,
                photo=self._photo_path,
                caption="".join(self._parts),
                parse_mode=self._parse_mode,
                reply_markup=self._reply_markup,
            )
        except telegram.error.BadRequest as e:
            print(f"An error occurred in send_photo method: {e}")
            return await self._context.bot.send_photo(
                chat_id=self._update.effective_user.id,
                photo=open("pics/not_found.jpg", "rb"),
                caption="".join(self._parts),
                parse_mode=self._parse_mode,
                reply_markup=self._reply_markup,
            )

    async def send_message(self, user: User) -> None:
        try:
            await self._context.bot.send_message(
                chat_id=user.id,
                text="".join(self._parts),
                parse_mode=self._parse_mode,
                reply_markup=self._reply_markup,
            )
        except (telegram.error.BadRequest, telegram.error.Forbidden):
            logger.info(f"User {user.first_name} {user.id} blocked")
        else:
            logger.info(f"Bot sent message to User={user.first_name} with id={user.id}")

    async def edit_message_caption(self, message: TelegramMessage, new_caption: list[str]) -> None:
        await self._context.bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.message_id,
            caption="".join(new_caption),
            parse_mode=self._parse_mode,
            reply_markup=self._reply_markup,
        )

    async def edit_message_text(self) -> None:
        await self._context.bot.edit_message_text(
            chat_id=self._update.callback_query.message.chat_id,
            message_id=self._update.callback_query.message.message_id,
            text="".join(self._parts),
            parse_mode=self._parse_mode,
            reply_markup=self._reply_markup,
        )

    def __str__(self) -> str:
        return (
            f"Message(parts: {''.join(self._parts)} "
            f"reply_keyboard: {self._reply_keyboard} "
            f"photo_path: {self._photo_path})"
        )


TO_ESCAPE = {
    "\\",
    "_",
    "*",
    "[",
    "]",
    "(",
    ")",
    "~",
    ">",
    "#",
    "+",
    "-",
    "=",
    "|",
    "{",
    "}",
    ".",
    "!",
}


def escape(s: str) -> str:
    return "".join(map(lambda c: f"\\{c}" if c in TO_ESCAPE else c, str(s)))


def italic(s: str) -> str:
    return f"_{s}_"


def bold(s: str) -> str:
    return f"*{s}*"


def underscore(s: str) -> str:
    return f"__{s}__"


def strikethrough(s: str) -> str:
    return f"~{s}~"


def spoiler(s: str) -> str:
    return f"||{s}||"


class MemberMessage(Message):
    def edit_message_prayer_need(self, message: TelegramMessage, new_caption: str):
        self._parts[-1] = new_caption
        self.edit_message_caption(message, self._parts)
