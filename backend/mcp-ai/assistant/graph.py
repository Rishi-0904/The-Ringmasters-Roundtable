# backend/mcp-ai/assistant/graph.py
import os
import sys
from typing import Annotated, Dict, Any, List, Literal, Optional
from typing_extensions import TypedDict
from dotenv import load_dotenv

# Ensure parent and root backend directories are in sys.path to resolve imports correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

# Load environment variables
backend_mcp_env = os.path.join(os.path.dirname(current_dir), ".env")
load_dotenv(backend_mcp_env)
root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), ".env")
load_dotenv(root_env)
load_dotenv() # Fallback to standard CWD load_dotenv

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, AIMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Import our custom memory and vector store components
from assistant.vector_store import VectorItineraryStore
from assistant.memory import UserMemoryManager

# Define Structured Extraction Schema
class ExtractedTripContext(BaseModel):
    intent: Literal["budget", "route", "weather", "events", "itinerary", "general_chat"] = Field(
        description="The user's primary intent. Must select 'general_chat' if they are just saying hello, asking basic questions, or talking about other topics."
    )
    origin: Optional[str] = Field(None, description="The departure/starting city name of the trip.")
    destination: Optional[str] = Field(None, description="The destination city name of the trip.")
    num_days: Optional[int] = Field(None, description="The number of days for the trip/itinerary.")
    travelers: Optional[int] = Field(None, description="The number of travelers / people.")
    start_date: Optional[str] = Field(None, description="The start date of the trip (e.g. YYYY-MM-DD or relative like 'tomorrow').")
    end_date: Optional[str] = Field(None, description="The end date of the trip.")
    budget_type: Optional[str] = Field(None, description="The budget tier (e.g., Low, Mid-range, Luxury).")
    interests: Optional[List[str]] = Field(None, description="Specific interests (e.g., shopping, music, sightseeing, dining).")
    transport_mode: Optional[Literal["flight", "train", "road_trip"]] = Field(
        None,
        description="How the user wants to travel. Must be explicitly stated by the user: 'flight' for air travel, 'train' for rail travel, or 'road_trip' for driving/road journey. Do NOT assume or infer this."
    )
    confidence: float = Field(
        1.0,
        description="Confidence score between 0.0 and 1.0. Set to low (e.g., < 0.5) if any destination/origin or parameter is vague, has a typo, or is ambiguous."
    )

# Define Graph State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    user_preferences: Dict[str, Any]
    retrieved_itineraries: List[Dict[str, Any]]
    context_injected: bool
    trip_context: Dict[str, Any]      # Accumulated parameters across turns
    latest_extraction: Dict[str, Any] # Extracted context from last turn

# Initialize Components
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    GROQ_API_KEY = "gsk_XhWv7aXj98mN4k5P2q1w" # Fallback to user key if available

llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=GROQ_API_KEY, temperature=0.3)

# Strict structured extractor (temperature 0 for determinism)
extractor_llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=GROQ_API_KEY, temperature=0.0).with_structured_output(ExtractedTripContext)

vector_store = VectorItineraryStore()
memory_manager = UserMemoryManager()

# Import the actual Python functions from the server file to use as native tools
from server.travel_mcp_server import calculate_route, get_weather, find_events, generate_itinerary, compute_budget

agent_tools = [calculate_route, get_weather, find_events, generate_itinerary, compute_budget]
llm_with_tools = llm.bind_tools(agent_tools)


def initialize_context(state: AgentState) -> Dict[str, Any]:
    """Retrieves user memory profiles and context-specific logs prior to LLM execution."""
    user_id = state.get("user_id", "default_guest")
    
    # 1. Fetch user memory preferences from Firestore
    prefs = memory_manager.get_user_profile(user_id)
    
    # 2. Retrieve vector store itineraries matching the last user query
    last_query = ""
    for msg in reversed(state["messages"]):
        if msg.type == "user":
            last_query = msg.content
            break
            
    retrieved = []
    if last_query:
        retrieved = vector_store.similarity_search(last_query, user_id=user_id, limit=2)
        
    # Initialize trip_context if missing
    trip_context = state.get("trip_context", {}) or {}
        
    return {
        "user_preferences": prefs,
        "retrieved_itineraries": retrieved,
        "context_injected": True,
        "trip_context": trip_context
    }


