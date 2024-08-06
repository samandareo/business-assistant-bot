import asyncio
import json

from credentials import BOT_TOKEN
from database import execute_query, fetch_query
from datetime import datetime, timedelta
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from State.userState import UserState, AdminState, AdminStateOne, UserMessagesToAdmin
from bot import dp, bot


async def get_users(time, msg_id):
    try:
        if not isinstance(msg_id, tuple):
            msg_id = tuple(msg_id)
        query = """
        SELECT bu.user_id, bu.name, bu.cur_msg_id 
        FROM bot_users as bu 
        LEFT JOIN end_users as eu ON bu.phone_number = eu.phone_number 
        WHERE eu.phone_number IS NULL 
            AND bu.updated_at <= '$1' 
            AND bu.cur_msg_id = ANY($2::int[]) 
            AND bu.is_check = true;
        """
        params = [time, list(msg_id)]
        return await fetch_query(query=query,params=params)
    except Exception as e:
        print(e)
        return None

async def get_users_for_first(time):
    try:
        query = """
        SELECT bu.user_id, bu.name, bu.cur_msg_id 
        FROM bot_users as bu 
        LEFT JOIN end_users as eu ON bu.phone_number = eu.phone_number
        WHERE eu.phone_number IS NULL 
          AND bu.created_at <= $1 
          AND bu.cur_msg_id = 1 
          AND bu.is_check = true;
        """
        params = [time]
        return await fetch_query(query=query,params=params)
    except Exception as e:
        print(e)
        return None

async def send_first_message():
    with open('extras/messages.json', 'r') as file:
        data = json.load(file)['msg1']

    time = datetime.now() - timedelta(hours=24)
    users = await get_users_for_first(time)
    if not users:
        return
    

    for user in users:
        msg_id = user['cur_msg_id'] + 1
        try:
            await bot.send_message(chat_id=user['user_id'], text=data.replace('$name', user['name']), disable_web_page_preview=True)
            await execute_query(f"UPDATE bot_users SET updated_at = '$1',cur_msg_id = $2 WHERE user_id = '$3';", (datetime.now(), msg_id, user['user_id']))
        except Exception as e:
            if 'Forbidden' in str(e):
                await execute_query(f"DELETE FROM bot_users WHERE bot_users.user_id = '$1';", (user['user_id'],))
            print(e)
            continue
        print(f"Message sent to {user['name']} ({user['user_id']})")
        await asyncio.sleep(0.7)



async def send_24_messages():
    with open('extras/messages.json', 'r') as file:
        data = json.load(file)

    time = datetime.now() - timedelta(hours=24)
    users = await get_users(time, [2,4,5,6,8])

    if not users:
        return


    for user in users:
        msg_id = user['cur_msg_id'] + 1
        if user['cur_msg_id'] != 4:
            try:
                await bot.send_message(chat_id=user['user_id'], text=data[f"msg{user['cur_msg_id']}"].replace('$name', user['name']), disable_web_page_preview=True)
                await execute_query(f"UPDATE bot_users SET updated_at = '$1',cur_msg_id = $2 WHERE user_id = '$3';", (datetime.now(), msg_id, user['user_id']))
            except Exception as e:
                if 'Forbidden' in str(e):
                    await execute_query(f"DELETE FROM bot_users WHERE bot_users.user_id = '$1';", (user['user_id'],))
                print(e)
                continue
            print(f"Message sent to {user['name']} ({user['user_id']})")
        elif user['cur_msg_id'] == 4:
            try:
                await bot.send_message(chat_id=user['user_id'], text=data[f"msg{user['cur_msg_id']}1"].replace('$name', user['name']), disable_web_page_preview=True)
                await bot.copy_message(chat_id=user['user_id'], from_chat_id=-1002151076535, message_id=18)
                await bot.send_message(chat_id=user['user_id'], text=data[f"msg{user['cur_msg_id']}2"].replace('$name', user['name']), disable_web_page_preview=True)
                await execute_query(f"UPDATE bot_users SET updated_at = '$1',cur_msg_id = $2 WHERE user_id = '$3';", (datetime.now(), msg_id, user['user_id']))
            except Exception as e:
                if 'Forbidden' in str(e):
                    await execute_query(f"DELETE FROM bot_users WHERE bot_users.user_id = '$1';", (user['user_id'],))
                print(e)
                continue
            print(f"Message sent to {user['name']} ({user['user_id']})")
        await asyncio.sleep(0.7)


async def send_48_messages():
    with open('extras/messages.json', 'r') as file:
        data = json.load(file)

    time = datetime.now() - timedelta(hours=48)
    users = await get_users(time, [3,7])

    if not users:
        return


    for user in users:
        msg_id = user['cur_msg_id'] + 1
        try:
            await bot.send_message(chat_id=user['user_id'], text=data[f"msg{user['cur_msg_id']}"].replace('$name', user['name']), disable_web_page_preview=True)
            await execute_query(f"UPDATE bot_users SET updated_at = '$1',cur_msg_id = $2 WHERE user_id = '$3';", (datetime.now(), msg_id, user['user_id']))
        except Exception as e:
            if 'Forbidden' in str(e):
                await execute_query(f"DELETE FROM bot_users WHERE bot_users.user_id = '$1';", (user['user_id'],))
            print(e)
            continue
        await asyncio.sleep(0.7)


async def send_message_to_users():
    try:
        await send_first_message()
        await send_24_messages()
        await send_48_messages()
    except Exception as e:
        print(e)


    


