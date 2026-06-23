# backend/mcp-ai/assistant/test_assistant.py
import os
import sys
import uuid
import asyncio

# Ensure parent and root backend directories are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

from assistant.graph import app as agent

async def run_tests():
    print("==================================================")
    print("RUNNING AI TRAVEL ASSISTANT REGRESSION TEST SUITE")
    print("==================================================")

    # ============================================================
    # Test 1: Plan trip -> Ask for destination, no tools.
    # ============================================================
    print("\n[TEST 1] User prompt: 'Plan trip'")
    session_1 = f"test-session-{uuid.uuid4()}"
    config_1 = {"configurable": {"thread_id": session_1}}
    
    inputs_1 = {
        "messages": [("user", "Plan trip")],
        "user_id": "test_user",
        "context_injected": False
    }
    
    res_1 = await agent.ainvoke(inputs_1, config_1)
    last_msg_1 = res_1["messages"][-1].content
    context_1 = res_1.get("trip_context", {})
    
    print(f"Assistant Response: {last_msg_1}")
    print(f"Extracted Context: {context_1}")
    
    assert "destination" not in context_1 or context_1.get("destination") is None, "Failed: Destination should be None"
    assert "Destination city" in last_msg_1 or "destination" in last_msg_1.lower(), "Failed: Did not ask for destination"
    print("-> TEST 1 PASSED: Correctly asked for destination with no tool execution.")

    # ============================================================
    # Test 2: Trip from Delhi to Shimla -> Ask for duration, no tools.
    # ============================================================
    print("\n[TEST 2] User prompt: 'Trip from Delhi to Shimla'")
    session_2 = f"test-session-{uuid.uuid4()}"
    config_2 = {"configurable": {"thread_id": session_2}}
    
    inputs_2 = {
        "messages": [("user", "Trip from Delhi to Shimla")],
        "user_id": "test_user",
        "context_injected": False
    }
    
    res_2 = await agent.ainvoke(inputs_2, config_2)
    last_msg_2 = res_2["messages"][-1].content
    context_2 = res_2.get("trip_context", {})
    
    print(f"Assistant Response: {last_msg_2}")
    print(f"Extracted Context: {context_2}")
    
    assert context_2.get("origin") == "Delhi", "Failed: Origin should be Delhi"
    assert context_2.get("destination") == "Shimla", "Failed: Destination should be Shimla"
    assert context_2.get("num_days") is None, "Failed: Duration should be None"
    assert "duration" in last_msg_2.lower() or "number of days" in last_msg_2.lower() or "how many days" in last_msg_2.lower(), "Failed: Did not ask for duration"
    print("-> TEST 2 PASSED: Correctly extracted origin and destination, and asked for trip duration.")

    # ============================================================
    # Test 3: 5 days -> Uses remembered Delhi + Shimla.
    # ============================================================
    print("\n[TEST 3] User prompt: '5 days' (Same session)")
    inputs_3 = {
        "messages": [("user", "5 days")],
        "user_id": "test_user",
        "context_injected": False
    }
    
    # Run in the same session_2 to test memory persistence
    res_3 = await agent.ainvoke(inputs_3, config_2)
    last_msg_3 = res_3["messages"][-1].content
    context_3 = res_3.get("trip_context", {})
    
    print(f"Assistant Response: {last_msg_3}")
    print(f"Extracted Context: {context_3}")
    
    assert context_3.get("origin") == "Delhi", "Failed: Origin memory lost"
    assert context_3.get("destination") == "Shimla", "Failed: Destination memory lost"
    assert int(context_3.get("num_days")) == 5, "Failed: Duration was not set to 5"
    print("-> TEST 3 PASSED: Correctly remembered Delhi + Shimla from prior turn and set days to 5.")

    # ============================================================
    # Test 4: Actually make it Manali -> Context updated.
    # ============================================================
    print("\n[TEST 4] User prompt: 'Actually make it Manali'")
    inputs_4 = {
        "messages": [("user", "Actually make it Manali")],
        "user_id": "test_user",
        "context_injected": False
    }
    
    # Run in the same session_2 to test overriding existing memory
    res_4 = await agent.ainvoke(inputs_4, config_2)
    last_msg_4 = res_4["messages"][-1].content
    context_4 = res_4.get("trip_context", {})
    
    print(f"Assistant Response: {last_msg_4}")
    print(f"Extracted Context: {context_4}")
    
    assert context_4.get("destination") == "Manali", "Failed: Destination did not update to Manali"
    assert context_4.get("origin") == "Delhi", "Failed: Origin was lost during override"
    assert int(context_4.get("num_days")) == 5, "Failed: Duration was lost during override"
    print("-> TEST 4 PASSED: Correctly updated destination to Manali while preserving other context parameters.")

    # ============================================================
    # Test 5: New chat session -> No memory leakage.
    # ============================================================
    print("\n[TEST 5] New session verification (Verify no leakage)")
    session_5 = f"test-session-{uuid.uuid4()}"
    config_5 = {"configurable": {"thread_id": session_5}}
    
    # Query state in a new clean session
    state_5 = await agent.aget_state(config_5)
    context_5 = state_5.values.get("trip_context", {}) if state_5 else {}
    
    print(f"New Session Context: {context_5}")
    assert not context_5, "Failed: New session should have empty context, but found data"
    print("-> TEST 5 PASSED: Session isolated. No Delhi/Shimla context leakage detected.")

    print("\n==================================================")
    print("ALL 5 REGRESSION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
