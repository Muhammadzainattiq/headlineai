from fastapi import FastAPI
from app.routes import auth_routes, ai_routes
from app.db import create_db_and_tables
from app.ai.main_agent import compile_main_agent
from app.ai.sub_agent import compile_sub_agent
from contextlib import asynccontextmanager

main_agent = None
sub_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables...")
    create_db_and_tables()
    print("Table created")
    global sub_agent
    print("Compiling Sub Agent...")
    sub_agent = compile_sub_agent()  # Await sub_agent compilation
    print("Sub Agent compiled")
    global main_agent
    print("Compiling Main Agent...")
    main_agent = compile_main_agent(sub_agent)
    print("Main Agent compiled")
    try:
        yield
    finally:
        print("Lifespan context ended")

app = FastAPI(lifespan=lifespan)

# Include authentication and AI routes separately
app.include_router(auth_routes.auth_router)
app.include_router(ai_routes.ai_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Headline AI Backend!"}
