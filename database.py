import asyncpg

# ------------------- DATABASE CONFIGURATION ------------------- #
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


# ------------------- DATABASE OPERATIONS ------------------- #
async def fetch_query(query, params=None):
    conn = await get_db_connection()
    result = await conn.fetch(query, *params if params else [])
    await conn.close()
    return result
"""
Return value as below format:
(Record id=1 name='John Doe' age=25)

You can take them with their keys like:
result[0]['id']
result[0]['name']

OR

result[1]['id']
result[1]['name']

result[0] is the first row of the result.
"""

async def execute_query(query, params=None):
    conn = await get_db_connection()
    await conn.execute(query, *params if params else [])
    await conn.close()

