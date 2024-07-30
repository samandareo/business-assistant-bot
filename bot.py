from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.loggers import LoggingMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.filters.command import CommandStart



# Replace with your bot token and channel ID
BOT_TOKEN = '7341078660:AAHtF2WA3Cyyafu0EDv6lF1BUapMvGVdM0o'
CHANNEL_ID = '-1002151076535'

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, )
dp = Dispatcher()

# States for handling token verification and book sending
class BookSending(StatesGroup):
    waiting_for_token = State()

# Function to check token validity (replace with your logic)
async def check_token(token):
    # Your token verification logic here
    return True  # Replace with actual token validation

# Function to get book based on token (replace with your logic)
async def get_book(token):
    # Your book retrieval logic here
    if token == 7:
        return "https://t.me/c/2151076535/31"


# Handler for start command with token in URL
@dp.message(lambda message: message.text.startswith('https://t.me/'))
async def start_with_token(message: types.Message):
    # Extract token from URL
    url = message.text
    try:
        token = url.split('start=')[1]
        if await check_token(token):
            book = await get_book(token)
            await bot.forward_message(CHANNEL_ID, message.chat.id, book)
        else:
            await message.reply("Invalid token")
    except IndexError:
        await message.reply("Invalid URL format")

# Handler for start command without token
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.reply("Send your token to start")
    await BookSending.waiting_for_token.set()

# Handler for token input
@dp.message(state=BookSending.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    token = message.text
    if await check_token(token):
        book = await get_book(token)
        await message.reply(book)
        await state.finish()
    else:
        await message.reply("Invalid token")
        await state.finish()

# Handler for channel message forwarding (replace with your logic)
@dp.message()
async def forward_message(message: types.Message):
    # Logic to forward message to specific chats based on tokens
    # ...
    pass

if __name__ == '__main__':
    dp.start_polling(dp, skip_updates=True)
