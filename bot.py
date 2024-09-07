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
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile

from database import execute_query, fetch_query, init_db
import functions as fns
from State.userState import UserState, AdminState, AdminStateOne, UserMessagesToAdmin
import Keyboards.keyboards as kb

from credentials import admins
from Userbot.userbot import initialize_clients
from Userbot.assign import assign_task_to_operator



from credentials import BOT_TOKEN, CHANNEL_ID, APPEAL_CHANNEL_ID, TEST_BOT_TOKEN, REPORT_ID
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    # Extract the special link data (phone number and book ID)
    print(message.text)
    special_data = message.text.split('/start ')[1] if '/start ' in message.text else None
    print(special_data)
    if special_data and special_data == 'all':
        await message.reply(f"Assalomu alekum, {message.from_user.first_name}. \nXush kelibsiz!\n\nQuyida barcha kitoblarni ko'rishingiz mumkin!", reply_markup=kb.contact_with_admin)
        msg_url = await fetch_query(f"SELECT b.book_location_link FROM books b;")
        for msg in msg_url:
            pattern = r"https://t\.me/c/2151076535/(\d+)"
            match = re.match(pattern, msg['book_location_link'])
            if match:
                msg_id = int(match.group(1))
            
            if msg_id ==31:
                continue
            await bot.copy_message(chat_id=message.chat.id, from_chat_id=CHANNEL_ID, message_id=msg_id)
        user_data_query = f"INSERT INTO bot_users (user_id, username, name, phone_number, created_at) VALUES ($1, $2, $3, $4, NOW()) ON CONFLICT (user_id) DO NOTHING;"
    elif special_data:
        phone_number, book_id = special_data.split('_')
        print(phone_number, book_id)
        msg_url = await fetch_query(f"SELECT b.book_location_link FROM books b WHERE b.book_id = {book_id};")
        pattern = r"https://t\.me/c/2151076535/(\d+)"
        match = re.match(pattern, msg_url[0]['book_location_link'])

        if match:
            msg_id = int(match.group(1))
        await message.reply(f"Assalomu alaykum, {message.from_user.first_name}!",reply_markup=kb.contact_with_admin)
        
        # Forward book from private channel to user
        # Replace 'YOUR_CHANNEL_ID' with actual channel ID
        await bot.copy_message(chat_id=message.chat.id, from_chat_id=CHANNEL_ID, message_id=msg_id)
                # Store user information in bot_users table
        user_data_query = f"INSERT INTO bot_users (user_id, username, name, phone_number, created_at) VALUES ($1, $2, $3, $4, NOW()) ON CONFLICT (user_id) DO NOTHING;"
        await execute_query(user_data_query,(str(message.from_user.id), message.from_user.username, message.from_user.first_name, phone_number))

    else:
        await message.reply(f"Assalomu alekum, {message.from_user.first_name}. \nXush kelibsiz!\n\nSizni qiziqtirayotgan kitobchani olish uchun, iltimos biz sms orqali yuborgan maxsus link orqali botga tashrif buyuring😊\nShunda men siz hohlagan kitobchani yuboraman.\n\nHurmat bilan The Wolf jamoasi!", reply_markup=kb.contact_with_admin)

        user_data_query = f"INSERT INTO bot_users (user_id, username, name, phone_number, created_at) VALUES ($1, $2, $3, $4, NOW()) ON CONFLICT (user_id) DO NOTHING;"
        await execute_query(user_data_query,(str(message.from_user.id), message.from_user.username, message.from_user.first_name, None))


@dp.message(UserState.message_text_id)
async def take_id(message: Message, state: FSMContext) -> None:
    stop_msg_text = str(message.text)
    if stop_msg_text == '!cancel':
        await state.clear()
        await message.reply("Jarayon bekor qilindi!")
        return
    elif not message.text.isdigit():
        await message.reply("Please enter the correct message number.")
        await state.set_state(UserState.message_text_id)
        return
    await state.update_data(message_text_id=message.text)
    with open('extras/messages.json', 'r') as file:
        data = json.load(file)
    
    message_text = data[f"msg{message.text}"]
    await message.reply(f"Current message text: {message_text}\n\nPlease enter the new message text.")
    await state.set_state(UserState.message_text)

