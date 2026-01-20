"""
Vital Trend Analyzer Agent
Detects deteriorating patients by analyzing vital sign trends
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('health.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_vital_history(patient_id: int, vital_type: str, days: int = 7) -> List[Dict]:
    """
    Fetch vital readings for a patient over specified days
    
    Args:
        patient_id: Patient ID
        vital_type: Type of vital (BP, SUGAR, TEMP)
        days: Number of days to look back
        
    Returns:
        List of vital readings with timestamps
    """
    conn = get_db_connection()
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        readings = conn.execute("""
            SELECT value1, value2, timestamp
            FROM readings
            WHERE patient_id = ? AND reading_type = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (patient_id, vital_type, cutoff_date.isoformat())).fetchall()
        
        return [dict(r) for r in readings]
    finally:
        conn.close()

def detect_trend(readings: List[Dict], vital_type: str) -> Dict:
    """
    Analyze trend in vital readings
    
    Args:
        readings: List of vital readings
        vital_type: Type of vital
        
    Returns:
        Trend analysis with direction and severity
    """
    if len(readings) < 2:
        return {"trend": "INSUFFICIENT_DATA", "severity": "NONE"}
    
    if vital_type == "BP":
        # Analyze systolic BP (value1)
        values = [r['value1'] for r in readings]
        first_val = values[0]
        last_val = values[-1]
        change = last_val - first_val
        
        # Detect trend
        if change >= 20:
            severity = "HIGH" if change >= 30 else "MODERATE"
            return {
                "trend": "RISING",
                "severity": severity,
                "change": change,
                "first_value": f"{readings[0]['value1']}/{readings[0]['value2']}",
                "last_value": f"{readings[-1]['value1']}/{readings[-1]['value2']}",
                "days": len(readings)
            }
        elif change <= -20:
            return {
                "trend": "FALLING",
                "severity": "MODERATE",
                "change": abs(change),
                "first_value": f"{readings[0]['value1']}/{readings[0]['value2']}",
                "last_value": f"{readings[-1]['value1']}/{readings[-1]['value2']}",
                "days": len(readings)
            }
        else:
            return {"trend": "STABLE", "severity": "NONE"}
    
    elif vital_type == "SUGAR":
        values = [r['value1'] for r in readings]
        first_val = values[0]
        last_val = values[-1]
        change = last_val - first_val
        
        if change >= 50:
            severity = "HIGH" if change >= 80 else "MODERATE"
            return {
                "trend": "RISING",
                "severity": severity,
                "change": change,
                "first_value": readings[0]['value1'],
                "last_value": readings[-1]['value1'],
                "days": len(readings)
            }
        elif change <= -50:
            return {
                "trend": "FALLING",
                "severity": "MODERATE",
                "change": abs(change),
                "first_value": readings[0]['value1'],
                "last_value": readings[-1]['value1'],
                "days": len(readings)
            }
        else:
            return {"trend": "STABLE", "severity": "NONE"}
    
    return {"trend": "UNKNOWN", "severity": "NONE"}

