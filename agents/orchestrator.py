from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Literal

import os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import dotenv
import logging
from datetime import datetime

from project_manager import tools as project_tools
from scheduler_agent import tools as scheduler_tools

# Define shared state (modify based on your agents' needs)
class OrchestratorState(BaseModel):
    user_input: str
    scheduler_data: Optional[Dict] = None
    project_data: Optional[Dict] = None
    next_agent: Literal["orchestrator", "scheduler", "project_manager"] = "orchestrator"
    history: List[str] = Field(default_factory=list)
    output: Optional[str] = None


# Load environment variables

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the LLM instances
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Define the orchestrator node
def orchestrator(state: OrchestratorState) -> OrchestratorState:
    """Determine which agent should handle the user request"""
    
    # Define a template for the orchestrator
    prompt = ChatPromptTemplate.from_template("""
    You are an orchestrator that decides which agent should handle a user request.
    Based on the user input, determine if the request is related to:
    
    1. Scheduling/Calendar management (scheduler)
    2. Assignment/Project management in Notion (project_manager)
    
    Respond with only ONE of the following: "scheduler" or "project_manager"
    
    User input: {input}
    """)
    
    # Run the prompt
    response = prompt.invoke({"input": state.user_input}) | llm 
    agent_choice = response.content.strip().lower()
    
    # Update state
    state.next_agent = agent_choice
    state.history.append(f"Orchestrator decided to route to: {agent_choice}")
    
    return state

# Define the project manager node
def project_manager(state: OrchestratorState) -> OrchestratorState:
    """Handle project/assignment management tasks"""
    
    # Re-use the prompt from your existing project manager
    from project_manager import prompt, tools
    
    # Create a simplified version of your existing agent executor
    chain = prompt | llm.bind(tools=tools)
    
    # Execute and capture result
    response = chain.invoke({"input": state.user_input})
    
    # Update the state
    state.output = response.content
    state.history.append(f"Project Manager: {response.content}")
    state.next_agent = "orchestrator"
    
    return state


# Define the scheduler node  
def scheduler(state: OrchestratorState) -> OrchestratorState:
    """Handle calendar scheduling tasks"""
    
    # Re-use the prompt from your existing scheduler
    from scheduler_agent import prompt, tools
    
    # Create a simplified version of your existing agent executor
    chain = prompt | llm.bind(tools=tools)
    
    # Execute and capture result
    response = chain.invoke({"input": state.user_input})
    
    # Update the state
    state.output = response.content
    state.history.append(f"Scheduler: {response.content}")
    state.next_agent = "orchestrator"
    
    return state



# Define the routing function
def router(state: OrchestratorState) -> str:
    """Route to the next agent based on state.next_agent"""
    return state.next_agent

# Build the graph
def build_graph():
    workflow = StateGraph(OrchestratorState)

    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("scheduler", scheduler)
    workflow.add_node("project_manager", project_manager)

    workflow.add_conditional_edges(
        "orchestrator",
        router,
        {
            "scheduler": "scheduler",
            "project_manager": "project_manager",
            "end": END
        }
    )

    workflow.add_edge("scheduler", "project_manager")
    workflow.set_entry_point("orchestrator")
    
    return workflow.compile()

# Create the executable graph
graph = build_graph()

# Main execution function
def process_user_input(user_input: str) -> str:
    """Process the user input through the graph and return the response"""
    
    # Create the initial state
    state = OrchestratorState(user_input=user_input)
    
    # Execute the graph
    final_state = graph.invoke(state)
    
    return final_state.output

# Add CLI interface for testing
if __name__ == "__main__":
    print("Flowstate Assistant (Type 'exit' to quit)")
    print("----------------------------------------")
    
    while True:
        user_input = input("\nHow can I help you today? ")
        
        if user_input.lower() in ("exit", "quit"):
            break
        
        try:
            response = process_user_input(user_input)
            print(f"\nAssistant: {response}")
        except Exception as e:
            print(f"\nError: {str(e)}")
            logger.error(f"Error in processing: {str(e)}", exc_info=True)