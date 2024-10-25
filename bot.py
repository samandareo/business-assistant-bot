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
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile, Poll
from aiogram.exceptions import TelegramRetryAfter

from database import execute_query, fetch_query, init_db
import functions as fns
from State.userState import UserState, AdminState, AdminStateOne, UserMessagesToAdmin, CreatePoll, PollResults
import Keyboards.keyboards as kb

from credentials import admins
from Userbot.userbot import initialize_clients
from Userbot.assign import assign_task_to_operator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



from credentials import BOT_TOKEN, CHANNEL_ID, APPEAL_CHANNEL_ID, TEST_BOT_TOKEN, REPORT_ID
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

@dp.poll()
async def handler_poll(poll: Poll):
    poll_id = poll.id
    question = poll.question
    options = poll.options

    data = {
        'question' : question
    }
    print(f"Poll ID: {poll_id}, Question: {question}")
    for option in options:
        data[option.text] = option.voter_count
        print(f"Option: {option.text}, Voter Count: {option.voter_count}")
    
    await fns.change_data(poll_id,data)

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
        await execute_query(user_data_query,(str(message.from_user.id), message.from_user.username, message.from_user.first_name, None))

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

broadcast_task = None

async def rasilka(users, message):
    global broadcast_task
    cnt = 0
    for user in users:
        if broadcast_task is not None and broadcast_task.cancelled():
            print("Broadcast task was cancelled.")
            await message.reply(f"Xabar {cnt} ta foydalanuvchiga jo'natildi!")
            break
        try:
            if message.text:
                await bot.send_message(user['user_id'],message.text.replace("$name", user['name']), disable_web_page_preview=True)
            elif message.caption:
                await bot.copy_message(user['user_id'],message.chat.id,message.message_id, caption=message.caption.replace("$name", user['name']))
            elif not message.text and not message.caption:
                await bot.copy_message(user['user_id'],message.chat.id,message.message_id)
            print(f"Message sent to {user['name']} ({user['user_id']})")
            cnt += 1
        except TelegramRetryAfter as e:
            print(f'Rate limit exceeded. Sleeping for {e.timeout} seconds.')
            await asyncio.sleep(e.timeout)
            if message.text:
                await bot.send_message(user['user_id'],message.text.replace("$name", user['name']), disable_web_page_preview=True)
            elif message.caption:
                await bot.copy_message(user['user_id'],message.chat.id,message.message_id, caption=message.caption.replace("$name", user['name']))
            elif not message.text and not message.caption:
                await bot.copy_message(user['user_id'],message.chat.id,message.message_id)
            print(f"Message sent to {user['name']} ({user['user_id']})")
            cnt += 1

        except Exception as e:
            if 'Forbidden' in str(e):
                await execute_query(f"DELETE FROM bot_users WHERE bot_users.user_id = '{user['user_id']}';")
            print(e)
            continue
        print(f"Message sent to {user['name']} ({user['user_id']})")
        await asyncio.sleep(0.05)
    await message.answer(f"Xabar {cnt} ta foydalanuvchiga jo'natildi!")

@dp.message(AdminState.message_text)
async def send_to_all(message: Message, state: FSMContext) -> None:
    global brodcast_task
    message_text = message.text
    if message_text == "!cancel":
        await message.reply("Jarayon bekor qilindi!")
        await state.clear()
        return
    
    users = await fetch_query("SELECT user_id, name FROM bot_users;")
    # We need to run the function in a separate task to avoid blocking the event loop
    try:
        brodcast_task = asyncio.create_task(rasilka(users, message))
        await message.answer("Rasilka boshlandi!")
    except Exception as e:
        logger.info(f"Error sending message to users: {e}")

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
        if message.text:
            await bot.send_message(chat_id=user_id,text=message_text.replace("$name", user[0]['name']), disable_web_page_preview=True)
        elif message.caption:
            await bot.copy_message(user_id,message.chat.id,message.message_id, caption=message.caption.replace("$name", user[0]['name']))
        elif not message.text and not message.caption:
            await bot.copy_message(user_id,message.chat.id,message.message_id)
        await message.answer("Xabar jo'natildi!")
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

