from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import asyncio

app = FastAPI(title="TestSystem")

# Security
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory storage (будем использовать пока без БД для быстрого старта)
users_db = {
    "admin": {
        "username": "admin",
        "password": pwd_context.hash("admin123"),  # пароль: admin123
        "role": "admin"
    },
    "client1": {
        "username": "client1",
        "password": pwd_context.hash("client123"),  # пароль: client123
        "role": "client"
    }
}

# Active connections
active_clients: Dict[str, dict] = {}
admin_connections: List[WebSocket] = []

# Root endpoint
@app.get("/")
async def root():
    return {"message": "TestSystem API", "status": "running"}

# Authentication
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "active_clients": len(active_clients),
        "admin_connections": len(admin_connections)
    }
# HTML Routes
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

templates = Jinja2Templates(directory="templates")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/client", response_class=HTMLResponse)
async def client_page(request: Request):
    return templates.TemplateResponse("client.html", {"request": request})

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
