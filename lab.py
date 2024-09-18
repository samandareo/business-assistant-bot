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

users = [895775406, 1586676962, 5881965498]
users = [
    {
        "id": 895775406,
        "name": "Samandar"
    },
    {
        "id": 1586676962,
        "name": "Umid"
    },
    {
        "id": 5881965498,
        "name": "Sam"
    }
]

@dp.message()
async def handle_message(message: types.Message) -> None:
    # if message.video:
    #     await message.answer_video(message.video.file_id,caption=message.caption)
    # elif message.photo:
    #     await message.answer_photo(message.photo[-1].file_id,caption=message.caption)
    # elif message.audio:
    #     await message.answer_audio(message.audio.file_id,caption=message.caption)
    # elif message.voice:
    #     await message.answer_voice(message.voice.file_id,caption=message.caption)
    # elif message.document:
    #     await message.answer_document(message.document.file_id,caption=message.caption)
    # elif message.sticker:
    #     await message.answer_sticker(message.sticker.file_id)
    # elif message.animation:
    #     await message.answer_animation(message.animation.file_id,caption=message.caption)
    # elif message.video_note:
    #     await message.answer_video_note(message.video_note.file_id)
    # elif message.location:
    #     await message.answer_location(message.location.latitude,message.location.longitude)
    # elif message.text:
    #     await message.answer(message.text)
    for user in users:
        try:
            if message.text:
                await bot.send_message(user['id'],message.text.replace("$name", user['name']), disable_web_page_preview=True)
            elif message.caption:
                await bot.copy_message(user['id'],message.chat.id,message.message_id, caption=message.caption.replace("$name", user['name']))
            elif not message.text and not message.caption:
                await bot.copy_message(user['id'],message.chat.id,message.message_id)
        except Exception as e:
            print(e)
            continue


# @dp.message(UserState.message_text_id)
# async def take_id(message: Message, state: FSMContext) -> None:
#     await state.update_data(message_text_id=message.text)
#     await message.answer("Please enter the new message text.")
#     await state.set_state(UserState.message_text)

# @dp.message(UserState.message_text)
# async def take_text(message: Message, state: FSMContext) -> None:
#     new_data = await state.get_data()
#     message_text_id = new_data.get('message_text_id')
#     message_text = message.text

#     with open('extras/messages.json', 'r') as file:
#         data = json.load(file)
    
#     data[f"msg{message_text_id}"] = message_text

#     with open('extras/messages.json', 'w') as file:
#         json.dump(data, file, indent=4)

#     await message.answer(f"Message number {message_text_id} has been changed.")
#     await state.clear()
    


# @dp.message()
# async def take_input(message: Message, state: FSMContext):
#     if message.text == '/change_message':
#         await message.answer("Please enter the message number you want to change.")
#     elif message.text == '/sendMe':
#         with open('extras/messages.json', 'r') as file:
#             data = json.load(file)
#         name = message.from_user.first_name
#         send_message_text = f"{data['msg1'].replace('$name', name)}"
#         await message.answer(send_message_text,protect_content=True,disable_web_page_preview=True)
#         return
#     elif message.text == '/sendMe2':
#         with open('extras/messages.json', 'r') as file:
#             data = json.load(file)
#         name = message.from_user.first_name
#         send_message_text = f"{data['msg2'].replace('$name', name)}"
#         await message.answer(send_message_text,protect_content=True,disable_web_page_preview=True)
#         return
#     await state.set_state(UserState.message_text_id)





async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())