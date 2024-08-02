import asyncio
import logging
import sys
import re
import json

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters.command import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import Message

import database as db
import functions as fns
from State.userState import UserState, AdminState

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


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    # Extract the special link data (phone number and book ID)
    print(message.text)
    special_data = message.text.split('/start ')[1] if '/start ' in message.text else None
    if special_data:
        phone_number, book_id = special_data.split('_')
        msg_url = await db.fetch_query(f"SELECT b.book_location_link FROM books b WHERE b.book_id = {book_id};")
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
        await db.execute_query(user_data_query,(str(message.from_user.id), message.from_user.username, message.from_user.first_name, phone_number))
        

        user_additions_query = f"INSERT INTO bot_users_additions (user_id) VALUES ({str(message.from_user.id)}) ON CONFLICT (user_id) DO NOTHING;"
        await db.execute_query(user_additions_query)
    else:
        await message.reply(f"Assalomu alekum, {message.from_user.first_name}. \nXush kelibsiz!")

        user_data_query = f"INSERT INTO bot_users (user_id, username, name, phone_number, created_at) VALUES ($1, $2, $3, $4, NOW()) ON CONFLICT (user_id) DO NOTHING;"
        await db.execute_query(user_data_query,(str(message.from_user.id), message.from_user.username, message.from_user.first_name, None))
        
        user_additions_query = f"INSERT INTO bot_users_additions (user_id) VALUES ({str(message.from_user.id)}) ON CONFLICT (user_id) DO NOTHING;"
        await db.execute_query(user_additions_query)


@dp.message(UserState.message_text_id)
async def take_id(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await state.clear()
        message.answer("The process has been canceled.")
        return
    elif not message.text.isdigit():
        await message.answer("Please enter the correct message number.")
        await state.set_state(UserState.message_text_id)
        return
    await state.update_data(message_text_id=message.text)
    await message.answer("Please enter the new message text.")
    await state.set_state(UserState.message_text)

@dp.message(UserState.message_text)
async def take_text(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await state.clear()
        message.answer("The process has been canceled.")
        return
    new_data = await state.get_data()
    message_text_id = new_data.get('message_text_id')
    message_text = message.text

    with open('extras/messages.json', 'r') as file:
        data = json.load(file)
    
    data[f"msg{message_text_id}"] = message_text

    with open('extras/messages.json', 'w') as file:
        json.dump(data, file, indent=4)

    await message.answer(f"Message number {message_text_id} has been changed.")
    await state.clear()
    
@dp.message(AdminState.message_text)
async def send_to_all(message: Message, state: FSMContext) -> None:
    message_text = message.text

    users = await db.fetch_query("SELECT user_id, name FROM bot_users;")
    for user in users:
        try:
            await bot.send_message(chat_id=user['user_id'], text=message_text.replace("$name",user['name']), disable_web_page_preview=True)
        except Exception as e:
            if 'Forbidden' in str(e):
                await db.execute_query(f"DELETE FROM bot_users USING bot_users_additions WHERE bot_users.user_id = bot_users_additions.user_id AND bot_users.user_id = '{user['user_id']}';")
            print(e)
            continue
        print(f"Message sent to {user['name']} ({user['user_id']})")
        await asyncio.sleep(1)
    await state.clear()

@dp.message()
async def take_input(message: Message, state: FSMContext):
    print(message.text)
    if message.text == '/change_message':
        await message.answer("Please enter the message number you want to change.")
        await state.set_state(UserState.message_text_id)
        return
    elif message.text == '/send':
        await message.answer("Foydalanuvchilarga yuborishni xoxlagan xabarni kiriting.")
        await state.set_state(AdminState.message_text)
        return
    

async def main() -> None:

    scheduler = AsyncIOScheduler()
    scheduler.add_job(fns.send_message_to_users, 'interval', hours=2)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())