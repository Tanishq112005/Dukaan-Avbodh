# main.py
from fastapi import FastAPI
from config.database import db_connection
from routes import auth_routes, product_routes, user_routes, order_routes, checkout_routes

from fastapi.middleware.cors import CORSMiddleware

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
    await db_connection.init_db()


@app.on_event("shutdown")
async def shutdown():
    await db_connection.close()