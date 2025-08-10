from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import sys

# Import the tools
from tools import DuckDuckGoSearchRun, weather_info_tool, hub_stats_tool
from retriever import guest_info_tool

# Load environment variables from .env file
# Try multiple possible locations
env_loaded = load_dotenv()
if not env_loaded:
    # Try parent directory
    load_dotenv('../.env')
    # Try explicit path
    load_dotenv('./.env')

# Get API key from environment - try multiple possible names
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")

# Debug: Print environment info
print(f"Environment variables loaded: {env_loaded}")
print(f"Current directory: {os.getcwd()}")
print(f".env file exists in current dir: {os.path.exists('.env')}")
print(f"GEMINI_API_KEY found: {'Yes' if GEMINI_API_KEY else 'No'}")

if not GEMINI_API_KEY:
    print("\n❌ ERROR: GEMINI_API_KEY not found!")
    print("\nPlease ensure you have a .env file with one of these variables:")
    print("  GEMINI_API_KEY=your_api_key_here")
    print("  GOOGLE_API_KEY=your_api_key_here")
    print("  GOOGLE_GEMINI_API_KEY=your_api_key_here")
    print("\nYou can also set it directly in your terminal:")
    print("  export GEMINI_API_KEY='your_api_key_here'")
    sys.exit(1)

# Initialize the web search tool
search_tool = DuckDuckGoSearchRun()

# Initialize Gemini chat model
try:
    chat = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        google_api_key=GEMINI_API_KEY,
        temperature=0
    )
    print("✅ Gemini API initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing Gemini API: {e}")
    sys.exit(1)

# Bind tools to the chat model
tools = [guest_info_tool, search_tool, weather_info_tool, hub_stats_tool]
chat_with_tools = chat.bind_tools(tools)

# Generate the AgentState and Agent graph
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def assistant(state: AgentState):
    return {
        "messages": [chat_with_tools.invoke(state["messages"])],
    }

# Build the graph
builder = StateGraph(AgentState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message requires a tool, route to tools
    # Otherwise, provide a direct response
    tools_condition,
)
builder.add_edge("tools", "assistant")

# Compile the graph into an agent
alfred = builder.compile()

def run_alfred(user_query: str):
    """Run Alfred with a user query and return the response."""
    print(f"\n🎩 User Query: {user_query}")
    print("-" * 50)
    
    try:
        messages = [HumanMessage(content=user_query)]
        response = alfred.invoke({"messages": messages})
        
        # Get the final response
        final_response = response['messages'][-1].content
        print(f"🎩 Alfred's Response:\n{final_response}")
        print("-" * 50)
        
        return final_response
    except Exception as e:
        print(f"❌ Error: {e}")
        print("-" * 50)
        return None

if __name__ == "__main__":
    # Example queries to test Alfred
    test_queries = [
        "Tell me about guest Lady Ada Lovelace",
        "What's the weather in Paris right now?",
        "Who is the current President of France?",
        "What's Qwen's most downloaded model on HuggingFace?",
        "Find information about guest Einstein and what's the weather in his hometown?"
    ]
    
    print("\n🎩 Welcome to Alfred - Your AI Assistant!")
    print("=" * 50)
    
    # Run interactive mode
    while True:
        print("\nChoose an option:")
        print("1. Run test queries")
        print("2. Enter your own query")
        print("3. Exit")
        
        choice = input("\nYour choice (1-3): ").strip()
        
        if choice == "1":
            for query in test_queries:
                run_alfred(query)
                input("\nPress Enter to continue...")
        
        elif choice == "2":
            user_query = input("\nEnter your query: ").strip()
            if user_query:
                run_alfred(user_query)
            else:
                print("Please enter a valid query.")
        
        elif choice == "3":
            print("\n🎩 Goodbye! Alfred signing off.")
            break
        
        else:
            print("Invalid choice. Please select 1, 2, or 3.")