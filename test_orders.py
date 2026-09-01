import sys, asyncio
sys.path.append('backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')
from routes.merchant_routes import get_all_orders
from config.database import db_connection

async def test():
    await db_connection.init_db()
    try:
        res = await get_all_orders(current_user={'user_id': 1, 'role': 'merchant'})
        print("SUCCESS")
    except Exception as e:
        import traceback
        traceback.print_exc()

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(test())
