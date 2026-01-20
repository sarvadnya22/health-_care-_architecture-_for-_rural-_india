"""
Doctor Case Preparation Agent
Auto-generates comprehensive case summaries for doctor review
"""
import sqlite3
import json
import os
import requests
from datetime import datetime
from typing import Dict, List

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('health.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_patient_info(patient_id: int) -> Dict:
    """Get basic patient information"""
    conn = get_db_connection()
    try:
        patient = conn.execute("""
            SELECT id, name, phone_number, age, gender, village, asha_worker_phone
            FROM patients WHERE id = ?
        """, (patient_id,)).fetchone()
        return dict(patient) if patient else None
    finally:
        conn.close()

def get_patient_timeline(patient_id: int) -> List[Dict]:
    """Get chronological timeline of all patient events"""
    conn = get_db_connection()
    try:
        events = []
        
        # Get vital readings
        vitals = conn.execute("""
            SELECT reading_type, value1, value2, timestamp
            FROM readings WHERE patient_id = ?
            ORDER BY timestamp DESC LIMIT 10
        """, (patient_id,)).fetchall()
        
        for vital in vitals:
            if vital['reading_type'] == 'BP':
                value_str = f"{vital['value1']}/{vital['value2']}"
            else:
                value_str = str(vital['value1'])
            
            events.append({
                "type": "vital",
                "timestamp": vital['timestamp'],
                "description": f"{vital['reading_type']}: {value_str}"
            })
        
        # Get triage reports
        reports = conn.execute("""
            SELECT chief_complaint, symptoms, ai_prediction, timestamp
            FROM triage_reports WHERE patient_id = ?
            ORDER BY timestamp DESC LIMIT 5
        """, (patient_id,)).fetchall()
        
        for report in reports:
            events.append({
                "type": "triage",
                "timestamp": report['timestamp'],
                "description": f"Triage: {report['chief_complaint']}"
            })
        
        # Get prescriptions
        prescriptions = conn.execute("""
            SELECT medication_name, dosage, timestamp
            FROM prescriptions WHERE patient_id = ?
            ORDER BY timestamp DESC LIMIT 5
        """, (patient_id,)).fetchall()
        
        for rx in prescriptions:
            events.append({
                "type": "prescription",
                "timestamp": rx['timestamp'],
                "description": f"Prescribed: {rx['medication_name']} {rx['dosage']}"
            })
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return events
    finally:
        conn.close()

def get_latest_triage(patient_id: int) -> Dict:
    """Get most recent triage report"""
    conn = get_db_connection()
    try:
        triage = conn.execute("""
            SELECT chief_complaint, symptoms, notes, ai_prediction, timestamp
            FROM triage_reports WHERE patient_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (patient_id,)).fetchone()
        return dict(triage) if triage else None
    finally:
        conn.close()

def get_active_prescriptions(patient_id: int) -> List[Dict]:
    """Get active prescriptions"""
    conn = get_db_connection()
    try:
        prescriptions = conn.execute("""
            SELECT medication_name, dosage, notes, timestamp
            FROM prescriptions WHERE patient_id = ? AND is_active = 1
            ORDER BY timestamp DESC
        """, (patient_id,)).fetchall()
        return [dict(p) for p in prescriptions]
    finally:
        conn.close()

def get_patient_alerts(patient_id: int) -> List[Dict]:
    """Get recent alerts"""
    conn = get_db_connection()
    try:
        alerts = conn.execute("""
            SELECT alert_type, severity, message, vital_name, created_at
            FROM patient_alerts WHERE patient_id = ?
            ORDER BY created_at DESC LIMIT 5
        """, (patient_id,)).fetchall()
        return [dict(a) for a in alerts]
    finally:
        conn.close()

def format_with_llm(raw_data: Dict) -> str:
    """
    Use LLM to format case summary in readable markdown
    
    Args:
        raw_data: Raw patient data
        
    Returns:
        Formatted markdown case summary
    """
    if not OPENROUTER_API_KEY:
        return generate_basic_summary(raw_data)
    
    prompt = f"""
You are a medical case summary assistant. Format the following patient data into a clear, concise case summary for a doctor.

Patient: {raw_data['patient']['name']}, {raw_data['patient']['age']}Y, {raw_data['patient']['gender']}
Village: {raw_data['patient']['village']}

Latest Triage:
{json.dumps(raw_data.get('latest_triage'), indent=2)}

Recent Vitals Timeline:
{json.dumps(raw_data.get('timeline')[:5], indent=2)}

Active Medications:
{json.dumps(raw_data.get('prescriptions'), indent=2)}

Alerts:
{json.dumps(raw_data.get('alerts'), indent=2)}

Format as markdown with sections:
1. Patient Overview
2. Current Presentation
3. Recent Timeline (last 5 events)
4. Active Medications
5. AI Assessment
6. Recommended Actions

Keep it concise and clinical. Use bullet points.
"""
    
    try:
        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        content = response.json()["choices"][0]["message"]["content"]
        return content
    except Exception as e:
        print(f"LLM formatting failed: {e}")
        return generate_basic_summary(raw_data)

def generate_basic_summary(raw_data: Dict) -> str:
    """Generate basic markdown summary without LLM"""
    patient = raw_data['patient']
    triage = raw_data.get('latest_triage', {})
    timeline = raw_data.get('timeline', [])
    prescriptions = raw_data.get('prescriptions', [])
    alerts = raw_data.get('alerts', [])
    
    summary = f"""# CASE SUMMARY - URGENT REVIEW NEEDED

## Patient Overview
- **Name:** {patient['name']}
- **Age/Gender:** {patient['age']}Y / {patient['gender']}
- **Village:** {patient['village']}
- **ASHA Worker:** {patient['asha_worker_phone']}

## Current Presentation
- **Chief Complaint:** {triage.get('chief_complaint', 'N/A')}
- **Symptoms:** {triage.get('symptoms', 'N/A')}
- **Notes:** {triage.get('notes', 'N/A')}

## Recent Timeline
"""
    
    for event in timeline[:5]:
        summary += f"- **{event['timestamp'][:10]}:** {event['description']}\n"
    
    summary += "\n## Active Medications\n"
    if prescriptions:
        for rx in prescriptions:
            summary += f"- {rx['medication_name']} {rx['dosage']}\n"
    else:
        summary += "- None\n"
    
    summary += "\n## AI Assessment\n"
    if triage.get('ai_prediction'):
        summary += f"{triage['ai_prediction']}\n"
    else:
        summary += "- No AI assessment available\n"
    
    summary += "\n## Alerts\n"
    if alerts:
        for alert in alerts:
            emoji = "🔴" if alert['severity'] == 'HIGH' else "🟡"
            summary += f"{emoji} **{alert['severity']}:** {alert['message']}\n"
    else:
        summary += "- No active alerts\n"
    
    summary += "\n## Recommended Actions\n"
    summary += "☐ Review current medications\n"
    summary += "☐ Assess vital trends\n"
    summary += "☐ Consider treatment adjustment\n"
    summary += "☐ Schedule follow-up\n"
    
    return summary

def prepare_case_summary(patient_id: int, use_llm: bool = True) -> str:
    """
    Main function: Generate comprehensive case summary
    
    Args:
        patient_id: Patient ID
        use_llm: Whether to use LLM for formatting
        
    Returns:
        Markdown-formatted case summary
    """
    start_time = datetime.now()
    
    # Gather all patient data
    raw_data = {
        "patient": get_patient_info(patient_id),
        "timeline": get_patient_timeline(patient_id),
        "latest_triage": get_latest_triage(patient_id),
        "prescriptions": get_active_prescriptions(patient_id),
        "alerts": get_patient_alerts(patient_id)
    }
    
    # Format summary
    if use_llm:
        summary = format_with_llm(raw_data)
    else:
        summary = generate_basic_summary(raw_data)
    
    # Log agent execution
    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
    log_agent_execution(patient_id, "doctor_case_prep_agent", {
        "use_llm": use_llm
    }, {
        "summary_length": len(summary),
        "sections_included": ["overview", "presentation", "timeline", "medications", "assessment", "recommendations"]
    }, execution_time)
    
    return summary

def log_agent_execution(patient_id: int, agent_name: str, input_data: Dict, output_data: Dict, execution_time_ms: int = 0):
    """Log agent execution to database"""
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO agent_logs (patient_id, agent_name, input_data, output_data, execution_time_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, agent_name, json.dumps(input_data), json.dumps(output_data), execution_time_ms))
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    # Test the agent
    print("Running Doctor Case Preparation Agent...")
    summary = prepare_case_summary(1, use_llm=False)
    print(summary)
