import json
import time
import uuid
from fastapi import FastAPI, Request, BackgroundTasks, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langgraph.store.memory import InMemoryStore
from fastapi.responses import StreamingResponse
from agents.supervisor import stream_response, stream_events

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
from models.user import UserCreate, UserLogin, UserResponse
from utils.auth import get_password_hash, verify_password, create_access_token, get_current_user_dependency

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
    try:
        # Test Supabase connection instead of creating SQLAlchemy tables
        from config.supabase import test_connection
        await test_connection()
        print("✅ Supabase connection initialized successfully")
    except Exception as e:
        print(f"⚠️  Supabase connection failed: {e}")
        print("🔧 Running in fallback mode for testing")
        # Don't raise the exception - let the app continue without database
        pass

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
async def test_auth(current_user = Depends(get_current_user_dependency)):
    return {"message": "Auth working", "user": current_user.email}

# Your existing auth endpoints
@app.post("/api/auth/signup", response_model=dict)
async def signup(user_data: UserCreate):
    from services.database import get_database_service
    
    try:
        # BACKDOOR FOR TESTING - Allow test signup without database
        if user_data.email == 'test@flowstate.dev' or 'test' in user_data.email:
            access_token = "mock-test-token-123"
            return {
                "token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": "test-user-123",
                    "name": user_data.name,
                    "email": user_data.email,
                    "notion_connected": False,
                    "google_calendar_connected": False
                }
            }
        
        db_service = get_database_service()
        
        # Check if user already exists
        existing_user = await db_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        new_user_data = await db_service.create_user(user_data)
        
        # Create access token
        access_token = create_access_token(data={"sub": new_user_data["id"]})
        
        return {
            "token": access_token,
            "token_type": "bearer",
            "user": new_user_data
        }
        
    except Exception as e:
        if "test" in user_data.email.lower():
            # Fallback for test users if database fails
            return {
                "token": "mock-test-token-123",
                "token_type": "bearer",
                "user": {
                    "id": "test-user-123",
                    "name": user_data.name,
                    "email": user_data.email,
                    "notion_connected": False,
                    "google_calendar_connected": False
                }
            }
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login", response_model=dict)
async def login(user_data: UserLogin):
    from services.database import get_database_service
    
    try:
        # BACKDOOR FOR TESTING - Allow test login without database
        if user_data.email == 'test@flowstate.dev' and user_data.password == 'testpass123':
            access_token = "mock-test-token-123"
            return {
                "token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": "test-user-123",
                    "name": "Test User",
                    "email": "test@flowstate.dev",
                    "notion_connected": False,
                    "google_calendar_connected": False
                }
            }
        
        start_time = time.time()
        
        db_service = get_database_service()
        
        # Authenticate user with database service
        user_data_dict = await db_service.authenticate_user(user_data)
        
        if not user_data_dict:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user_data_dict["id"]})
        
        total_time = time.time() - start_time
        print(f"Login timing - Total: {total_time:.3f}s")
        
        return {
            "token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_data_dict["id"],
                "name": user_data_dict["name"],
                "email": user_data_dict["email"],
                "notion_connected": user_data_dict["notion_connected"],
                "google_calendar_connected": user_data_dict["google_calendar_connected"]
            }
        }
        
    except Exception as e:
        if user_data.email == 'test@flowstate.dev':
            # Fallback for test user if database fails
            return {
                "token": "mock-test-token-123",
                "token_type": "bearer",
                "user": {
                    "id": "test-user-123",
                    "name": "Test User",
                    "email": "test@flowstate.dev",
                    "notion_connected": False,
                    "google_calendar_connected": False
                }
            }
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.get("/api/auth/user", response_model=UserResponse)
async def get_user(current_user = Depends(get_current_user_dependency)):
    return current_user

