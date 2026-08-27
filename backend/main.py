# main.py
from fastapi import FastAPI
from config.database import db_connection
from routes import auth_routes, product_routes, user_routes, order_routes, checkout_routes

app = FastAPI(title="Sauda API")

app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(user_routes.router)
app.include_router(order_routes.router)
app.include_router(checkout_routes.router)


@app.on_event("startup")
async def startup():
    await db_connection.init_db()


@app.on_event("shutdown")
async def shutdown():
    await db_connection.close()