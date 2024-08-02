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
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from State.userState import UserState

import json

from credentials import BOT_TOKEN, CHANNEL_ID
bot = Bot(token="1147881044:AAGr-a4YfBRj5XPDeY4xBVaxKo9JSE7bMp8", default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def handle_start(message: types.Message) -> None:
    await message.answer("Hello! I'm a bot.")


@dp.message(UserState.message_text_id)
async def take_id(message: Message, state: FSMContext) -> None:
    await state.update_data(message_text_id=message.text)
    await message.answer("Please enter the new message text.")
    await state.set_state(UserState.message_text)

@dp.message(UserState.message_text)
async def take_text(message: Message, state: FSMContext) -> None:
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
    


@dp.message()
async def take_input(message: Message, state: FSMContext):
    if message.text == '/change_message':
        await message.answer("Please enter the message number you want to change.")
    elif message.text == '/sendMe':
        with open('extras/messages.json', 'r') as file:
            data = json.load(file)
        name = message.from_user.first_name
        send_message_text = f"{data['msg1'].replace('$name', name)}"
        await message.answer(send_message_text,protect_content=True,disable_web_page_preview=True)
        return
    elif message.text == '/sendMe2':
        with open('extras/messages.json', 'r') as file:
            data = json.load(file)
        name = message.from_user.first_name
        send_message_text = f"{data['msg2'].replace('$name', name)}"
        await message.answer(send_message_text,protect_content=True,disable_web_page_preview=True)
        return
    await state.set_state(UserState.message_text_id)





async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())