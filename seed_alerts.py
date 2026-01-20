import sqlite3

conn = sqlite3.connect('health.db')
conn.row_factory = sqlite3.Row

# Find patients assigned to this ASHA worker
patients = conn.execute("""
    SELECT id, name FROM patients 
    WHERE asha_worker_phone = '+919834358534' 
    LIMIT 2
""").fetchall()

if len(patients) < 2:
    print("Not enough patients assigned to this ASHA worker. Assigning some...")
    # Get any 2 patients and assign them
    all_patients = conn.execute("SELECT id, name FROM patients LIMIT 2").fetchall()
    for p in all_patients:
        conn.execute("UPDATE patients SET asha_worker_phone = ? WHERE id = ?", ('+919834358534', p['id']))
    conn.commit()
    patients = conn.execute("SELECT id, name FROM patients WHERE asha_worker_phone = '+919834358534' LIMIT 2").fetchall()

print(f"Adding HIGH priority alerts for:")
for p in patients:
    print(f"  - {p['name']} (ID: {p['id']})")

# Delete any existing alerts for these patients first
for p in patients:
    conn.execute("DELETE FROM patient_alerts WHERE patient_id = ?", (p['id'],))

# Add fresh HIGH severity alerts
alerts = [
    (patients[0]['id'], 'VITAL_TREND_WORSENING', 'HIGH', 
     '⚠️ Blood pressure readings show dangerous fluctuation pattern. Schedule urgent home visit.',
     'BP', '{"trend": "unstable"}'),
    (patients[1]['id'], 'MISSED_FOLLOW_UP', 'HIGH',
     '📅 Patient missed 2 scheduled follow-up appointments. Requires immediate outreach.',
     'APPOINTMENT', '{"missed_count": 2}'),
]

for alert in alerts:
    conn.execute("""
        INSERT INTO patient_alerts (patient_id, alert_type, severity, message, vital_name, trend_data, is_acknowledged)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, alert)

conn.commit()
print("\n✅ Added 2 HIGH priority AI tasks!")
conn.close()
