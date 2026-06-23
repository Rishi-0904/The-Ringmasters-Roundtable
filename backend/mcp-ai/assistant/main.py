# backend/mcp-ai/assistant/main.py
import os
import sys
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# Import compiled LangGraph workflow app
from assistant.graph import app as langgraph_agent

app = FastAPI(title="Roundtable Conversational AI Service")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatPayload(BaseModel):
    message: str
    user_id: str
    session_id: str

class UpdateContextPayload(BaseModel):
    user_id: str
    session_id: str
    trip_context: dict

@app.post("/api/assistant/context/update")
async def update_context(payload: UpdateContextPayload):
    config = {"configurable": {"thread_id": payload.session_id}}
    try:
        state = await langgraph_agent.aget_state(config)
        current_values = state.values if state else {}
        current_context = current_values.get("trip_context", {}) or {}
        
        # Merge edits
        for k, v in payload.trip_context.items():
            if v is None or v == "":
                current_context.pop(k, None)
            else:
                if k in ["num_days", "travelers"]:
                    try:
                        current_context[k] = int(v)
                    except:
                        current_context[k] = v
                else:
                    current_context[k] = v
                    
        await langgraph_agent.aupdate_state(config, {"trip_context": current_context})
        return {"status": "success", "trip_context": current_context}
    except Exception as e:
        print(f"[FastAPI Update Context] Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/assistant/chat")
async def chat_stream(payload: ChatPayload):
    """
    HTTP POST streaming endpoint utilizing Server-Sent Events (SSE)
    to yield token chunks, tool invocations, and completion states.
    """
    config = {"configurable": {"thread_id": payload.session_id}}
    
    async def sse_event_stream():
        inputs = {
            "messages": [("user", payload.message)],
            "user_id": payload.user_id,
            "context_injected": False
        }
        
        try:
            # Stream events using langgraph's astream_events interface
            async for event in langgraph_agent.astream_events(inputs, config, version="v1"):
                kind = event.get("event")
                
                # 1. Yield streaming tokens from Groq
                if kind == "on_chat_model_stream":
                    token = event["data"]["chunk"].content
                    if token:
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
                # 2. Yield tool call initialization logs
                elif kind == "on_tool_start":
                    tool_name = event.get("name")
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name})}\n\n"
                    
                # 3. Yield tool call results back to the frontend
                elif kind == "on_tool_end":
                    tool_name = event.get("name")
                    output = event["data"].get("output")
                    # Make output string readable and clean
                    if isinstance(output, list) and len(output) > 0:
                        output_summary = f"Calculated travel plan with {len(output)} segments."
                    elif isinstance(output, dict):
                        output_summary = f"Retrieved dataset: {list(output.keys())}."
                    else:
                        output_summary = str(output)[:150] + "..."
                        
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name, 'result': output_summary})}\n\n"
            
            # Fetch final trip_context state and yield it to the frontend
            state_val = await langgraph_agent.aget_state(config)
            if state_val:
                final_context = state_val.values.get("trip_context", {}) or {}
                yield f"data: {json.dumps({'type': 'trip_context', 'context': final_context})}\n\n"
                
            # Yield final completion notice
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            print(f"[FastAPI Assistant] Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "assistant-api"}

if __name__ == "__main__":
    import uvicorn
    # Runs FastAPI server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
