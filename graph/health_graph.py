from langgraph.graph import StateGraph, END
from graph.health_state import HealthState
from graph.nodes import triage_node, asha_task_node, inventory_check_node

def verify_and_route(state):
    # This routing function checks the decision from the Triage Agent
    decision = state["decision"].strip().lower()
    
    if decision == "emergency":
        return "end_process" # Immediate end, needs human override
    elif decision == "home care":
        return "end_process" # Simple case, no further checks needed
    elif decision == "asha follow-up":
        # This decision implies the ASHA worker might prescribe/refer—needs inventory check
        return "inventory_check"
    else:
        return "asha_task" # Default path

def build_health_graph():
    graph = StateGraph(HealthState)

    graph.add_node("triage", triage_node)
    graph.add_node("inventory_check", inventory_check_node)
    graph.add_node("asha_task", asha_task_node)

    # 1. Triage always runs first
    graph.set_entry_point("triage")
    
    # 2. Triage output determines next step
    graph.add_conditional_edges(
        "triage",
        verify_and_route,
        {
            "inventory_check": "inventory_check",
            "end_process": END,
            "asha_task": "asha_task",
        },
    )

    # 3. After inventory check, go to ASHA task and finish
    graph.add_edge("inventory_check", "asha_task")
    
    # 4. ASHA task is the final step
    graph.add_edge("asha_task", END)

    return graph.compile()

# 🔥 IMPORTANT: compile at import time
health_graph = build_health_graph()