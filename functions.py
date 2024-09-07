import asyncio
import json
from datetime import datetime, timedelta


from database import execute_query, fetch_query, init_db
from bot import bot

from Userbot.userbot import initialize_clients, send_to_users, copy_to_users
from credentials import REPORT_ID

import pandas as pd


async def get_users(time, msg_id):
    try:
        if not isinstance(msg_id, tuple):
            msg_id = tuple(msg_id)
        query = """
        SELECT bu.user_id, bu.username, bu.name, bu.cur_msg_id, bu.res_id 
        FROM bot_users as bu 
        LEFT JOIN end_users as eu ON bu.phone_number = eu.phone_number 
        WHERE eu.phone_number IS NULL 
            AND bu.updated_at <= $1 
            AND bu.cur_msg_id = ANY($2::int[]) 
            AND bu.is_check = true;
        """
        params = (time, list(msg_id))
        return await fetch_query(query=query, params=params)
    except Exception as e:
        print(e)
        return None

async def get_users_for_first(time):
    await init_db()
    try:
        query = """
        SELECT bu.user_id,bu.username, bu.name, bu.cur_msg_id, bu.res_id 
        FROM bot_users as bu 
        LEFT JOIN end_users as eu ON bu.phone_number = eu.phone_number
        WHERE eu.phone_number IS NULL 
          AND bu.created_at <= $1
          AND bu.cur_msg_id = 1 
          AND bu.is_check = true;
        """
        params = (time,)
        return await fetch_query(query=query, params=params)
    except Exception as e:
        print(e)
        return None

async def send_first_message():
    with open('extras/messages.json', 'r') as file:
        data = json.load(file)['msg1']

    time = datetime.now() - timedelta(hours=24)
    users = await get_users_for_first(time=time)
    print(users)
    if not users:
        print('No users')
        return

    await bot.send_message(chat_id=REPORT_ID,text=f"Birinchi xabar yuborilishi boshlandi!")
    cnt = 0
    for user in users:
        msg_id = user['cur_msg_id'] + 1
        txt = str(data)
        txt = txt.replace('$name', user['name'])
        try:

            # # This userbot ------ #
            # if user['username']:
            #     try:
            #         await send_to_users(username=user['username'], message_text=txt, respon_id=user['res_id'])
            #     except Exception as e:
            #         print(e)
            # # ------------------- #

            await bot.send_message(chat_id=user['user_id'], text=data.replace('$name', user['name']), disable_web_page_preview=True)
            await asyncio.sleep(1)
            await execute_query("UPDATE bot_users SET updated_at = $1, cur_msg_id = $2 WHERE user_id = $3;", (datetime.now(), msg_id, user['user_id']))
        except Exception as e:
            if 'Forbidden' in str(e):
                await execute_query("DELETE FROM bot_users WHERE user_id = $1;", (user['user_id'],))
            print(e)
            continue
        print(f"Message sent to {user['name']} ({user['user_id']})")
        await asyncio.sleep(0.7)
        cnt += 1
    await bot.send_message(chat_id=REPORT_ID,text=f"Birinchi xabar {cnt} ta foydalanuvchiga xabar yuborildi✅")

async def send_24_messages():
    with open('extras/messages.json', 'r') as file:
        data = json.load(file)

    time = datetime.now() - timedelta(hours=24)
    users = await get_users(time, [2, 4, 5, 6, 8])

    if not users:
        print('No users')
        return
    await bot.send_message(chat_id=REPORT_ID,text=f"24 soatlik xabarlar yuborilishi boshlandi!")

    cnt = {
        2: 0,
        4: 0,
        5: 0,
        6: 0,
        8: 0
    }

    for user in users:
        msg_id = user['cur_msg_id'] + 1
        if user['cur_msg_id'] != 4:
            try:
                # # This userbot ------ #
                # if user['username']:
                #     txt = str(data[f"msg{user['cur_msg_id']}"])
                #     try:
                #         await send_to_users(username=user['username'], message_text=txt.replace('$name', user['name']), respon_id=user['res_id'])
                #     except Exception as e:
                #         print(e)
                # # ------------------- #

                await bot.send_message(chat_id=user['user_id'], text=data[f"msg{user['cur_msg_id']}"].replace('$name', user['name']), disable_web_page_preview=True)
                # await execute_query("UPDATE bot_users SET updated_at = $1, cur_msg_id = $2 WHERE user_id = $3;", (datetime.now(), msg_id, user['user_id']))
                await asyncio.sleep(1)
                await execute_query("UPDATE bot_users SET updated_at = $1, cur_msg_id = $2 WHERE user_id = $3;", (datetime.now(), msg_id, user['user_id']))
            except Exception as e:
                if 'Forbidden' in str(e):
                    await execute_query("DELETE FROM bot_users WHERE user_id = $1;", (user['user_id'],))
                print(e)
                continue
            print(f"Message sent to {user['name']} ({user['user_id']})")

        elif user['cur_msg_id'] == 4:
            txt1 = str(data[f"msg{user['cur_msg_id']}1"])
            txt2 = str(data[f"msg{user['cur_msg_id']}2"])
            try:

                # # This userbot ------ #
                # if user['username']:
                #     try:
                #         await send_to_users(username=user['username'], message_text=txt1.replace('$name', user['name']), respon_id=user['res_id'])
                #         await copy_to_users(username=user['username'], channel_id=-1002151076535, respon_id=user['res_id'], message_id=18)
                #         await send_to_users(username=user['username'], message_text=txt2.replace('$name', user['name']), respon_id=user['res_id'])
                #     except Exception as e:
                #         print(e)
                # # ------------------- #

                await bot.send_message(chat_id=user['user_id'], text=data[f"msg{user['cur_msg_id']}1"].replace('$name', user['name']), disable_web_page_preview=True)
                await asyncio.sleep(0.1)
                await bot.copy_message(chat_id=user['user_id'], from_chat_id=-1002151076535, message_id=18)
                await asyncio.sleep(0.1)
                await bot.send_message(chat_id=user['user_id'], text=data[f"msg{user['cur_msg_id']}2"].replace('$name', user['name']), disable_web_page_preview=True)
                await asyncio.sleep(0.1)
                await execute_query("UPDATE bot_users SET updated_at = $1, cur_msg_id = $2 WHERE user_id = $3;", (datetime.now(), msg_id, user['user_id']))

            except Exception as e:
                if 'Forbidden' in str(e):
                    await execute_query("DELETE FROM bot_users WHERE user_id = $1;", (user['user_id'],))
                print(e)
                continue
            print(f"Message sent to {user['name']} ({user['user_id']})")
        await asyncio.sleep(0.7)
        cnt[user['cur_msg_id']] += 1

    done_msg = f"Foydalanuvchilarga yuborilgan xabarlar soni:\nIkkinchi xabar soni: {cnt.get(2)}\nTo'rtinchi xabar soni: {cnt.get(4)}\nBeshinchi xabar soni: {cnt.get(5)}\nOltinchi xabar soni: {cnt.get(6)}\nSakkizinchi xabar soni: {cnt.get(8)}"
    await bot.send_message(chat_id=REPORT_ID,text=done_msg)
    cnt = {
        2: 0,
        4: 0,
        5: 0,
        6: 0,
        8: 0
    }