def extract_parameters(state: AgentState) -> Dict[str, Any]:
    """Analyzes message history to extract and accumulate parameters into state['trip_context']."""
    messages = state.get("messages", [])
    current_context = state.get("trip_context", {}) or {}
    
    system_prompt = f"""You are a travel parameter extraction agent.
Analyze the conversation history and the latest user message.
Extract parameters mentioned and output them in the schema.

Current Accumulated Parameters (Reference):
{current_context}

Guidelines:
- Retain existing values in the current context unless the user explicitly changes them (e.g. "Actually make it Manali instead" or "no, 3 days instead").
- If the user changes an existing parameter, update it.
- If a parameter/destination is ambiguous, vague, or contains a typo (e.g. "Pris" or "some place cold"), set a low confidence score (< 0.5) for the extraction.
"""
    
    history = [SystemMessage(content=system_prompt)] + messages[-10:]
    
    try:
        extraction = extractor_llm.invoke(history)
        extracted_dict = extraction.dict()
        
        # Merge values
        updated_context = dict(current_context)
        for key, val in extracted_dict.items():
            if key in ["intent", "confidence"]:
                continue
            if val is not None and val != [] and val != "":
                updated_context[key] = val
                
        return {
            "trip_context": updated_context,
            "latest_extraction": extracted_dict
        }
    except Exception as e:
        print(f"[Graph Extractor] Error: {e}")
        # Return fallback values
        return {
            "trip_context": current_context,
            "latest_extraction": {"intent": "general_chat", "confidence": 1.0}
        }


def validate_parameters(state: AgentState) -> Literal["call_model", "clarification_node"]:
    """Conditional router that checks if required parameters are met based on the user's intent.
    Transport mode is MANDATORY for budget, route, and itinerary intents."""
    extraction = state.get("latest_extraction", {}) or {}
    intent = extraction.get("intent", "general_chat")
    context = state.get("trip_context", {}) or {}
    confidence = extraction.get("confidence", 1.0)
    
    # 1. Low Confidence Check
    if confidence < 0.5 and extraction.get("destination"):
        return "clarification_node"
        
    # 2. Intent-specific Required Checks
    if intent in ["budget", "route"]:
        # Required: origin, destination, num_days, transport_mode
        if not context.get("origin") or not context.get("destination") or not context.get("num_days"):
            return "clarification_node"
        if not context.get("transport_mode"):
            return "clarification_node"
            
    elif intent == "itinerary":
        # Required: destination, num_days, transport_mode
        if not context.get("destination") or not context.get("num_days"):
            return "clarification_node"
        if not context.get("transport_mode"):
            return "clarification_node"
            
    elif intent == "weather":
        # Required: destination or origin (location)
        if not context.get("destination") and not context.get("origin"):
            return "clarification_node"
            
    elif intent == "events":
        # Required: destination or origin (city)
        if not context.get("destination") and not context.get("origin"):
            return "clarification_node"
            
    return "call_model"


def clarification_node(state: AgentState) -> Dict[str, Any]:
    """Asks user for missing or clarified inputs before permitting tool node progression.
    Always asks for transport_mode first if missing for planning intents."""
    extraction = state.get("latest_extraction", {}) or {}
    intent = extraction.get("intent", "general_chat")
    context = state.get("trip_context", {}) or {}
    confidence = extraction.get("confidence", 1.0)
    
    missing = []
    
    if confidence < 0.5 and extraction.get("destination"):
        msg = f"I'm not completely sure about your destination. Did you mean **{extraction['destination']}**? Please confirm or provide the destination name."
    elif intent in ["budget", "route", "itinerary"]:
        if not context.get("origin") and intent != "itinerary":
            missing.append("• Departure/Starting city (Origin)")
        if not context.get("destination"):
            missing.append("• Destination city")
        if not context.get("num_days"):
            missing.append("• Trip duration (number of days)")
        if not context.get("transport_mode"):
            missing.append("• Mode of travel — would you like to go by **✈️ Flight**, **🚆 Train**, or **🚗 Road Trip**?")
            
        if intent == "route":
            action_name = "calculate a route"
        elif intent == "budget":
            action_name = "estimate a budget"
        else:
            action_name = "generate your daily itinerary"
        msg = f"I can help you {action_name}! To get started, I just need a few details:\n\n" + "\n".join(missing)
    elif intent in ["weather", "events"]:
        action_name = "check the weather" if intent == "weather" else "find local events"
        msg = f"To {action_name}, please let me know the city name you'd like to check."
    else:
        msg = "I didn't quite capture the travel details. Could you please specify your destination and how long you plan to travel?"
        
    response_msg = AIMessage(content=msg)
    return {"messages": [response_msg]}


