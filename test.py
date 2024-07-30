import asyncio
import logging
import sys
import re

import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters.command import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

from credentials import BOT_TOKEN, CHANNEL_ID
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

DATABASE_CONFIG = {
    'host': "dpg-cqitjr8gph6c738u4sp0-a.frankfurt-postgres.render.com",
    'database': "tarbotdb",
    'user': "sreo",
    'password': "4INdhZzCVyZ7GagHBnJoPp38sAqg3iOS",
    'port': "5432"
}

async def get_db_connection():
    conn = await asyncpg.connect(
        user=DATABASE_CONFIG['user'],
        password=DATABASE_CONFIG['password'],
        database=DATABASE_CONFIG['database'],
        host=DATABASE_CONFIG['host'],
        port=DATABASE_CONFIG['port']
    )
    return conn

async def execute_query(query, params=None):
    conn = await get_db_connection()
    await conn.execute(query, *params if params else [])
    await conn.close()

async def fetch_query(query, params=None):
    conn = await get_db_connection()
    result = await conn.fetch(query, *params if params else [])
    await conn.close()
    return result


@dp.message(CommandStart())
async def handle_start(message: types.Message) -> None:
    # Extract the special link data (phone number and book ID)
    print(message.text)
    special_data = message.text.split('/start ')[1] if '/start ' in message.text else None
    if special_data:
        phone_number, book_id = special_data.split('_')
        msg_url = await fetch_query(f"SELECT b.book_location_link FROM books b WHERE b.book_id = {book_id};")
        pattern = r"https://t\.me/c/2151076535/(\d+)"
        match = re.match(pattern, msg_url[0]['book_location_link'])

        if match:
            msg_id = int(match.group(1))

        await message.reply(f"Assalomu alaykum, {message.from_user.first_name}!")
        
        # Forward book from private channel to user
        # Replace 'YOUR_CHANNEL_ID' with actual channel ID
        await bot.copy_message(chat_id=message.chat.id, from_chat_id=CHANNEL_ID, message_id=msg_id)
                # Store user information in bot_users table
        user_data_query = f"INSERT INTO bot_users (user_id, username, name, phone_number, created_at) VALUES ($1, $2, $3, $4, NOW()) ON CONFLICT (user_id) DO NOTHING;"
        await execute_query(user_data_query,(str(message.from_user.id), message.from_user.username, message.from_user.first_name, phone_number))
        

        user_additions_query = f"INSERT INTO bot_users_additions (user_id) VALUES ({str(message.from_user.id)}) ON CONFLICT (user_id) DO NOTHING;"
        await execute_query(user_additions_query)
    else:
        await message.reply(f"Assalomu alekum, {message.from_user.first_name}. \nXush kelibsiz!")

        user_data_query = f"INSERT INTO bot_users (user_id, username, name, phone_number, created_at) VALUES ($1, $2, $3, $4, NOW()) ON CONFLICT (user_id) DO NOTHING;"
        await execute_query(user_data_query,(str(message.from_user.id), message.from_user.username, message.from_user.first_name, None))
        
        user_additions_query = f"INSERT INTO bot_users_additions (user_id) VALUES ({str(message.from_user.id)}) ON CONFLICT (user_id) DO NOTHING;"
        await execute_query(user_additions_query)

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())