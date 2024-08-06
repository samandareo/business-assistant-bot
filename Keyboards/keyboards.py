from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

contact_with_admin = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Murojaat")
        ],
    ],
    resize_keyboard=True
)

proove_message = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ha", callback_data="proove"),
            InlineKeyboardButton(text="Yo'q", callback_data="cancel")
        ]
    ],
    resize_keyboard=True
)