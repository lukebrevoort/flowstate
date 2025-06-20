import json
import uuid
from fastapi import FastAPI, Request, BackgroundTasks, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langgraph.store.memory import InMemoryStore
from sqlalchemy.orm import Session

# Import your compiled agent
try:
    from agents.supervisor import app as agent_app
    print("✅ Successfully imported agent_app")
except ImportError as e:
    print(f"❌ Failed to import agent_app: {e}")
    agent_app = None

try:
    import agents.configuration as configuration
    print("✅ Successfully imported configuration")
except ImportError as e:
    print(f"❌ Failed to import configuration: {e}")
    configuration = None

# Import authentication components
from db import get_db, engine, Base
import models
from models.user import User, UserCreate, UserLogin, UserResponse
from utils.auth import get_password_hash, authenticate_user, create_access_token, get_current_user

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
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str

@app.get("/")
async def health_check():
    return {
        "status": "healthy", 
        "service": "FlowState API",
        "agent_loaded": agent_app is not None,
        "configuration_loaded": configuration is not None
    }

# Test endpoint for debugging
@app.get("/test-auth")
async def test_auth(current_user: User = Depends(get_current_user)):
    return {"message": "Auth working", "user": current_user.email}

# Your existing auth endpoints
@app.post("/api/auth/signup", response_model=dict)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
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


# Agent debugging endpoint
@app.post("/debug-agent")
async def debug_agent(current_user: User = Depends(get_current_user)):
    try:
        if agent_app is None:
            return {"error": "Agent not loaded"}
        
        # Simple test invocation
        state = {"messages": [HumanMessage(content="Hello, test message")]}
        config = {
            "configurable": {
                "user_id": current_user.id,
                "todo_category": "default"
            },
            "store": memory_store  # ✅ Pass store through config
        }
        
        print("Testing agent invocation...")
        result = agent_app.invoke(state, config=config)  # ✅ Removed store parameter
        
        return {
            "success": True,
            "result_type": str(type(result)),
            "result_keys": list(result.keys()) if isinstance(result, dict) else "Not a dict",
            "message_count": len(result.get("messages", [])) if isinstance(result, dict) else 0,
            "result_sample": str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        print(f"Chat request from user {current_user.email}: {request.message}")
        
        user_id = current_user.id
        session_id = request.session_id or str(uuid.uuid4())
        
        # Check if agent_app is available and properly configured
        if agent_app is None:
            return ChatResponse(
                response=f"Hello {current_user.name}! I received your message: '{request.message}'. The AI agent is currently initializing. For now, I can confirm I'm receiving your messages correctly!",
                session_id=session_id
            )
        
        try:
            # Prepare the state with the user message
            state = {"messages": [HumanMessage(content=request.message)]}
            
            # Create configuration for LangGraph - FIXED: Include store in config
            config = {
                "configurable": {
                    "user_id": user_id,
                    "todo_category": request.todo_category
                },
                "store": memory_store  # ✅ Pass store through config
            }
            
            print(f"Invoking agent with state: {state}")
            print(f"Config: {config}")
            
            # Invoke the agent WITHOUT the store parameter
            result = agent_app.invoke(state, config=config)  # ✅ Removed store parameter
            
            print(f"Agent result: {result}")
            print(f"Result type: {type(result)}")
            print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            
            # Extract the assistant's response - IMPROVED EXTRACTION
            if isinstance(result, dict):
                messages = result.get("messages", [])
                print(f"Found {len(messages)} messages in result")
                
                # Look for the last AI message with content
                ai_response = None
                for msg in reversed(messages):  # Check from last to first
                    print(f"Message type: {type(msg)}, has content: {hasattr(msg, 'content')}")
                    if hasattr(msg, 'content') and msg.content:
                        # Check if it's an AI message
                        if hasattr(msg, 'type') and msg.type == "ai":
                            ai_response = str(msg.content)
                            print(f"Found AI response: {ai_response}")
                            break
                        elif hasattr(msg, '__class__') and 'AI' in msg.__class__.__name__:
                            ai_response = str(msg.content)
                            print(f"Found AI response by class name: {ai_response}")
                            break
                
                if ai_response:
                    response = ai_response
                else:
                    print("No AI messages found, creating default response")
                    response = f"Hello {current_user.name}! I processed your message: '{request.message}'. How can I help you manage your tasks and schedule today?"
            else:
                print(f"Unexpected result format: {type(result)}")
                response = f"Hello {current_user.name}! I processed your message: '{request.message}'. How can I help you manage your tasks and schedule today?"
            
        except Exception as agent_error:
            print(f"Agent invocation error: {agent_error}")
            import traceback
            traceback.print_exc()
            
            # Provide a helpful fallback response instead of an error
            response = f"Hello {current_user.name}! I received your message: '{request.message}'. I'm your AI assistant for managing tasks and schedule. While I'm still calibrating my full capabilities, I'm here to help! What would you like to work on today?"
        
        print(f"Sending response: {response}")
        
        return ChatResponse(
            response=response,
            session_id=session_id
        )
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        import traceback
        traceback.print_exc()
        
        # Even for unexpected errors, provide a user-friendly response
        return ChatResponse(
            response=f"Hello {current_user.name}! I'm experiencing a temporary issue but I'm here to help. Please try sending your message again, or let me know what you'd like to work on!",
            session_id=request.session_id or str(uuid.uuid4())
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)