import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

import asyncpg
import asyncio


DATABASE_CONFIG = {
    'host': "dpg-cqitjr8gph6c738u4sp0-a.frankfurt-postgres.render.com",
    'database': "tarbotdb",
    'user': "sreo",
    'password': "4INdhZzCVyZ7GagHBnJoPp38sAqg3iOS",
    'port': "5432"
}


async def get_db_connection():
    conn = await asyncpg.connect(
        user=DATABASE_CONFIG['user'],
        password=DATABASE_CONFIG['password'],
        database=DATABASE_CONFIG['database'],
        host=DATABASE_CONFIG['host'],
        port=DATABASE_CONFIG['port']
    )
    return conn


async def fetch_query(query, params=None):
    conn = await get_db_connection()
    result = await conn.fetch(query, *params if params else [])
    await conn.close()
    return result

async def execute_query(query, params=None):
    conn = await get_db_connection()
    await conn.execute(query, *params if params else [])
    await conn.close()


async def get_operators_count():
    operators = await fetch_query('SELECT res_id FROM operators;')
    return operators

async def get_unassigned_users():
    unassigned_users = await fetch_query("SELECT id FROM bot_users WHERE res_id IS NULL;")
    return unassigned_users
    
async def get_operator_user_counts():
    operator_users = await fetch_query("SELECT res_id, COUNT(id) FROM bot_users WHERE res_id IS NULL GROUP BY res_id;")
    count = {}
    for row in operator_users:
        count[row['res_id']] = row['count']
    return count


async def assign_task_to_operator():
    operators = await get_operators_count()
    operator_users_count = await get_operator_user_counts()
    users = await get_unassigned_users()

    for operator in operators:
        if operator['res_id'] not in operator_users_count:
            operator_users_count[operator['res_id']] = 0
    
    operator_count = len(operators)
    index = 0

    for user_id in users:
        min_count = min(operator_users_count.values())
        for operator in operators:
            if operator_users_count[operator['res_id']] == min_count:
                selected_operator = operator
                break
        
        await execute_query("UPDATE bot_users SET res_id = $1 WHERE id = $2;", (selected_operator['res_id'], user_id['id']))
        print(f"User {user_id} assigned to operator {selected_operator['res_id']}")
        operator_users_count[selected_operator['res_id']] += 1
        await asyncio.sleep(0.5)


