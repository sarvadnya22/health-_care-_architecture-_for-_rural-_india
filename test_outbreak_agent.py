"""
Test Script: Outbreak Monitor Agent
Simulates triage submissions to trigger the autonomous outbreak detection
"""
import sqlite3
import sys
sys.path.insert(0, '.')

from agents.orchestrator import orchestrator

def get_db_connection():
    conn = sqlite3.connect('health.db')
    conn.row_factory = sqlite3.Row
    return conn

def seed_triage_reports_for_village(village_name, patient_ids, count=3):
    """Seed triage reports to trigger outbreak detection"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing Outbreak Agent for Village: {village_name}")
    print(f"{'='*60}")
    
    # Check current count (using timestamp column)
    cursor.execute("""
        SELECT count(*) FROM triage_reports 
        WHERE timestamp >= date('now', '-7 days') 
        AND patient_id IN (SELECT id FROM patients WHERE village = ?)
    """, (village_name,))
    current_count = cursor.fetchone()[0]
    print(f"📊 Current triage reports in {village_name} (last 7 days): {current_count}")
    
    # Check existing advisories
    cursor.execute("SELECT count(*) FROM ministry_advisories WHERE village = ?", (village_name,))
    existing_advisories = cursor.fetchone()[0]
    print(f"📋 Existing advisories for {village_name}: {existing_advisories}")
    
    # Clear recent advisories to allow re-testing
    cursor.execute("DELETE FROM ministry_advisories WHERE village = ?", (village_name,))
    conn.commit()
    print(f"🗑️  Cleared advisories for fresh test")
    
    # Seed triage reports
    print(f"\n📥 Seeding {count} triage reports...")
    for i, patient_id in enumerate(patient_ids[:count]):
        cursor.execute("""
            INSERT INTO triage_reports (patient_id, chief_complaint, symptoms, notes, ai_prediction, timestamp)
            VALUES (?, 'High fever outbreak test', 'fever, cough, cold', 'Test report for outbreak detection', 
                    '<b>Risk:</b> High<br><b>Decision:</b> Doctor Consultation', datetime('now'))
        """, (patient_id,))
        print(f"   ✅ Report {i+1}: Patient ID {patient_id}")
    
    conn.commit()
    
    # Now verify new count
    cursor.execute("""
        SELECT count(*) FROM triage_reports 
        WHERE timestamp >= date('now', '-7 days') 
        AND patient_id IN (SELECT id FROM patients WHERE village = ?)
    """, (village_name,))
    new_count = cursor.fetchone()[0]
    print(f"\n📊 New count of triage reports: {new_count}")
    
    conn.close()
    
    # Now trigger the orchestrator's outbreak detection
    print(f"\n🤖 Triggering Outbreak Detection Agent...")
    alert = orchestrator.detect_outbreak_patterns(village_name, "Doctor Consultation")
    
    if alert:
        print(f"\n🚨 AGENT ALERT TRIGGERED!")
        print(f"   Type: {alert.get('type')}")
        print(f"   Message: {alert.get('message')}")
        
        # Verify advisory was created
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ministry_advisories WHERE village = ? ORDER BY id DESC LIMIT 1", (village_name,))
        advisory = cursor.fetchone()
        if advisory:
            print(f"\n✅ AUTONOMOUS ADVISORY CREATED:")
            print(f"   ID: {advisory['id']}")
            print(f"   District: {advisory['district']}")
            print(f"   Village: {advisory['village']}")
            print(f"   Message: {advisory['message']}")
        conn.close()
    else:
        print(f"\n⚠️  No alert triggered. Threshold may not be met or advisory already exists.")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    # Get patients for Rukmini Devi (Udane village)
    conn = get_db_connection()
    
    # First, let's standardize the village name
    conn.execute("UPDATE patients SET village = 'Udane' WHERE LOWER(village) = 'udane'")
    conn.commit()
    
    # Get patient IDs for Udane
    patients = conn.execute("SELECT id FROM patients WHERE village = 'Udane'").fetchall()
    patient_ids = [p['id'] for p in patients]
    
    print(f"Found {len(patient_ids)} patients in Udane: {patient_ids}")
    
    conn.close()
    
    if len(patient_ids) >= 3:
        seed_triage_reports_for_village("Udane", patient_ids, count=3)
    else:
        print("Not enough patients in Udane village. Adding some...")
        conn = get_db_connection()
        patients = conn.execute("SELECT id FROM patients LIMIT 3").fetchall()
        patient_ids = [p['id'] for p in patients]
        conn.close()
        seed_triage_reports_for_village("Udane", patient_ids, count=3)
