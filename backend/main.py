# main.py
import sys
import asyncio

# Windows par asyncpg (SSL connections) ProactorEventLoop ke saath fail hota hai
# (ConnectionResetError: WinError 64). Selector loop policy chahiye, kisi bhi
# asyncio loop ke banne se PEHLE (uvicorn is import ke baad apna loop banata hai).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from config.database import db_connection 
from routes import auth_routes, product_routes, user_routes, order_routes, checkout_routes
from config.chatModel import chatModel
from fastapi.middleware.cors import CORSMiddleware
from config.embeddingModel import embeddingModel
from config.vectorDatabase import vectorDB
from agents import agent_service
app = FastAPI(title="Sauda API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global WebSocket Manager (Imported from utils to prevent circular dependencies)
from utils.websocket_manager import manager
app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(user_routes.router)
app.include_router(order_routes.router)
app.include_router(checkout_routes.router)

from routes import chat_routes
app.include_router(chat_routes.router)


@app.on_event("startup")
async def startup():
    print("\n" + "=" * 60)
    print("🚀 Dukaan backend start ho raha hai...")
    print("=" * 60)

    print("🗄️  Database initialize ho rahi hai (tables check/create)...")
    await db_connection.init_db()
    print("✅ Database ready hai.")

    print("🧠 Chat model (LLM) initialize ho raha hai...")
    chatModel.get_chat_model()
    print("✅ Chat model ready hai.")

    print("📦 Vector database (Pinecone) se connect ho raha hai...")
    vectorDB.get_index()
    print("✅ Vector database ready hai.")

    # MCP server (mcp_server/main.py) ek ALAG process ke roop mein pehle se chal
    # raha hona chahiye (python -m mcp_server.main), tabhi yeh connect ho payega.
    print("🔧 MCP server se tools load ho rahe hain (agent ban raha hai)...")
    await agent_service.init_agent()
    print("✅ Agent ready hai, saare tools connected hain.")

    print("=" * 60)
    print("🎉 Dukaan backend poori tarah ready hai — requests handle karne ke liye taiyar!")
    print("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown():
    await db_connection.close()
    