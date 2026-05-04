from fastapi import FastAPI, HTTPException
from backend.db import database, engine, metadata
from backend.models import users
from backend.schemas import UserCreate, UserLogin
import secrets
import bcrypt

app = FastAPI()
metadata.create_all(engine)

# ── Password helpers using bcrypt directly (passlib is unmaintained) ──────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

# In-memory token store: {token: {"username": ..., "role": ...}}
active_sessions: dict = {}

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/register")
async def register(user: UserCreate):
    query = users.select().where(users.c.username == user.username)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = hash_password(user.password)
    query = users.insert().values(
        username=user.username,
        password=hashed_password,
        role=user.role,
    )
    await database.execute(query)
    return {"message": "User registered successfully", "role": user.role}


@app.post("/login")
async def login(user: UserLogin):
    query = users.select().where(users.c.username == user.username)
    existing_user = await database.fetch_one(query)
    if not existing_user:
        raise HTTPException(status_code=400, detail="Invalid Username")

    if not verify_password(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid Password")

    token = secrets.token_hex(32)
    active_sessions[token] = {
        "username": existing_user["username"],
        "role": existing_user["role"],
    }

    return {
        "message": "Login successful",
        "token": token,
        "role": existing_user["role"],
        "username": existing_user["username"],
    }


@app.post("/logout")
async def logout(token: str):
    active_sessions.pop(token, None)
    return {"message": "Logged out"}