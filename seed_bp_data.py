import sqlite3

conn = sqlite3.connect('health.db')
conn.row_factory = sqlite3.Row

# Find Yogiraj Shinde's ID
yogiraj = conn.execute("SELECT id FROM patients WHERE name LIKE '%Yogiraj%'").fetchone()

if yogiraj:
    patient_id = yogiraj['id']
    print(f"Found Yogiraj Shinde with ID: {patient_id}")
    
    # Delete old BP readings for this patient
    conn.execute("DELETE FROM readings WHERE patient_id = ? AND reading_type = 'BP'", (patient_id,))
    print("Deleted old BP readings")
    
    # Seed INCONSISTENT Blood Pressure readings (30+ points variation)
    readings_data = [
        (patient_id, 'BP', 118, 75, "datetime('now', '-7 days')"),   # Normal
        (patient_id, 'BP', 155, 98, "datetime('now', '-6 days')"),   # High spike (+37)
        (patient_id, 'BP', 122, 78, "datetime('now', '-5 days')"),   # Back to normal (-33)
        (patient_id, 'BP', 160, 100, "datetime('now', '-4 days')"),  # High spike (+38)
        (patient_id, 'BP', 125, 80, "datetime('now', '-3 days')"),   # Normal (-35)
        (patient_id, 'BP', 165, 105, "datetime('now', '-2 days')"),  # Very high (+40)
        (patient_id, 'BP', 130, 82, "datetime('now', '-1 day')"),    # Dropped (-35)
        (patient_id, 'BP', 158, 95, "datetime('now')"),              # Spiked again (+28)
    ]
    
    for r in readings_data:
        conn.execute(f"""
            INSERT INTO readings (patient_id, reading_type, value1, value2, timestamp)
            VALUES (?, ?, ?, ?, {r[4]})
        """, (r[0], r[1], r[2], r[3]))
    
    conn.commit()
    print(f"Inserted {len(readings_data)} INCONSISTENT BP readings for Yogiraj Shinde!")
    print("\nNew readings (Systolic/Diastolic):")
    for i, r in enumerate(readings_data):
        print(f"  Day -{7-i}: {r[2]}/{r[3]}")
else:
    print("Yogiraj Shinde not found in database")

conn.close()
