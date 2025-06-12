import json
import uuid
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage
from langgraph.store.memory import InMemoryStore

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

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "FlowState API"}

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