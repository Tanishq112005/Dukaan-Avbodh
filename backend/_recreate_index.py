# One-time helper: delete the old 768-dim Pinecone index so the app
# recreates it fresh at 384-dim (matching all-MiniLM-L6-v2) on next run.
# Delete this file after running it once.
#
# Usage:
#   cd A:\Projects\Dukaan\backend
#   .venv\Scripts\activate
#   python _recreate_index.py

import os
from dotenv import load_dotenv
load_dotenv()

from pinecone import Pinecone

INDEX_NAME = "dukaan-products"

api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=api_key)

existing = [info["name"] for info in pc.list_indexes()]
if INDEX_NAME in existing:
    print(f"Deleting old index '{INDEX_NAME}' (768-dim)...")
    pc.delete_index(INDEX_NAME)
    print("Deleted. It will be recreated automatically at 384-dim the next time "
          "vectorDB.get_index() runs (e.g. when you run backfill_embeddings.py).")
else:
    print(f"No existing index named '{INDEX_NAME}' found — nothing to delete.")
