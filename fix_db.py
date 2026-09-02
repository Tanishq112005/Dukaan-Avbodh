import sys, asyncio
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')
from config.database import db_connection
from sqlalchemy import text

async def alter():
    async with db_connection.engine.begin() as conn:
        try:
            await conn.execute(text('ALTER TABLE "order" ADD COLUMN razorpay_order_id VARCHAR'))
            print('Added razorpay_order_id')
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(text('ALTER TABLE "order" ADD COLUMN razorpay_payment_id VARCHAR'))
            print('Added razorpay_payment_id')
        except Exception as e:
            print(e)
            
        try:
            await conn.execute(text('ALTER TABLE "product" ADD COLUMN importance_score INTEGER DEFAULT 0'))
            print('Added importance_score to product')
        except Exception as e:
            print(e)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(alter())
