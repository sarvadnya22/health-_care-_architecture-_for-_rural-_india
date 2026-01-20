from datetime import datetime, timedelta

def followup_agent(workflow: dict) -> dict:
    current_state = workflow["current_state"]
    created_at = datetime.fromisoformat(workflow["created_at"])

    now = datetime.now()
    elapsed_hours = (now - created_at).total_seconds() / 3600

    # Default
    next_action = workflow["next_action"]
    new_state = current_state

    if current_state == "monitoring" and elapsed_hours >= 72:
        new_state = "closed"
        next_action = "Case closed – symptoms stable"

    elif current_state == "awaiting_followup":
        if elapsed_hours >= 48:
            new_state = "escalated"
            next_action = "Escalate case – follow-up missed"
        elif elapsed_hours >= 24:
            next_action = "Reminder: ASHA follow-up visit due"

    return {
        "new_state": new_state,
        "next_action": next_action
    }
