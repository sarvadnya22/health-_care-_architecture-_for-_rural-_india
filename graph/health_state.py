from typing import TypedDict, List, Optional

class HealthState(TypedDict):
    patient_id: int
    age: int
    chief_complaint: str
    symptoms: List[str]
    notes: str
    
    # NEW: Critical Vitals from readings table
    latest_bp: Optional[str]
    latest_sugar: Optional[str]

    # NEW: Inventory Check Tool Output
    medication_stock_status: Optional[str] 

    # Agent outputs
    risk: str
    decision: str
    reasoning: str