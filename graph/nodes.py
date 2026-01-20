from agents.triage_agent import triage_agent, check_critical_vitals
from agents.asha_task_agent import asha_task_agent
import sqlite3

def get_db_connection():
    # Use the application's connection logic
    conn = sqlite3.connect('health.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def triage_node(state: dict) -> dict:
    # Check Vitals and pass to Triage Agent
    vitals = check_critical_vitals(state["patient_id"]) 
    
    # Pass the full state (including vitals) to the LLM agent
    result = triage_agent(state) 
    
    state.update({
        "risk": result["risk"],
        "decision": result["decision"],
        "reasoning": result["reasoning"],
        "latest_bp": vitals["latest_bp"],
        "latest_sugar": vitals["latest_sugar"],
        # New State update
        "medication_stock_status": None 
    })
    return state

def inventory_check_node(state: dict) -> dict:
    conn = get_db_connection()
    try:
        # Simplified Check: Always look for a common prescription (e.g., Paracetamol)
        # In a real app, this would use a predicted medication from the Triage Agent.
        medication_to_check = "Paracetamol"
        
        stock = conn.execute(
            "SELECT stock_status FROM pharmacy_inventory WHERE medication = ? AND stock_status = 'In Stock' LIMIT 1",
            (medication_to_check,)
        ).fetchone()
        
        if not stock:
            # If nothing is 'In Stock', check if it's 'Low Stock'
            low_stock = conn.execute(
                "SELECT stock_status FROM pharmacy_inventory WHERE medication = ? AND stock_status = 'Low Stock' LIMIT 1",
                (medication_to_check,)
            ).fetchone()
            
            if low_stock:
                status_msg = f"WARNING: {medication_to_check} is LOW stock in the district."
            else:
                status_msg = f"CRITICAL: {medication_to_check} is OUT OF STOCK in local pharmacies."
                # We can even escalate the decision if medicine is out of stock!
                state["decision"] = "Emergency" # Force escalation
        else:
            status_msg = f"OK: {medication_to_check} is IN STOCK locally."

    except Exception as e:
        status_msg = f"Inventory Check Failed: {e}"
        print(status_msg)
    finally:
        conn.close()

    state["medication_stock_status"] = status_msg
    
    # Rerun the ASHA task agent to incorporate the new stock information into the final task
    state = asha_task_node(state)
    return state
    
def asha_task_node(state: dict) -> dict:
    # If the decision was escalated due to stock, the ASHA task agent must know.
    # It also gets the medication status to include in the task.
    result = asha_task_agent(state) 
    
    # Append stock status to the ASHA task for immediate awareness
    if state.get("medication_stock_status"):
        result["asha_task"] += f" | NOTE: Inventory Check: {state['medication_stock_status']}"
        
    state["asha_task"] = result["asha_task"]
    state["task_priority"] = result["task_priority"]
    return state