@dp.message(CreatePoll.question)
async def take_question(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await message.reply("Jarayon bekor qilindi")
        await state.clear()
        return
    
    await state.update_data(question=message.text)
    await message.reply("Qabul qilindi! So'rovnomada nechta javob/variant bo'lishi kerak?")
    await state.set_state(CreatePoll.count)

@dp.message(CreatePoll.count)
async def take_count(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await message.reply("Jarayon bekor qilindi")
        await state.clear()
        return
    
    await state.update_data(count=int(message.text), options=[])
    await message.reply("Axa! Iltimos, 1 - variantni kiriting:")
    await state.set_state(CreatePoll.option)


@dp.message(CreatePoll.option)
async def take_options(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await message.reply("Jarayon bekor qilindi")
        await state.clear()
        return
    
    user_data = await state.get_data()
    options = user_data.get('options', [])
    count = user_data.get('count')

    options.append(message.text)
    await state.update_data(options=options)

    if len(options) < count:
        await message.reply(f"Qabul qilindi! {len(options)+1}-variantni kiriting:")
        await state.set_state(CreatePoll.option)
        return
    else:
        question = user_data.get('question')
        options = user_data.get('options')
        text = ''
        for option in options:
            text += f"{option}\n"

        await message.reply(f"Savol : {question}\nVariantlar:\n{text}\n---------------------\nSo'rovnomani tasdiqlaysizmi?", reply_markup=kb.proove_poll)
        await state.set_state(CreatePoll.proove)

@dp.callback_query(CreatePoll.proove)
async def send_appeal(callback_data: CallbackQuery, state: FSMContext) -> None:
    if callback_data.data == 'proove':
        msg = await callback_data.message.answer("So'rovnoma yaratildi va yuborilmoqda...",show_alert=True, reply_markup=kb.contact_with_admin)
        await callback_data.message.delete()
        try:
            await bot.copy_message(chat_id=msg.chat.id, from_chat_id=-1002465539645, message_id=3, reply_to_message_id=msg.message_id)
        except Exception as e:
            print(e)
        data = await state.get_data()
        question = data.get('question')
        options = data.get('options')
        await fns.create_poll(question, options)
        await state.clear()
        print("Poll created")
        return
    
    elif callback_data.data == 'cancel':
        msg = await callback_data.message.reply("So'rovnoma bekor qilindi")
        await callback_data.message.delete()
        try:
            await bot.copy_message(chat_id=callback_data.message.chat.id, from_chat_id=-1002465539645, message_id=5, reply_to_message_id=msg.message_id)
        except Exception as e:
            print(e)
        await state.clear()
        print("Poll canceled")
        return

@dp.message(PollResults.poll_name)
async def take_poll_name(message: Message, state: FSMContext) -> None:
    if message.text == '!cancel':
        await message.reply("Jarayon bekor qilindi")
        await state.clear()
        return
    
    with open('polls/poll_ids.json', 'r') as file:
        data = json.load(file)
    
    polls = []

    for item in data:
        polls.append(item)
    
    poll_name = polls[int(message.text)-1]

    res = await fns.get_result(poll_name)
    text = f"Question: {res['question']}\n"
    for key, value in res.items():
        if key == 'question':
            continue
        text += f"{key}: {value}\n"
    
    await message.answer(text=text)
    await state.clear()
    return


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
    elif message.text == '/polls':
        if message.text == '!cancel':
            await message.reply("Jarayon bekor qilindi")
            await state.clear()
            return
        names = []
        text = ''

        with open('polls/poll_ids.json', 'r') as file:
            data = json.load(file)
            
        count = 1   
        for item in data:
            names.append(item)
            text += f"{count}. {item}\n"
            count += 1

        req = "Tanlagan so'rovnomangizni raqamini kriting:"
        full_text = f"{text}\n{req}"
        await message.answer(text=full_text)
        await state.set_state(PollResults.poll_name)
        return
    elif message.text == '/create_poll':
        await message.reply("So'rovnoma savolini kiriting!")
        await state.set_state(CreatePoll.question)
        return
    elif message.text == '/stop_rasilka':
        global brodcast_task
        if brodcast_task is not None and not brodcast_task.cancelled():
            brodcast_task.cancel()
            await message.answer("Rasilkani to'xtatish uchun buyruq qabul qilindi.")
        else:
            await message.answer("Rasilkani to'xtatish uchun hech qanday buyruq qabul qilinmadi.")
        return
    



async def main() -> None:
    await init_db()
    # await initialize_clients()
    scheduler = AsyncIOScheduler()
    # scheduler.add_job(assign_task_to_operator, 'interval',hours=1)
    scheduler.add_job(fns.send_message_to_users, 'interval', hours=2)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
