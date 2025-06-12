import json
import uuid
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langgraph.store.memory import InMemoryStore

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db, engine, Base
import models
from models.user import User, UserCreate, UserLogin, UserResponse
from utils.auth import get_password_hash, authenticate_user, create_access_token, get_current_user
from pydantic import BaseModel
from typing import Dict

# Import your compiled agent
from agents.supervisor import app as agent_app
import agents.configuration as configuration

# Create FastAPI app
app = FastAPI(title="FlowState API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create an in-memory store for chat sessions
memory_store = InMemoryStore()
sessions = {}

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    todo_category: str = "default"
    session_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    session_id: str

# Create tables in the database
@app.on_event("startup")
async def startup_db_client():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "FlowState API"}


@app.post("/api/auth/signup", response_model=dict)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user with email exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": new_user.id})
    
    return {
        "token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "notion_connected": new_user.notion_connected,
            "google_calendar_connected": new_user.google_calendar_connected
        }
    }

@app.post("/api/auth/login", response_model=dict)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "notion_connected": user.notion_connected,
            "google_calendar_connected": user.google_calendar_connected
        }
    }

@app.get("/api/auth/user", response_model=UserResponse)
async def get_user(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    # Use existing session ID or create a new one
    session_id = request.session_id or str(uuid.uuid4())
    
    # Initialize or get the existing thread
    if session_id not in sessions:
        config = configuration.Configuration(
            user_id=request.user_id,
            todo_category=request.todo_category
        )
        thread = agent_app.create_thread(config=config, store=memory_store)
        sessions[session_id] = thread
    else:
        thread = sessions[session_id]
    
    # Add human message to the thread and run the agent
    result = agent_app.invoke(
        {"messages": [HumanMessage(content=request.message)]}, 
        thread=thread
    )
    
    # Extract the assistant's response(s)
    ai_messages = [msg.content for msg in result["messages"] if msg.type == "ai" and msg.content]
    response = ai_messages[-1] if ai_messages else "I'm processing your request."
    
    return ChatResponse(
        response=response,
        session_id=session_id
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)