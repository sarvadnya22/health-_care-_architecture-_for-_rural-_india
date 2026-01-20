def asha_task_agent(state: dict) -> dict:
    print(" ASHA TASK AGENT EXECUTED")

    decision = state.get("decision", "").strip().lower()

    if decision == "emergency":
        task = (
            "Immediately escort patient to nearest government hospital "
            "and coordinate ambulance services."
        )
        priority = "HIGH"

    elif decision == "asha follow-up":
        task = (
            "Visit patient within 24–48 hours, recheck vitals, "
            "and monitor symptoms."
        )
        priority = "MEDIUM"

    elif decision == "home care":
        task = (
            "Educate patient on home care, ensure hydration, "
            "and follow up after 3 days."
        )
        priority = "LOW"

    else:
        task = "Follow up with patient as per standard protocol."
        priority = "MEDIUM"

    return {
        "asha_task": task,
        "task_priority": priority
    }
