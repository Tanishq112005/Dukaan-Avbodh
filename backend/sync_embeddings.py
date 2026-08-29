import asyncio
from sqlmodel import select
from sqlalchemy import text
from config.database import db_connection
from models.product import Product
from config.embeddingModel import EmbeddingModel
from config.vectorDatabase import vectorDB

async def main():
    await db_connection.init_db()
    
    # 1. Update DB schema if gender is missing (raw SQL)
    async with db_connection.engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE product ADD COLUMN gender VARCHAR;"))
        except Exception as e:
            print("Gender column might already exist:", e)
    
    # 2. Fetch all products
    session = db_connection.get_session()
    result = await session.execute(select(Product))
    products = result.scalars().all()
    
    print(f"Found {len(products)} products.")
    
    embedder = EmbeddingModel().getModel()
    index = vectorDB.get_index("dukaan-products")
    
    vectors_to_upsert = []
    
    for p in products:
        # Default gender logic based on name/description if gender is None
        if not p.gender:
            desc = (p.name + " " + (p.description or "")).lower()
            if "women" in desc or "girl" in desc or "lady" in desc:
                p.gender = "women"
            elif "men" in desc or "boy" in desc or "guy" in desc:
                p.gender = "men"
            else:
                p.gender = "unisex"
            
            session.add(p)
        
        # 3. Create embedding
        category_val = p.type.value if hasattr(p.type, 'value') else p.type
        search_query = f"Category: {category_val}. Gender: {p.gender}. Matches with: {p.name} {p.description or ''}"
        
        # Checking if embedding model has embed_query
        vector = embedder.embed_query(search_query)
        
        vectors_to_upsert.append({
            "id": str(p.id),
            "values": vector,
            "metadata": {
                "category": category_val,
                "gender": p.gender,
                "name": p.name
            }
        })
        print(f"Generated embedding for Product {p.id}: {p.name}")
    
    await session.commit()
    await session.close()
    
    # 4. Upsert to Pinecone in batches
    batch_size = 100
    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"Upserted batch {i//batch_size + 1}")
        
    print("Done generating embeddings and updating products.")

if __name__ == "__main__":
    asyncio.run(main())
