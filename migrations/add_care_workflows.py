import sqlite3

conn = sqlite3.connect("health.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS care_workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    current_state TEXT,
    next_action TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ care_workflows table added safely")
