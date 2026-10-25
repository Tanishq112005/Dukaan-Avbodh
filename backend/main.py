import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from config.mogodbconfig import nosql_client
from fastapi import FastAPI
from config.database import db_connection 
from auth.routes import router as auth_router
from Product.routes import router as product_router
from UserEvents.routes import router as user_events_router
from Order.routes import router as order_router
from Cart.routes import router as cart_router
from config.chatModel import chatModel
from fastapi.middleware.cors import CORSMiddleware
from config.vectorDatabase import vectorDB
from agents.user import agent_service
from config.redis import redisClient
from agents.merchant import agent_service as merchant_agent_service
app = FastAPI(title="Dukaan")
import warnings
warnings.filterwarnings("ignore", message="Key 'additionalProperties' is not supported")
import logging
class SchemaWarningFilter(logging.Filter):
    def filter(self, record):
        return "Key 'additionalProperties' is not supported in schema" not in record.getMessage()

logging.getLogger().addFilter(SchemaWarningFilter())
logging.getLogger("langchain_google_genai").addFilter(SchemaWarningFilter())
logging.getLogger("google.generativeai").addFilter(SchemaWarningFilter())


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes.payment_routes import router as payment_router

app.include_router(auth_router)
app.include_router(product_router)
app.include_router(user_events_router)
app.include_router(order_router)
app.include_router(cart_router)
app.include_router(payment_router, prefix="/api")

from Chat.routes import router as chat_router
from routes.chat_routes import router as ai_chat_router
from routes import a2a_routes, merchant_routes
app.include_router(chat_router)
app.include_router(ai_chat_router)
app.include_router(a2a_routes.router)
app.include_router(merchant_routes.router)

from negotiation.routes import router as negotiation_router
app.include_router(negotiation_router)


@app.on_event("startup")
async def startup():
    print("\n" + "=" * 60)
    print("[STARTING] Dukaan backend start ho raha hai...")
    print("=" * 60)
     
    print("[REDIS] Redis server se connect ho raha hai...")
    redisClient.get_redis_client()
    print("[OK] Redis ready hai.")

    print("[DB] Database initialize ho rahi hai (tables check/create)...")
    await db_connection.init_db()
    print("[OK] Database ready hai.")
    
    
    '''
    print("[LLM] Chat model (LLM) initialize ho raha hai...")
    print("[LLM] Large initiliaze ho raha hai...")
    chatModel._large_chat_model()
    print("[LLM] Medium initiliaze ho raha hai...")
    chatModel._medium_chat_model()
    print("[LLM] Small initiliaze ho raha hai...")
    chatModel._small_chat_model()
    print("[OK] Chat model ready hai.")
    
    
        
    print("[VECTOR] Vector database (Pinecone) se connect ho raha hai...")
    vectorDB.get_index()
    print("[OK] Vector database ready hai.")
    
    
    print("[MCP] MCP user server se tools load ho rahe hain (user agent ban raha hai)...")
    await agent_service.init_agent()
    print("[OK] User Agent ready hai, saare tools connected hain.")
    
    
    print("[MCP] MCP merchant server se tools load ho rahe hain (merchant agent ban raha hai)...")
    await merchant_agent_service.init_merchant_agent()
    print("[OK] Merchant Agent ready hai.")
    
    
    '''
    
    
    print("Abh MongoDb se connect ho raha hai ...")

    nosql_client.get_client()  
    print("[OK] MongoDB ready hai.")
    
    
    print("=" * 60)
    print("[READY] Dukaan backend poori tarah ready hai - requests handle karne ke liye taiyar!")
    print("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown():
    await db_connection.close()
    nosql_client.close()