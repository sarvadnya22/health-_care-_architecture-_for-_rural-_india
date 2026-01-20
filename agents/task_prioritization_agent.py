"""
ASHA Task Prioritization Agent
Organizes ASHA worker's daily workload by urgency
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('health.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_urgency_score(patient_data: Dict) -> int:
    """
    Calculate urgency score (0-100) for a patient
    
    Scoring factors:
    - High severity alert: +50
    - Moderate severity alert: +30
    - Overdue follow-up: +20
    - Recent high vitals: +15
    - Pending triage report: +10
    
    Args:
        patient_data: Patient information with alerts and vitals
        
    Returns:
        Urgency score (0-100)
    """
    score = 0
    
    # Check for alerts
    if patient_data.get('alerts'):
        for alert in patient_data['alerts']:
            if alert['severity'] == 'HIGH':
                score += 50
            elif alert['severity'] == 'MODERATE':
                score += 30
    
    # Check for overdue follow-ups
    if patient_data.get('overdue_followup'):
        days_overdue = patient_data['overdue_followup']['days']
        score += min(20 + (days_overdue * 5), 40)  # Cap at 40
    
    # Check latest vitals
    if patient_data.get('latest_vitals'):
        vitals = patient_data['latest_vitals']
        if vitals.get('bp_systolic', 0) >= 160 or vitals.get('sugar', 0) >= 250:
            score += 15
    
    # Check for pending triage
    if patient_data.get('needs_triage'):
        score += 10
    
    return min(score, 100)  # Cap at 100

def get_patient_alerts(patient_id: int) -> List[Dict]:
    """Get unacknowledged alerts for patient"""
    conn = get_db_connection()
    try:
        alerts = conn.execute("""
            SELECT id, alert_type, severity, message, vital_name, created_at
            FROM patient_alerts
            WHERE patient_id = ? AND is_acknowledged = 0
            ORDER BY severity DESC, created_at DESC
        """, (patient_id,)).fetchall()
        return [dict(a) for a in alerts]
    finally:
        conn.close()

def get_overdue_followup(patient_id: int) -> Dict:
    """Check if patient has overdue follow-up"""
    conn = get_db_connection()
    try:
        overdue = conn.execute("""
            SELECT id, scheduled_date, visit_type, priority
            FROM follow_up_schedule
            WHERE patient_id = ? AND status = 'PENDING' 
            AND scheduled_date < DATE('now')
            ORDER BY scheduled_date ASC
            LIMIT 1
        """, (patient_id,)).fetchone()
        
        if overdue:
            scheduled_date = datetime.strptime(overdue['scheduled_date'], '%Y-%m-%d')
            days_overdue = (datetime.now() - scheduled_date).days
            return {
                "id": overdue['id'],
                "scheduled_date": overdue['scheduled_date'],
                "visit_type": overdue['visit_type'],
                "days": days_overdue
            }
        return None
    finally:
        conn.close()

def get_latest_vitals(patient_id: int) -> Dict:
    """Get latest vital readings"""
    conn = get_db_connection()
    try:
        bp = conn.execute("""
            SELECT value1, value2 FROM readings
            WHERE patient_id = ? AND reading_type = 'BP'
            ORDER BY timestamp DESC LIMIT 1
        """, (patient_id,)).fetchone()
        
        sugar = conn.execute("""
            SELECT value1 FROM readings
            WHERE patient_id = ? AND reading_type = 'SUGAR'
            ORDER BY timestamp DESC LIMIT 1
        """, (patient_id,)).fetchone()
        
        return {
            "bp_systolic": bp['value1'] if bp else None,
            "bp_diastolic": bp['value2'] if bp else None,
            "sugar": sugar['value1'] if sugar else None
        }
    finally:
        conn.close()

def prioritize_patients(asha_worker_phone: str) -> List[Dict]:
    """
    Get prioritized list of patients for ASHA worker
    
    Args:
        asha_worker_phone: ASHA worker's phone number
        
    Returns:
        Sorted list of patients with urgency scores
    """
    conn = get_db_connection()
    try:
        # Get all patients assigned to this ASHA worker
        patients = conn.execute("""
            SELECT id, name, phone_number, age, gender, village
            FROM patients
            WHERE asha_worker_phone = ?
            ORDER BY name
        """, (asha_worker_phone,)).fetchall()
        
        prioritized_list = []
        
        for patient in patients:
            patient_id = patient['id']
            
            # Gather patient data
            patient_data = {
                "id": patient_id,
                "name": patient['name'],
                "phone_number": patient['phone_number'],
                "age": patient['age'],
                "gender": patient['gender'],
                "village": patient['village'],
                "alerts": get_patient_alerts(patient_id),
                "overdue_followup": get_overdue_followup(patient_id),
                "latest_vitals": get_latest_vitals(patient_id)
            }
            
            # Calculate urgency score
            urgency_score = calculate_urgency_score(patient_data)
            
            # Add to list if score > 0 (needs attention)
            if urgency_score > 0:
                prioritized_list.append({
                    "patient": patient_data,
                    "urgency_score": urgency_score,
                    "priority_level": "HIGH" if urgency_score >= 50 else "MODERATE" if urgency_score >= 30 else "LOW"
                })
        
        # Sort by urgency score (descending)
        prioritized_list.sort(key=lambda x: x['urgency_score'], reverse=True)
        
        return prioritized_list
    finally:
        conn.close()

def suggest_visit_route(patient_list: List[Dict]) -> Dict:
    """
    Suggest optimal visit route (simple version)
    
    Args:
        patient_list: Prioritized patient list
        
    Returns:
        Route suggestion with estimated time
    """
    # Simple implementation: visit by priority order
    # Future: integrate Google Maps API for distance-based routing
    
    route = {
        "total_patients": len(patient_list),
        "estimated_time_hours": len(patient_list) * 0.5,  # 30 min per patient
        "visit_order": []
    }
    
    for idx, item in enumerate(patient_list, 1):
        route["visit_order"].append({
            "sequence": idx,
            "patient_name": item['patient']['name'],
            "village": item['patient']['village'],
            "priority": item['priority_level'],
            "reason": get_visit_reason(item)
        })
    
    return route

def get_visit_reason(patient_item: Dict) -> str:
    """Generate human-readable visit reason"""
    patient = patient_item['patient']
    reasons = []
    
    if patient['alerts']:
        alert = patient['alerts'][0]  # Most severe alert
        reasons.append(alert['message'])
    
    if patient['overdue_followup']:
        followup = patient['overdue_followup']
        reasons.append(f"Follow-up overdue by {followup['days']} days")
    
    if patient['latest_vitals']:
        vitals = patient['latest_vitals']
        if vitals.get('bp_systolic', 0) >= 160:
            reasons.append(f"High BP: {vitals['bp_systolic']}/{vitals['bp_diastolic']}")
        if vitals.get('sugar', 0) >= 250:
            reasons.append(f"High Sugar: {vitals['sugar']} mg/dL")
    
    return " | ".join(reasons) if reasons else "Routine check"

def generate_daily_task_list(asha_worker_phone: str) -> Dict:
    """
    Generate complete daily task list for ASHA worker
    
    Args:
        asha_worker_phone: ASHA worker's phone number
        
    Returns:
        Complete task list with priorities and route
    """
    start_time = datetime.now()
    
    # Get prioritized patients
    prioritized_patients = prioritize_patients(asha_worker_phone)
    
    # Suggest route
    route = suggest_visit_route(prioritized_patients)
    
    # Generate summary
    summary = {
        "generated_at": datetime.now().isoformat(),
        "asha_worker": asha_worker_phone,
        "total_patients": len(prioritized_patients),
        "high_priority": sum(1 for p in prioritized_patients if p['priority_level'] == 'HIGH'),
        "moderate_priority": sum(1 for p in prioritized_patients if p['priority_level'] == 'MODERATE'),
        "low_priority": sum(1 for p in prioritized_patients if p['priority_level'] == 'LOW'),
        "patients": prioritized_patients,
        "suggested_route": route
    }
    
    # Log agent execution
    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
    log_agent_execution(asha_worker_phone, "task_prioritization_agent", {
        "asha_worker": asha_worker_phone
    }, {
        "patients_analyzed": len(prioritized_patients),
        "high_priority_count": summary['high_priority']
    }, execution_time)
    
    return summary

def log_agent_execution(identifier: str, agent_name: str, input_data: Dict, output_data: Dict, execution_time_ms: int = 0):
    """Log agent execution to database"""
    conn = get_db_connection()
    try:
        # Use patient_id = 0 for ASHA-level operations
        conn.execute("""
            INSERT INTO agent_logs (patient_id, agent_name, input_data, output_data, execution_time_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (0, agent_name, json.dumps(input_data), json.dumps(output_data), execution_time_ms))
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    # Test the agent
    print("Running ASHA Task Prioritization Agent...")
    task_list = generate_daily_task_list("+919123456789")
    print(f"✅ Total patients: {task_list['total_patients']}")
    print(f"🔴 High priority: {task_list['high_priority']}")
    print(f"🟡 Moderate priority: {task_list['moderate_priority']}")
    print(f"🟢 Low priority: {task_list['low_priority']}")
