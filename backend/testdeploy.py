import asyncio
from langgraph_sdk import get_client
from langchain_core.messages import HumanMessage
from langchain_core.messages import convert_to_messages
from langchain_core.messages import HumanMessage, SystemMessage

async def main():
    client = get_client(url="http://localhost:9876")
    thread = await client.threads.create()
    user_input = "What do I have going on today?"
    config = {"configurable": {"user_id": "Test"}}
    graph_name = "main" 
    run = await client.runs.create(thread["thread_id"], graph_name, input={"messages": [HumanMessage(content=user_input)]}, config=config)
    
    # Get and print the run
    result = await client.runs.get(thread["thread_id"], run["run_id"])
    print(result)

# Run the async function
asyncio.run(main())