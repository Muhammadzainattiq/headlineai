from fastapi import FastAPI
from app.routes import auth_routes
from app.db import create_db_and_tables

app = FastAPI()

# Include authentication routes
app.include_router(auth_routes.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()  # Initialize the database tables

@app.get("/")
def read_root():
    return {"message": "Welcome to the Headline AI Backend!"}
