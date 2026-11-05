import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./studymate.db")
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET_KEY_BEFORE_DEPLOYMENT")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "1440"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Render/PostgreSQL URLs are normalized for the installed psycopg 3 driver.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

app = FastAPI(title="StudyMate AI API", version="1.0.0")
origins = os.getenv("FRONTEND_ORIGIN", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class ChatInput(BaseModel):
    message: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def make_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Vui lòng đăng nhập")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Tài khoản không tồn tại")
    return user

@app.get("/")
def root():
    return {"name": "StudyMate AI API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/register")
def register(data: RegisterInput, db: Session = Depends(get_db)):
    if len(data.name.strip()) < 2 or len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Tên phải có ít nhất 2 ký tự và mật khẩu ít nhất 8 ký tự")
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email đã được đăng ký")
    user = User(name=data.name.strip(), email=email, password_hash=pwd_context.hash(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": make_token(user.id), "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.post("/api/auth/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    return {"access_token": make_token(user.id), "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email}

@app.get("/api/chat/history")
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).order_by(ChatMessage.id.asc()).limit(100).all()
    return [{"id": row.id, "role": row.role, "content": row.content,
             "created_at": row.created_at.isoformat()} for row in rows]

async def ask_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return ("Chưa cấu hình GEMINI_API_KEY. Hãy thêm API key trong biến môi trường của backend "
                "để bật tính năng trả lời bằng AI. Bạn vẫn có thể kiểm tra đăng ký, đăng nhập và lưu lịch sử.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {"system_instruction": {"parts": [{"text":
        "Bạn là StudyMate AI, trợ lý học tập thân thiện. Trả lời bằng tiếng Việt rõ ràng, "
        "có cấu trúc, giải thích từng bước và khuyến khích người học tự hiểu bài."}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, params={"key": GEMINI_API_KEY}, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Dịch vụ AI đang bận hoặc API key chưa hợp lệ")
    result = response.json()
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail="AI chưa tạo được câu trả lời. Vui lòng thử lại.")

@app.post("/api/chat")
async def chat(data: ChatInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Nội dung không được để trống")
    if len(message) > 8000:
        raise HTTPException(status_code=400, detail="Tin nhắn tối đa 8.000 ký tự")
    answer = await ask_gemini(message)
    db.add_all([ChatMessage(user_id=user.id, role="user", content=message),
                ChatMessage(user_id=user.id, role="assistant", content=answer)])
    db.commit()
    return {"reply": answer}

@app.delete("/api/chat/history")
def clear_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.commit()
    return {"message": "Đã xóa lịch sử trò chuyện"}
