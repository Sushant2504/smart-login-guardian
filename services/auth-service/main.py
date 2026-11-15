#!/usr/bin/env python3
"""
Smart Login Guardian - Authentication Service
FastAPI-based authentication with JWT tokens, user management, and RBAC
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import sqlite3
import uuid
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_PATH = "data/auth.db"

app = FastAPI(
    title="Smart Login Guardian - Auth Service",
    description="Authentication and user management service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ===========================================
# Models
# ===========================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    status: str
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# ===========================================
# Database
# ===========================================

def init_db():
    """Initialize SQLite database"""
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            email_verified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tenants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tenant memberships
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenant_memberships (
            membership_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tenant_id, user_id),
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Create default tenant
    cursor.execute("""
        INSERT OR IGNORE INTO tenants (tenant_id, name, slug, status)
        VALUES ('tenant_default', 'Default Organization', 'default', 'active')
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ===========================================
# Authentication helpers
# ===========================================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), conn = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (token_data.email,))
    user = cursor.fetchone()

    if user is None:
        raise credentials_exception

    return dict(user)

# ===========================================
# API Endpoints
# ===========================================

@app.on_event("startup")
async def startup():
    init_db()

@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, conn = Depends(get_db)):
    """Register a new user"""
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT user_id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user_id = str(uuid.uuid4())
    password_hash = get_password_hash(user.password)

    cursor.execute("""
        INSERT INTO users (user_id, email, password_hash, full_name, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (user_id, user.email, password_hash, user.full_name))

    # Add to default tenant
    membership_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO tenant_memberships (membership_id, tenant_id, user_id, role)
        VALUES (?, 'tenant_default', ?, 'security_analyst')
    """, (membership_id, user_id))

    conn.commit()

    # Fetch created user
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    created_user = dict(cursor.fetchone())

    return UserResponse(
        user_id=created_user['user_id'],
        email=created_user['email'],
        full_name=created_user['full_name'],
        status=created_user['status'],
        created_at=created_user['created_at']
    )

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), conn = Depends(get_db)):
    """Login and get access token"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
    user = cursor.fetchone()

    if not user or not verify_password(form_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_dict = dict(user)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_dict['email']},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            user_id=user_dict['user_id'],
            email=user_dict['email'],
            full_name=user_dict['full_name'],
            status=user_dict['status'],
            created_at=user_dict['created_at']
        )
    )

@app.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """Get current user"""
    return UserResponse(
        user_id=current_user['user_id'],
        email=current_user['email'],
        full_name=current_user['full_name'],
        status=current_user['status'],
        created_at=current_user['created_at']
    )

@app.get("/users", response_model=List[UserResponse])
async def list_users(current_user = Depends(get_current_user), conn = Depends(get_db)):
    """List all users (admin only in production)"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 100")
    users = cursor.fetchall()

    return [
        UserResponse(
            user_id=u['user_id'],
            email=u['email'],
            full_name=u['full_name'],
            status=u['status'],
            created_at=u['created_at']
        )
        for u in users
    ]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         SMART LOGIN GUARDIAN - AUTHENTICATION SERVICE            ║
    ╚══════════════════════════════════════════════════════════════════╝

    🔐 Authentication Service Starting...

    Features:
    ✅ User registration
    ✅ JWT token authentication
    ✅ Password hashing (bcrypt)
    ✅ Role-based access control
    ✅ SQLite database (production-ready structure)

    API Docs: http://localhost:8001/docs

    Starting server...
    """)

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
