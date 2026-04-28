"""
Jarvis FastAPI Expertise Module
Comprehensive knowledge and coding capabilities for Python FastAPI development.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import re


@dataclass
class FastAPIProjectTemplate:
    name: str
    description: str
    dependencies: Dict[str, str]
    files: Dict[str, str]
    setup_commands: List[str]


@dataclass
class FastAPIPattern:
    name: str
    description: str
    code: str
    use_case: str


class FastAPIExpertise:
    """Comprehensive FastAPI knowledge and coding expertise."""
    
    def __init__(self):
        self.templates = self._build_templates()
        self.patterns = self._build_patterns()
        self.best_practices = self._build_best_practices()
    
    def _build_templates(self) -> Dict[str, FastAPIProjectTemplate]:
        """Build FastAPI project templates."""
        
        return {
            "microservice": FastAPIProjectTemplate(
                name="FastAPI Microservice",
                description="Production-ready microservice with authentication, database, and testing",
                dependencies={
                    "fastapi": "^0.104.0",
                    "uvicorn[standard]": "^0.24.0",
                    "sqlalchemy": "^2.0.0",
                    "alembic": "^1.12.0",
                    "psycopg2-binary": "^2.9.0",
                    "pydantic": "^2.5.0",
                    "pydantic-settings": "^2.1.0",
                    "python-jose[cryptography]": "^3.3.0",
                    "passlib[bcrypt]": "^1.7.4",
                    "python-multipart": "^0.0.6",
                    "pytest": "^7.4.0",
                    "pytest-asyncio": "^0.21.0",
                    "httpx": "^0.25.0",
                    "black": "^23.11.0",
                    "isort": "^5.12.0",
                    "flake8": "^6.1.0",
                    "mypy": "^1.7.0"
                },
                files={
                    "requirements.txt": '''fastapi==0.104.0
uvicorn[standard]==0.24.0
sqlalchemy==2.0.0
alembic==1.12.0
psycopg2-binary==2.9.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.0
pytest-asyncio==0.21.0
httpx==0.25.0''',
                    
                    "main.py": '''from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.auth import verify_token

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A production-ready FastAPI microservice",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )''',
                    
                    "app/core/config.py": '''from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Microservice"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()''',
                    
                    "app/core/database.py": '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()''',
                    
                    "app/core/auth.py": '''from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # In a real app, you'd fetch user from database here
    return {"username": username}''',
                    
                    "app/models/user.py": '''from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())''',
                    
                    "app/schemas/user.py": '''from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str''',
                    
                    "app/api/v1/api.py": '''from fastapi import APIRouter
from app.api.v1.endpoints import users, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])''',
                    
                    "app/api/v1/endpoints/auth.py": '''from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.auth import authenticate_user, create_access_token
from app.core.config import settings
from app.schemas.user import UserCreate, User
from app.services.user_service import UserService

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return await user_service.create_user(user)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}''',
                    
                    "app/api/v1/endpoints/users.py": '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.user import User, UserUpdate
from app.services.user_service import UserService

router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_service = UserService(db)
    return await user_service.get_users(skip=skip, limit=limit)

@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_service = UserService(db)
    return await user_service.update_user(current_user.id, user_update)''',
                    
                    "app/services/user_service.py": '''from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate
from app.core.auth import get_password_hash

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(self, user: UserCreate) -> UserModel:
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.email == email).first()
    
    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.username == username).first()
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        return self.db.query(UserModel).offset(skip).limit(limit).all()
    
    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserModel:
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            update_data = user_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            self.db.commit()
            self.db.refresh(user)
        return user''',
                    
                    "tests/test_auth.py": '''import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"

def test_login_user():
    # First register a user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "loginpassword123"
        }
    )
    
    # Then login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "loginuser", "password": "loginpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"''',
                    
                    ".env.example": '''# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=604800

# CORS Origins (comma-separated)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
ENVIRONMENT=development''',
                    
                    "Dockerfile": '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]''',
                    
                    "docker-compose.yml": '''version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: fastapi_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db/fastapi_db
    volumes:
      - .:/app

volumes:
  postgres_data:'''
                },
                setup_commands=[
                    "mkdir -p app/{core,models,schemas,api/v1/endpoints,services,tests}",
                    "python -m venv venv",
                    "source venv/bin/activate  # On Windows: venv\\Scripts\\activate",
                    "pip install -r requirements.txt",
                    "cp .env.example .env",
                    "# Edit .env with your database URL and secret key",
                    "# Run database migrations: alembic init alembic",
                    "# Run the app: uvicorn main:app --reload"
                ]
            ),
            
            "simple_api": FastAPIProjectTemplate(
                name="Simple FastAPI",
                description="Minimal FastAPI setup for quick prototyping",
                dependencies={
                    "fastapi": "^0.104.0",
                    "uvicorn[standard]": "^0.24.0",
                    "pydantic": "^2.5.0"
                },
                files={
                    "main.py": '''from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Simple API", version="1.0.0")

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float

# In-memory storage
items_db = []
next_id = 1

@app.get("/")
async def root():
    return {"message": "Welcome to Simple API"}

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items_db:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    global next_id
    item_dict = item.model_dump()
    item_dict["id"] = next_id
    next_id += 1
    items_db.append(item_dict)
    return item_dict

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    for i, existing_item in enumerate(items_db):
        if existing_item["id"] == item_id:
            item_dict = item.model_dump()
            item_dict["id"] = item_id
            items_db[i] = item_dict
            return item_dict
    return {"error": "Item not found"}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            del items_db[i]
            return {"message": "Item deleted"}
    return {"error": "Item not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)'''
                },
                setup_commands=[
                    "pip install fastapi uvicorn pydantic",
                    "uvicorn main:app --reload"
                ]
            )
        }
    
    def _build_patterns(self) -> Dict[str, FastAPIPattern]:
        """Build common FastAPI patterns."""
        
        return {
            "dependency_injection": FastAPIPattern(
                name="Dependency Injection",
                description="Using FastAPI's dependency injection system",
                code='''
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user

async def get_user_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Dependency automatically handles database session and authentication
    items = db.query(Item).filter(Item.owner_id == current_user.id).all()
    return items''',
                use_case="Database access, authentication, configuration"
            ),
            
            "background_tasks": FastAPIPattern(
                name="Background Tasks",
                description="Running tasks in the background",
                code='''
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_notification(email: str, message: str):
    with open("log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, "Some notification")
    return {"message": "Notification sent in the background"}''',
                use_case="Email sending, file processing, data cleanup"
            ),
            
            "middleware": FastAPIPattern(
                name="Custom Middleware",
                description="Creating custom middleware for cross-cutting concerns",
                code='''
from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.base import BaseHTTPMiddleware
import time

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

app = FastAPI(middleware=[Middleware(ProcessTimeMiddleware)])''',
                use_case="Logging, timing, CORS, authentication"
            ),
            
            "exception_handlers": FastAPIPattern(
                name="Exception Handlers",
                description="Global exception handling",
                code='''
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )''',
                use_case="Error handling, validation, custom exceptions"
            ),
            
            "websockets": FastAPIPattern(
                name="WebSocket Support",
                description="Real-time communication with WebSockets",
                code='''
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")''',
                use_case="Chat applications, real-time updates, notifications"
            )
        }
    
    def _build_best_practices(self) -> Dict[str, List[str]]:
        """Build FastAPI best practices."""
        
        return {
            "performance": [
                "Use async/await for I/O operations",
                "Implement proper database connection pooling",
                "Use response models for data validation",
                "Implement caching strategies",
                "Use Pydantic for efficient data validation",
                "Optimize database queries with proper indexing",
                "Use background tasks for long-running operations"
            ],
            "security": [
                "Always use HTTPS in production",
                "Implement proper authentication and authorization",
                "Validate all input data with Pydantic models",
                "Use environment variables for sensitive configuration",
                "Implement rate limiting",
                "Sanitize database queries to prevent SQL injection",
                "Use CORS middleware properly"
            ],
            "architecture": [
                "Organize code in logical modules (models, schemas, services)",
                "Use dependency injection for testability",
                "Separate business logic from API layer",
                "Implement proper error handling",
                "Use type hints throughout the codebase",
                "Follow RESTful API design principles",
                "Implement proper logging and monitoring"
            ],
            "testing": [
                "Write unit tests for business logic",
                "Test API endpoints with TestClient",
                "Use pytest fixtures for database setup",
                "Mock external dependencies in tests",
                "Test both success and error scenarios",
                "Use parameterized tests for multiple inputs",
                "Implement integration tests for complete workflows"
            ]
        }
    
    def get_template(self, template_name: str) -> Optional[FastAPIProjectTemplate]:
        """Get a specific project template."""
        return self.templates.get(template_name)
    
    def get_pattern(self, pattern_name: str) -> Optional[FastAPIPattern]:
        """Get a specific pattern."""
        return self.patterns.get(pattern_name)
    
    def get_best_practices(self, category: str) -> List[str]:
        """Get best practices for a specific category."""
        return self.best_practices.get(category, [])
    
    def list_templates(self) -> List[str]:
        """List all available templates."""
        return list(self.templates.keys())
    
    def list_patterns(self) -> List[str]:
        """List all available patterns."""
        return list(self.patterns.keys())


# Singleton instance
fastapi_expertise = FastAPIExpertise()
