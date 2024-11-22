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

proove_poll = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ha", callback_data="proove"),
            InlineKeyboardButton(text="Yo'q", callback_data="cancel")
        ]
    ]
)

change_books = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Qo'shish", callback_data="add_book"),
            InlineKeyboardButton(text="O'chirish", callback_data="remove_book")
        ],
        [
            InlineKeyboardButton(text="Tahrirlash", callback_data="edit_book")
        ],
        [
            InlineKeyboardButton(text="Bekor qilish", callback_data="cancel")
        ]
    ]
)

book_id_proove = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ha", callback_data="yes_change"),
            InlineKeyboardButton(text="Yo'q", callback_data="no_change")
        ]
    ]
)