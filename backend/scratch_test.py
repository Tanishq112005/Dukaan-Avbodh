import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from config.database import db_connection
from repositories.product_repository import ProductRepository

async def main():
    p_repo = ProductRepository()
    t0 = time.time()
    await p_repo.get_by_ids([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
    print('Time taken for get_by_ids:', time.time() - t0)

if __name__ == "__main__":
    asyncio.run(main())
