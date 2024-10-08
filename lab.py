import asyncio
import logging
import sys
import re
import json

import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters.command import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Poll, CallbackQuery
from State.userState import UserState, CreatePoll, PollResults
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import Keyboards.keyboards as kb

import json

from credentials import BOT_TOKEN, CHANNEL_ID
bot = Bot(token="1147881044:AAGr-a4YfBRj5XPDeY4xBVaxKo9JSE7bMp8", default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def handle_start(message: types.Message) -> None:
    await message.answer("Hello! I'm a bot.")

users = [895775406, 1586676962, 5881965498]
users = [
    {
        "id": 895775406,
        "name": "Samandar"
    },
    # {
    #     "id": 7102300410,
    #     "name": "Umidjon"
    # },
    {
        "id": 5881965498,
        "name": "Sam"
    }
]

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
    
    await change_data(poll_id,data)



polls = []


async def insert_data(poll_data, poll_ids, question):
    try:
        with open("polls/poll_data.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError as e:
        print(e)


    try:
        with open("polls/poll_ids.json", "r") as file:
            polls_id = json.load(file)
    except FileNotFoundError as e:
        print(e)
    
    ids = {
        f"{question}" : poll_ids
    }
    
    data.update(poll_data)
    polls_id.update(ids)

    with open('polls/poll_data.json', "w") as file:
        json.dump(data, file, indent=4)
        print("New data added to [poll_data]")
    
    with open('polls/poll_ids.json', "w") as file:
        json.dump(polls_id, file, indent=4)
        print("New data added to [poll_data]")
    
    

async def change_data(id, new_data):
    with open('polls/poll_data.json', 'r') as file:
        data = json.load(file)

    data[id] = new_data

    with open('polls/poll_data.json', 'w') as file:
        json.dump(data, file, indent=4)
        print(f"Data changed to \n{new_data}")

async def get_result(name):
    with open('polls/poll_ids.json', 'r') as file:
        poll_ids = json.load(file)

    with open('polls/poll_data.json', 'r') as file:
        poll_data = json.load(file)
    
    main_question = ''
    result = {}
    for key, value in poll_data.items():
        if key in poll_ids[name]:
            if 'question' not in result:
                main_question = value['question']
                result['question'] = main_question
                for option, count in value.items():
                    if option == 'question':
                        continue
                    result[option] = count
            else:
                for option, count in value.items():
                    if option == 'question':
                        continue
                    if option in result:
                        result[option] += count
                    else:
                        result[option] = count

    return result

async def create_poll(received_question, received_options):
        

    data = {

    }

    poll_ids = []

    for user in users:
        try:
            options = received_options
            question = received_question.replace("$name", user['name'])

            poll_message = await bot.send_poll(chat_id=user['id'],question=question, options=options)

            ##############################
            poll_id = poll_message.poll.id
            poll_ids.append(poll_id)

            data[poll_id] = {}
            data[poll_id]['question'] = question

            for option in options:
                data[poll_id][option] = 0

        except Exception as e:
            print(e)
            continue
    

    await insert_data(data, poll_ids, question)            


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
        await create_poll(question, options)
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

    res = await get_result(poll_name)
    text = f"Question: {res['question']}\n"
    for key, value in res.items():
        if key == 'question':
            continue
        text += f"{key}: {value}\n"
    
    await message.answer(text=text)
    await state.clear()
    return


@dp.message()
async def handle_message(message: types.Message, state: FSMContext) -> None:
    if message.text == '/polls':

        names = []
        text = ''

        with open('polls/poll_ids.json', 'r') as file:
            data = json.load(file)
        
        for item in data:
            count = 1
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

    


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())