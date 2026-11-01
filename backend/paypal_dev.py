from fastapi import FastAPI
from backend.paypal_routes import router

app = FastAPI()
app.include_router(router)