# Notion OAuth endpoints
@app.get("/api/oauth/notion/authorize")
async def notion_authorize(current_user = Depends(get_current_user_dependency)):
    """Initialize Notion OAuth flow"""
    try:
        from services.notion_oauth import NotionOAuthService
        oauth_service = NotionOAuthService()
        
        auth_data = oauth_service.generate_auth_url(current_user.id)
        
        return {
            "auth_url": auth_data["auth_url"],
            "state": auth_data["state"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Notion auth URL: {str(e)}")

@app.get("/api/oauth/notion/callback")
async def notion_callback(code: str, state: str):
    """Handle Notion OAuth callback"""
    try:
        from services.notion_oauth import NotionOAuthService
        oauth_service = NotionOAuthService()
        
        # Extract user ID from state parameter for security
        if ":" not in state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        user_id, _ = state.split(":", 1)
        
        # Exchange code for token
        token_data = await oauth_service.exchange_code_for_token(code, state)
        
        # Store tokens in database
        success = await oauth_service.store_user_tokens(user_id, token_data)
        
        if success:
            return {
                "success": True,
                "message": "Notion connected successfully",
                "workspace_name": token_data.get("workspace_name")
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store Notion tokens")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(e)}")

@app.get("/api/oauth/notion/status")
async def notion_status(current_user = Depends(get_current_user_dependency)):
    """Check Notion connection status for current user"""
    try:
        from services.notion_oauth import NotionOAuthService
        oauth_service = NotionOAuthService()
        
        token = await oauth_service.get_user_notion_token(current_user.id)
        
        if token:
            # Test the connection
            test_result = await oauth_service.test_notion_connection(token)
            return {
                "connected": test_result["success"],
                "token_valid": test_result["success"],
                "user_info": test_result.get("data") if test_result["success"] else None
            }
        else:
            return {
                "connected": False,
                "token_valid": False,
                "user_info": None
            }
            
    except Exception as e:
        return {
            "connected": False,
            "token_valid": False,
            "error": str(e)
        }

@app.get("/api/integrations/status")
async def get_integrations_status(current_user = Depends(get_current_user_dependency)):
    """Get status of all integrations for current user"""
    try:
        from services.user_tokens import UserTokenService
        status = await UserTokenService.get_user_integrations_status(current_user.id)
        return status
    except Exception as e:
        return {
            "notion": False,
            "google_calendar": False,
            "google_drive": False,
            "error": str(e)
        }
    
@app.post("/debug-agent")
async def debug_agent(current_user = Depends(get_current_user_dependency)):
    try:
        if agent_app is None:
            return {"error": "Agent not loaded"}
        
        # Simple test invocation
        test_thread_id = f"debug_{uuid.uuid4()}"  # ✅ Generate a thread_id
        state = {"messages": [HumanMessage(content="Hello, test message")]}
        config = {
            "configurable": {
                "user_id": current_user.id,
                "todo_category": "default",
                "thread_id": test_thread_id  # ✅ Add the missing thread_id
            },
            "store": memory_store
        }
        
        print("Testing agent invocation...")
        result = agent_app.invoke(state, config=config)
        
        return {
            "success": True,
            "thread_id": test_thread_id,
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
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user = Depends(get_current_user_dependency)):
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
            
            # Create configuration for LangGraph - FIXED: Include thread_id
            config = {
                "configurable": {
                    "user_id": user_id,
                    "todo_category": request.todo_category,
                    "thread_id": session_id  # ✅ Add the missing thread_id
                },
                "store": memory_store
            }
            
            print(f"Invoking agent with state: {state}")
            print(f"Config: {config}")
            
            # Invoke the agent
            result = agent_app.invoke(state, config=config)
            
            print(f"Agent result: {result}")
            print(f"Result type: {type(result)}")
            print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            
            # Extract the assistant's response
            if isinstance(result, dict):
                messages = result.get("messages", [])
                print(f"Found {len(messages)} messages in result")
                
                # Look for the last AI message with content
                ai_response = None
                ai_messages = []
                for msg in messages:
                    if hasattr(msg, 'content') and msg.content:
                        # Check if it's an AI message
                        if hasattr(msg, 'type') and msg.type == "ai":
                            ai_messages.append(str(msg.content))
                            print(f"Found AI message: {msg.content}")
                        elif hasattr(msg, '__class__') and 'AI' in msg.__class__.__name__:
                            ai_messages.append(str(msg.content))
                            print(f"Found AI message by class name: {msg.content}")
                
                # Get the second to last AI message if available, through response agent
                if len(ai_messages) >= 2:
                    ai_response = ai_messages[-2]
                    print(f"Using second to last AI response: {ai_response}")
                elif len(ai_messages) >= 1:
                    ai_response = ai_messages[-1]
                    print(f"Only one AI message found, using it: {ai_response}")
                
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
    
@app.post("/api/chat/stream")
async def stream_chat(request: ChatRequest, current_user = Depends(get_current_user_dependency)):
    user_input = request.message
    session_id = request.session_id or str(uuid.uuid4())
    
    config = {
        "configurable": {
            "user_id": current_user.id,
            "todo_category": request.todo_category,
            "thread_id": session_id
        },
        "store": memory_store
    }

    async def generate():
        try:
            async for chunk in stream_response(user_input, config):
                chunk_json = json.dumps(chunk)
                print(f"Streaming chunk: {chunk_json}")  # Debug log
                yield f"data: {chunk_json}\n\n"
            yield "data: [DONE]\n\n"
        except GeneratorExit:
            # Handle client disconnect gracefully
            print("Client disconnected from stream")
            return
        except Exception as e:
            print(f"Streaming error: {e}")  # Debug log
            import traceback
            traceback.print_exc()
            error_msg = {"type": "error", "content": str(e), "agent": "system"}
            yield f"data: {json.dumps(error_msg)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/api/chat/events")
async def stream_events_endpoint(request: ChatRequest, current_user = Depends(get_current_user_dependency)):
    user_input = request.message
    session_id = request.session_id or str(uuid.uuid4())
    
    config = {
        "configurable": {
            "user_id": current_user.id,
            "todo_category": request.todo_category,
            "thread_id": session_id
        },
        "store": memory_store
    }
    
    async def generate():
        try:
            async for event in stream_events(user_input, config):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"
        except GeneratorExit:
            # Handle client disconnect gracefully
            print("Client disconnected from events stream")
            return
        except Exception as e:
            print(f"Events streaming error: {e}")
            import traceback
            traceback.print_exc()
            error_msg = {"type": "error", "content": str(e), "agent": "system"}
            yield f"data: {json.dumps(error_msg)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)