def _get_mode_specific_instructions(transport_mode: str) -> str:
    """Returns mode-specific tool usage instructions based on selected transport."""
    if transport_mode == "flight":
        return """TRANSPORT MODE: ✈️ FLIGHT
- Focus on airport-to-airport planning.
- Use compute_budget to get flight pricing and accommodation costs.
- Do NOT use calculate_route for intermediate road stops — flights go directly.
- After landing, plan local activities at the destination city.
- Include airport transfer tips in your response."""
    elif transport_mode == "train":
        return """TRANSPORT MODE: 🚆 TRAIN
- Focus on station-to-station rail planning.
- Use compute_budget to get train pricing and accommodation costs.
- calculate_route can be used to find scenic intermediate stops along the rail corridor.
- Mention major railway junctions or stops along the way.
- Include class recommendations (AC 1st, 2nd, 3rd, Sleeper) in your response."""
    elif transport_mode == "road_trip":
        return """TRANSPORT MODE: 🚗 ROAD TRIP
- This is a driving/road journey — use calculate_route to find intermediate city stops.
- Plan overnight stays at intermediate cities along the route.
- Use compute_budget for accommodation and local expenses at each stop.
- Include approximate driving time between stops.
- Suggest scenic detours, highway rest stops, and fuel station tips.
- Distribute activities across the route stops, not just the final destination."""
    else:
        return "Transport mode not yet determined. Ask the user for their preferred mode."


def call_model(state: AgentState) -> Dict[str, Any]:
    """Generates LLM completion incorporating the system memory context, validated parameters,
    and transport-mode-specific planning instructions."""
    messages = state["messages"]
    user_preferences = state.get("user_preferences", {})
    retrieved_plans = state.get("retrieved_itineraries", [])
    trip_context = state.get("trip_context", {}) or {}
    
    transport_mode = trip_context.get("transport_mode", "")
    mode_instructions = _get_mode_specific_instructions(transport_mode)
    
    # Construct User Memory and Current Parameter block
    system_prompt = f"""You are a luxury Travel Assistant and Planner on The Ringmaster's Roundtable.
Your mission is to understand user queries, invoke travel tools as needed, and synthesize stunning plans.

USER PROFILE MEMORY:
- Favorite Activities: {user_preferences.get('favorite_activities', [])}
- Budget Preference: {user_preferences.get('budget_preferences', 'Standard')}
- Travel Style: {user_preferences.get('travel_style', 'Cultural')}
- Previous Trips: {user_preferences.get('previous_trips', [])}

PREVIOUS PLANS FOUND:
{retrieved_plans}

CURRENT CONFIRMED TRIP DETAILS:
- Origin: {trip_context.get('origin')}
- Destination: {trip_context.get('destination')}
- Duration: {trip_context.get('num_days')} days
- Travelers: {trip_context.get('travelers')} people
- Start Date: {trip_context.get('start_date')}
- End Date: {trip_context.get('end_date')}
- Budget Tier: {trip_context.get('budget_type')}
- Interests: {trip_context.get('interests')}
- Transport Mode: {transport_mode}

{mode_instructions}

Instructions:
1. Since the trip details are ALREADY VALIDATED, you must use these parameters directly when calling tools (like compute_budget or calculate_route). Do not ask the user for them again.
2. If you are calling compute_budget, use the exact start_date and end_date if they are in the parameters (or use start_date/end_date matching the number of days). Pass the transport_mode parameter.
3. If no planning tools are needed (e.g. general discussion), just chat conversationally.
4. CRITICAL: Follow the transport-mode-specific instructions above when selecting which tools to call.
"""
    
    injected_messages = [SystemMessage(content=system_prompt)] + messages
    response = llm_with_tools.invoke(injected_messages)
    
    return {"messages": [response]}


tool_node = ToolNode(agent_tools)


def route_next(state: AgentState) -> Literal["tools", "persist_memory"]:
    """Decides if the LLM output requires calling tool nodes or if execution is ready to complete."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "persist_memory"


def persist_memory(state: AgentState) -> Dict[str, Any]:
    """Extracts new preferences dynamically and updates Firestore user metadata."""
    user_id = state.get("user_id", "default_guest")
    messages = state["messages"]
    
    last_user_message = ""
    for msg in reversed(messages):
        if msg.type == "user":
            last_user_message = msg.content
            break
            
    if last_user_message:
        memory_manager.update_preferences_implicitly(user_id, last_user_message)
        
    return {}


# Build StateGraph
workflow = StateGraph(AgentState)

workflow.add_node("initialize_context", initialize_context)
workflow.add_node("extract_parameters", extract_parameters)
workflow.add_node("clarification_node", clarification_node)
workflow.add_node("call_model", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("persist_memory", persist_memory)

workflow.add_edge(START, "initialize_context")
workflow.add_edge("initialize_context", "extract_parameters")
workflow.add_conditional_edges(
    "extract_parameters",
    validate_parameters,
    {
        "call_model": "call_model",
        "clarification_node": "clarification_node"
    }
)
workflow.add_edge("clarification_node", "persist_memory")

workflow.add_conditional_edges(
    "call_model",
    route_next,
    {
        "tools": "tools",
        "persist_memory": "persist_memory"
    }
)
workflow.add_edge("tools", "call_model")
workflow.add_edge("persist_memory", END)

# Compile using MemorySaver for multi-turn state retention
memory_checkpointer = MemorySaver()
app = workflow.compile(checkpointer=memory_checkpointer)
print("[LangGraph] Travel Assistant compiled successfully with MemorySaver.")