async def send_48_messages():
    with open('extras/messages.json', 'r') as file:
        data = json.load(file)

    time = datetime.now() - timedelta(hours=48)
    users = await get_users(time, [3, 7])

    if not users:
        print('No users')
        return
    
    cnt = {
        3: 0,
        7: 0
    }
    for user in users:
        msg_id = user['cur_msg_id'] + 1
        try:

            # # This userbot ------ #
            # if user['username']:
            #     txt = str(data[f"msg{user['cur_msg_id']}"])
            #     try:
            #         await send_to_users(username=user['username'], message_text=txt.replace('$name', user['name']), respon_id=user['res_id'])
            #     except Exception as e:
            #         print(e)
            # # ------------------- #

            await bot.send_message(chat_id=user['user_id'], text=data[f"msg{user['cur_msg_id']}"].replace('$name', user['name']), disable_web_page_preview=True)
            await asyncio.sleep(0.1)
            await execute_query("UPDATE bot_users SET updated_at = $1, cur_msg_id = $2 WHERE user_id = $3;", (datetime.now(), msg_id, user['user_id']))
        except Exception as e:
            if 'Forbidden' in str(e):
                await execute_query("DELETE FROM bot_users WHERE user_id = $1;", (user['user_id'],))
            print(e)
            continue
        await asyncio.sleep(0.7)
        cnt[user['cur_msg_id']] += 1

    done_msg = f"Foydalanuvchilarga yuborilgan xabarlar soni:\nUchinchi xabar soni: {cnt.get(3)}\nYettinchi xabar soni: {cnt.get(7)}"
    await bot.send_message(chat_id=REPORT_ID,text=done_msg)
    cnt = {
        3: 0,
        7: 0
    }




async def send_message_to_users():
    try:
        await send_first_message()
        await asyncio.sleep(1)
        await send_24_messages()
        await asyncio.sleep(1)
        await send_48_messages()
    except Exception as e:
        print(e)

# To run the functions
# asyncio.run(send_message_to_users())

async def get_users_data_as_excel():
    try:
        query = """
        SELECT user_id, username, name, phone_number, DATE(created_at) 
        FROM bot_users
        """
        data = await fetch_query(query=query)
        if not data:
            return None
        df = pd.DataFrame(data)

        df.columns = ['user_id', 'username', 'name', 'phone_number', 'created_at']
        print(df)
        new_data = {
            'user_id': [],
            'username': [],
            'name': [],
            'phone_number': [],
            'created_at': []
        }

        for i in range(len(df)):
            new_data['user_id'].append(df['user_id'][i])
            new_data['username'].append(df['username'][i])
            new_data['name'].append(df['name'][i])
            if str(df['phone_number'][i]) == 'None':
                new_data['phone_number'].append("Phone number is not valid")
            else:
                new_data['phone_number'].append(f"+{str(df['phone_number'][i])[:12]}")
            new_data['created_at'].append(str(df['created_at'][i]))
        
        new_data = pd.DataFrame(new_data)
        now = datetime.now().strftime("%Y_%m_%d")
        new_data.to_excel(f'extras/bot_users_data_{now}.xlsx', index=False)
        return f"extras/bot_users_data_{now}.xlsx"

    except Exception as e:
        print(e)
        return None