@dp.message(UserState.message_text)
async def take_text(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await state.clear()
        await message.reply("Jarayon bekor qilindi!")
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
    if message_text == "!cancel":
        await message.reply("Jarayon bekor qilindi!")
        await state.clear()
        return
    
    users = await fetch_query("SELECT user_id, name FROM bot_users;")
    for user in users:
        try:
            await bot.send_message(chat_id=user['user_id'], text=message_text.replace("$name",user['name']), disable_web_page_preview=True)
        except Exception as e:
            if 'Forbidden' in str(e):
                await execute_query(f"DELETE FROM bot_users WHERE bot_users.user_id = '{user['user_id']}';")
            print(e)
            continue
        print(f"Message sent to {user['name']} ({user['user_id']})")
        await asyncio.sleep(1)
    await state.clear()

@dp.message(AdminStateOne.userOneId)
async def take_message_one(message: Message, state: FSMContext) -> None:
    msg_text = str(message.text)
    print(msg_text)
    if msg_text == '!cancel':
        await message.reply("Jarayon bekor qilindi!")
        await state.clear()
        return
    else:
        wait_message = await message.answer("Foydalanuvchi qidirilmoqda...")
        check = await fetch_query("SELECT * FROM bot_users WHERE user_id = $1;", (msg_text,))

    if not check:
        await wait_message.edit_text("Foydalanuvchi topilmadi😕")
        await state.clear()
        return
    else:
        await state.update_data(user_id=message.text)
        found_msg_text = f"Foydalanuvchi topildi.\nUser ID: {check[0]['user_id']}\nName: {check[0]['name']}\nUsername: {check[0]['username']}\nPhone number: {check[0]['phone_number']}\n\nFoydalanuvchiga yuborishni xoxlagan xabarni kiriting."
        await wait_message.edit_text(found_msg_text)
        await state.set_state(AdminStateOne.message_text)

@dp.message(AdminStateOne.message_text)
async def send_to_one(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await message.reply("Jarayon bekor qilindi!")
        await state.clear()
        return
    await state.update_data(message_text=message.text)
    new_data = await state.get_data()
    user_id = new_data.get('user_id')
    message_text = new_data.get('message_text')
    user = await fetch_query(f"SELECT name FROM bot_users WHERE user_id = '{user_id}';")
    try:
        await bot.send_message(chat_id=user_id, text=message_text.replace("$name", user[0]['name']), disable_web_page_preview=True)
    except Exception as e:
        if 'Forbidden' in str(e):
            await execute_query(f"DELETE FROM bot_users WHERE bot_users.user_id = '{user_id}';")
        print(e)
    await state.clear()

@dp.message(UserMessagesToAdmin.message_text)
async def take_message(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await message.reply("Jarayon bekor qilindi")
        await state.clear()
        return
    
    if message.text == 'Murojaat':
        await message.reply("Iltimos, murojaat xabarini yuboring.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(UserMessagesToAdmin.message_text)
        return
    
    await state.update_data(message_text=message.text)
    await message.answer("Murojaatingizni tasdiqlaysizmi?", reply_markup=kb.proove_message)
    await state.set_state(UserMessagesToAdmin.message_proove)

@dp.callback_query(UserMessagesToAdmin.message_proove)
async def send_appeal(callback_data: CallbackQuery, state: FSMContext) -> None:
    if callback_data.data == "proove":
        data = await state.get_data()
        text = data.get('message_text')
        appeal = f"🔔🔔 Yangi Murojaat 🔔🔔\n\nFoydalanuvchi ID: {callback_data.from_user.id}\nFoydalanuvchi ismi: {callback_data.from_user.first_name}\nFoydalanuvchi username: @{callback_data.from_user.username}\n\nMurojaat xabari: {text}"


        try:
            await bot.send_message(chat_id=APPEAL_CHANNEL_ID,text=appeal, parse_mode=ParseMode.HTML)
            await callback_data.message.answer("Murojaatingiz qabul qilindi!",show_alert=True, reply_markup=kb.contact_with_admin)
            await callback_data.message.delete()
        except Exception as e:
            print(e)
    elif callback_data.data == "cancel":
        await callback_data.message.answer("Murojaatingiz bekor qilindi!", reply_markup=kb.contact_with_admin)
        await callback_data.message.delete()
    await state.clear()




@dp.message()
async def take_input(message: Message, state: FSMContext):
    if message.text == '/change_message':
        if message.from_user.id not in admins:
            await message.answer("Siz admin emassiz!")
            return
        await message.answer("Please enter the message number you want to change.")
        await state.set_state(UserState.message_text_id)
        return
    elif message.text == '/send':
        if message.from_user.id not in admins:
            await message.answer("Siz admin emassiz!")
            return
        await message.answer("Foydalanuvchilarga yuborishni xoxlagan xabarni kiriting.")
        await state.set_state(AdminState.message_text)
        return
    elif message.text == '/sendOne':
        if message.from_user.id not in admins:
            await message.answer("Siz admin emassiz!")
            return
        await message.answer("Foydalanuvchini ID raqamini kiriting.")
        await state.set_state(AdminStateOne.userOneId)
        return
    elif message.text == 'Murojaat':
        await message.reply("Iltimos, murojaat xabarini yuboring.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(UserMessagesToAdmin.message_text)
        return
    elif message.text == '/stat':
        if message.from_user.id not in admins:
            await message.answer("Siz admin emassiz!")
            return
        users = await fetch_query("SELECT COUNT(*) FROM bot_users;")
        await message.answer(f"Botda {users[0]['count']} ta foydalanuvchi mavjud.")
        return
    elif message.text == '/users':
        if message.from_user.id not in admins:
            await message.answer("Siz admin emassiz!")
            return
        path = await fns.get_users_data_as_excel()
        if path:
            file = FSInputFile(path,filename=path[7:])
            await bot.send_document(chat_id=message.chat.id, document=file,caption="Foydalanuvchilar ro'yxati")
    elif message.text == '/test':
        await bot.send_message(chat_id=REPORT_ID, text="Test xabar")



async def main() -> None:
    await init_db()
    # await initialize_clients()
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(assign_task_to_operator, 'interval',hours=1)
    # scheduler.add_job(fns.send_message_to_users, 'interval', hours=2)
    # scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())