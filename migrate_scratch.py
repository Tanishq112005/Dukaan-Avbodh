import sys, asyncio
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')
from config.database import db_connection
from sqlalchemy import text

async def alter():
    async with db_connection.engine.begin() as conn:
        try:
            await conn.execute(text('ALTER TABLE "product" ADD COLUMN IF NOT EXISTS importance_score INTEGER DEFAULT 0'))
            print('Added importance_score to product')
        except Exception as e:
            print('Error:', e)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(alter())
