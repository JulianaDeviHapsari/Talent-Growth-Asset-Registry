from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uuid, hashlib, jwt
from datetime import datetime, timedelta, timezone

app = FastAPI(title="Asset Registry API")
bearer_scheme = HTTPBearer()

DB_USERS  = {}
DB_ASSETS = {}
SECRET_KEY = "secret-key-kamu"
ALGORITHM  = "HS256"

@app.get("/")
def root():
    return {"message": "Asset Registry API berjalan!"}

class RegisterUserReq(BaseModel):
    username: str
    password: str
    wallet: str

class LoginReq(BaseModel):
    username: str
    password: str

class RegisterAssetReq(BaseModel):
    name: str
    asset_type: str
    description: str = None

def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        payload  = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username not in DB_USERS:
            raise HTTPException(status_code=401, detail="User tidak ditemukan")
        return DB_USERS[username]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Token tidak valid")
    
@app.post("/auth/register", status_code=201)
def register(body: RegisterUserReq):
    if body.username in DB_USERS:
        raise HTTPException(status_code=409, detail="Username sudah ada")
    DB_USERS[body.username] = {
        "username": body.username,
        "password_hash": hashlib.sha256(body.password.encode()).hexdigest(),
        "wallet": body.wallet,
    }
    return {"message": "Registrasi berhasil", "username": body.username}

@app.post("/auth/login")
def login(body: LoginReq):
    user    = DB_USERS.get(body.username)
    pw_hash = hashlib.sha256(body.password.encode()).hexdigest()
    if not user or user["password_hash"] != pw_hash:
        raise HTTPException(status_code=401, detail="Username/password salah")
    token = create_token(body.username)
    return {"access_token": token, "token_type": "Bearer"}

@app.post("/assets", status_code=201)
def register_asset(body: RegisterAssetReq, user: dict = Depends(get_current_user)):
    asset_id = str(uuid.uuid4())
    DB_ASSETS[asset_id] = {
        "asset_id":   asset_id,
        "name":       body.name,
        "asset_type": body.asset_type,
        "owner":      user["wallet"],
        "tx_hash":    "0x" + hashlib.sha256(asset_id.encode()).hexdigest(),
    }
    return DB_ASSETS[asset_id]

@app.get("/assets")
def list_assets(user: dict = Depends(get_current_user)):
    return [a for a in DB_ASSETS.values() if a["owner"] == user["wallet"]]

@app.get("/assets/{asset_id}")
def get_asset(asset_id: str, user: dict = Depends(get_current_user)):
    asset = DB_ASSETS.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset tidak ditemukan")
    return asset