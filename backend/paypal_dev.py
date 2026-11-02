from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.paypal_routes import router
from backend.db import init_db

init_db()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)