def generate_alert(patient_id: int, vital_type: str, trend_data: Dict) -> Optional[int]:
    """
    Create alert entry in database
    
    Args:
        patient_id: Patient ID
        vital_type: Type of vital
        trend_data: Trend analysis data
        
    Returns:
        Alert ID if created, None otherwise
    """
    if trend_data["severity"] == "NONE":
        return None
    
    conn = get_db_connection()
    try:
        # Check if similar alert already exists (within last 24 hours)
        existing = conn.execute("""
            SELECT id FROM patient_alerts
            WHERE patient_id = ? AND vital_name = ? 
            AND is_acknowledged = 0
            AND created_at >= datetime('now', '-1 day')
        """, (patient_id, vital_type)).fetchone()
        
        if existing:
            return None  # Don't create duplicate alert
        
        # Generate alert message
        if vital_type == "BP":
            message = f"Blood pressure {trend_data['trend'].lower()} trend detected ({trend_data['change']} points in {trend_data['days']} days)"
        elif vital_type == "SUGAR":
            message = f"Blood sugar {trend_data['trend'].lower()} trend detected ({trend_data['change']} mg/dL in {trend_data['days']} days)"
        else:
            message = f"{vital_type} {trend_data['trend'].lower()} trend detected"
        
        # Insert alert
        cursor = conn.execute("""
            INSERT INTO patient_alerts 
            (patient_id, alert_type, severity, message, vital_name, trend_data)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            "VITAL_TREND_WORSENING" if trend_data["trend"] == "RISING" else "VITAL_TREND_IMPROVING",
            trend_data["severity"],
            message,
            vital_type,
            json.dumps(trend_data)
        ))
        
        conn.commit()
        alert_id = cursor.lastrowid
        
        # Log agent execution
        log_agent_execution(patient_id, "vital_trend_analyzer", {
            "vital_type": vital_type,
            "readings_analyzed": trend_data.get("days", 0)
        }, {
            "alert_created": True,
            "alert_id": alert_id,
            "severity": trend_data["severity"]
        })
        
        return alert_id
    finally:
        conn.close()

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

def analyze_vital_trends(patient_id: int) -> Dict:
    """
    Main function: Analyze all vital trends for a patient
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Analysis results with alerts created
    """
    start_time = datetime.now()
    results = {
        "patient_id": patient_id,
        "analyzed_vitals": [],
        "alerts_created": []
    }
    
    # Analyze BP trends
    bp_readings = get_vital_history(patient_id, "BP", days=7)
    if bp_readings:
        bp_trend = detect_trend(bp_readings, "BP")
        results["analyzed_vitals"].append({
            "vital_type": "BP",
            "readings_count": len(bp_readings),
            "trend": bp_trend
        })
        
        alert_id = generate_alert(patient_id, "BP", bp_trend)
        if alert_id:
            results["alerts_created"].append({
                "alert_id": alert_id,
                "vital_type": "BP",
                "severity": bp_trend["severity"]
            })
    
    # Analyze Sugar trends
    sugar_readings = get_vital_history(patient_id, "SUGAR", days=7)
    if sugar_readings:
        sugar_trend = detect_trend(sugar_readings, "SUGAR")
        results["analyzed_vitals"].append({
            "vital_type": "SUGAR",
            "readings_count": len(sugar_readings),
            "trend": sugar_trend
        })
        
        alert_id = generate_alert(patient_id, "SUGAR", sugar_trend)
        if alert_id:
            results["alerts_created"].append({
                "alert_id": alert_id,
                "vital_type": "SUGAR",
                "severity": sugar_trend["severity"]
            })
    
    # Calculate execution time
    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
    
    # Log overall execution
    log_agent_execution(patient_id, "vital_trend_analyzer", {
        "analysis_type": "full_vital_scan"
    }, results, execution_time)
    
    return results

def analyze_all_patients() -> Dict:
    """
    Analyze vital trends for all patients with recent readings
    
    Returns:
        Summary of analysis across all patients
    """
    conn = get_db_connection()
    try:
        # Get all patients with readings in last 7 days
        patients = conn.execute("""
            SELECT DISTINCT patient_id
            FROM readings
            WHERE timestamp >= datetime('now', '-7 days')
        """).fetchall()
        
        summary = {
            "total_patients_analyzed": 0,
            "total_alerts_created": 0,
            "high_severity_alerts": 0,
            "patients_with_alerts": []
        }
        
        for patient in patients:
            patient_id = patient['patient_id']
            results = analyze_vital_trends(patient_id)
            summary["total_patients_analyzed"] += 1
            
            if results["alerts_created"]:
                summary["total_alerts_created"] += len(results["alerts_created"])
                summary["patients_with_alerts"].append(patient_id)
                
                for alert in results["alerts_created"]:
                    if alert["severity"] == "HIGH":
                        summary["high_severity_alerts"] += 1
        
        return summary
    finally:
        conn.close()

if __name__ == "__main__":
    # Test the agent
    print("Running Vital Trend Analyzer...")
    summary = analyze_all_patients()
    print(f"✅ Analyzed {summary['total_patients_analyzed']} patients")
    print(f"✅ Created {summary['total_alerts_created']} alerts")
    print(f"⚠️  {summary['high_severity_alerts']} high severity alerts")
