# backfill_embeddings.py
#
# Re-indexes ALL products from Postgres into the Pinecone vector index.
# Run this any time you:
#   - change the embedding model / provider
#   - change the embedding dimension (after deleting + recreating the Pinecone index)
#   - suspect the vector index is out of sync with Postgres
#
# Usage:
#   cd A:\Projects\Dukaan\backend
#   .venv\Scripts\activate
#   python backfill_embeddings.py

import sys
import os
import asyncio

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Same Windows fix used in mcp_server_user/main.py -- asyncpg + ProactorEventLoop
# don't get along on Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
load_dotenv()

from repositories.product_repository import ProductRepository
from config.embeddingModel import embeddingModel
from config.vectorDatabase import vectorDB

BATCH_SIZE = 100


def build_product_text(product) -> str:
    """Text representation of a product used to generate its embedding.
    Keep this in sync with how queries are phrased in mcp_server_user/search.py
    so query-vectors and product-vectors live in a similar semantic space."""
    parts = [product.name]
    if product.description:
        parts.append(product.description)

    category = product.type.value if hasattr(product.type, "value") else str(product.type)
    parts.append(f"Category: {category}")

    if product.brand:
        parts.append(f"Brand: {product.brand}")

    parts.append(f"Gender: {product.gender or 'unisex'}")

    return ". ".join(parts)


async def fetch_all_products():
    repo = ProductRepository()
    return await repo.get_all()


def main():
    print("[BACKFILL] Fetching products from Postgres...")
    products = asyncio.run(fetch_all_products())
    print(f"[BACKFILL] Found {len(products)} products.")

    if not products:
        print("[BACKFILL] No products found in Postgres. Nothing to do.")
        return

    print("[BACKFILL] Loading embedding model...")
    embedder = embeddingModel.getModel()

    print("[BACKFILL] Connecting to Pinecone index (will create it if missing)...")
    index = vectorDB.get_index("dukaan-products")

    total_upserted = 0
    total_batches = (len(products) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num, i in enumerate(range(0, len(products), BATCH_SIZE), start=1):
        batch = products[i:i + BATCH_SIZE]
        texts = [build_product_text(p) for p in batch]

        print(f"[BACKFILL] Batch {batch_num}/{total_batches}: embedding {len(batch)} product(s)...")
        vectors = embedder.embed_documents(texts)

        upsert_payload = []
        for product, vector in zip(batch, vectors):
            category = product.type.value if hasattr(product.type, "value") else str(product.type)
            metadata = {
                "category": category,
                "gender": product.gender or "unisex",
                "name": product.name,
            }
            upsert_payload.append({
                "id": str(product.id),
                "values": vector,
                "metadata": metadata,
            })

        index.upsert(vectors=upsert_payload)
        total_upserted += len(upsert_payload)
        print(f"[BACKFILL] Upserted {total_upserted}/{len(products)} product(s) so far.")

    print(f"[BACKFILL] Done. Total products indexed: {total_upserted}")


if __name__ == "__main__":
    main()
