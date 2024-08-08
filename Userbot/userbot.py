import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

import asyncpg
from credentials import accounts
import asyncio

from telethon import TelegramClient

clients = {}
async def initialize_clients():
    for account in accounts:
        client = TelegramClient(f'sessions/dil_{account["responsible_id"]}', account['api_id'], account['api_hash'])
        await client.start(account['phone_number'])

        clients[account['responsible_id']] = client

async def send_to_users(username, message_text, respon_id,cur_msg_id,name):

    client = clients.get(respon_id)

    await client.send_message(username, message_text, link_preview=False)
    await client.send_message(-1004218215589, f"{name} ga {respon_id}-xabar yuborildi✅ ")

async def copy_to_users(username,channel_id, respon_id, message_id):
    client = clients.get(respon_id)
    await client.forward_messages(username,channel_id, message_id, drop_author=True)