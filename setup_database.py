import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect('health.db')
cursor = connection.cursor()

# --- Drop all existing tables to ensure a clean start ---
cursor.execute("DROP TABLE IF EXISTS readings")
cursor.execute("DROP TABLE IF EXISTS prescriptions")
cursor.execute("DROP TABLE IF EXISTS triage_reports")
cursor.execute("DROP TABLE IF EXISTS pharmacy_inventory")
cursor.execute("DROP TABLE IF EXISTS pharmacies")
cursor.execute("DROP TABLE IF EXISTS patients")
cursor.execute("DROP TABLE IF EXISTS asha_workers")

# --- Create ASHA Workers Table ---
cursor.execute('''
CREATE TABLE asha_workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone_number TEXT UNIQUE NOT NULL,
    village TEXT,
    district TEXT DEFAULT 'Dhule'
)
''')

# --- Seed ASHA Workers ---
# 1. Existing ASHA from Udane
cursor.execute("INSERT INTO asha_workers (name, phone_number, village, district) VALUES (?, ?, ?, ?)", 
               ("Main ASHA Worker", "+919123456789", "Udane", "Dhule"))

# 2. New ASHA from Kapadne
cursor.execute("INSERT INTO asha_workers (name, phone_number, village, district) VALUES (?, ?, ?, ?)", 
               ("ASHA Worker (Kapadne)", "+919834358534", "Kapadne", "Dhule"))

# --- Create Patients Table ---
cursor.execute('''
CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone_number TEXT UNIQUE NOT NULL,
    email TEXT, password_hash TEXT NOT NULL, active_call_link TEXT, age INTEGER, gender TEXT,
    village TEXT, district TEXT DEFAULT 'Dhule', asha_worker_phone TEXT 
)''')

# --- Create Pharmacies & Inventory Tables ---
cursor.execute('''CREATE TABLE pharmacies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, location TEXT)''')
cursor.execute('''
CREATE TABLE pharmacy_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT, pharmacy_id INTEGER, medication_name TEXT NOT NULL,
    stock_status TEXT NOT NULL, last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pharmacy_id) REFERENCES pharmacies (id)
)''')

# --- Create Prescriptions Table ---
cursor.execute('''
CREATE TABLE prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, medication_name TEXT NOT NULL,
    dosage TEXT, notes TEXT, is_active INTEGER DEFAULT 1, dispensing_pharmacy_id INTEGER, 
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (patient_id) REFERENCES patients (id),
    FOREIGN KEY (dispensing_pharmacy_id) REFERENCES pharmacies (id)
)''')

# --- Create Readings Table ---
cursor.execute('''
CREATE TABLE readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, reading_type TEXT NOT NULL, 
    value1 INTEGER NOT NULL, value2 INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY (patient_id) REFERENCES patients (id)
)''')

# --- Create Triage Reports Table (UPDATED SCHEMA) ---
cursor.execute('''
CREATE TABLE triage_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    patient_id INTEGER, 
    chief_complaint TEXT NOT NULL,
    symptoms TEXT, 
    notes TEXT, 
    ai_prediction TEXT, -- NEW COLUMN for AI output
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients (id)
)
''')

# --- AGENT SYSTEM TABLES ---

# Table 1: Agent Decision Logging
cursor.execute('''
CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    input_data TEXT,
    output_data TEXT,
    execution_time_ms INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
)
''')

# Table 2: Patient Alerts
cursor.execute('''
CREATE TABLE IF NOT EXISTS patient_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    vital_name TEXT,
    trend_data TEXT,
    is_acknowledged BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at DATETIME,
    acknowledged_by TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
)
''')

# Table 3: Follow-up Schedule
cursor.execute('''
CREATE TABLE IF NOT EXISTS follow_up_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    scheduled_date DATE NOT NULL,
    visit_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    created_by_agent TEXT,
    notes TEXT,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
)
''')

# --- Ministry Advisories Table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS ministry_advisories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    village TEXT,
    district TEXT DEFAULT 'Dhule',
    urgency TEXT,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
# Sample Advisory
cursor.execute("INSERT INTO ministry_advisories (title, content, village, district, urgency) VALUES (?, ?, ?, ?, ?)", 
               ("Polio Drive", "Polio vaccination camp this Sunday.", "Songir", "Dhule", "Routine"))

# --- Indexes for Agent System ---
cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_logs_patient ON agent_logs(patient_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON agent_logs(timestamp)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_patient_alerts_patient ON patient_alerts(patient_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_patient_alerts_severity ON patient_alerts(severity, is_acknowledged)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_follow_up_schedule_patient ON follow_up_schedule(patient_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_follow_up_schedule_date ON follow_up_schedule(scheduled_date, status)")

# --- Insert Sample Data ---
cursor.execute("INSERT INTO pharmacies (name, location) VALUES (?, ?)", ('Nabha Civil Hospital Pharmacy', 'Nabha City'))
cursor.execute("INSERT INTO pharmacies (name, location) VALUES (?, ?)", ('PHC Bhadson Pharmacy', 'Bhadson Village'))
cursor.execute("INSERT INTO pharmacy_inventory (pharmacy_id, medication_name, stock_status) VALUES (?, ?, ?)", (1, 'Paracetamol 500mg', 'In Stock'))
cursor.execute("INSERT INTO pharmacy_inventory (pharmacy_id, medication_name, stock_status) VALUES (?, ?, ?)", (1, 'Metformin 500mg', 'Out of Stock'))
cursor.execute("INSERT INTO pharmacy_inventory (pharmacy_id, medication_name, stock_status) VALUES (?, ?, ?)", (2, 'Metformin 500mg', 'In Stock'))

hashed_password = generate_password_hash('password123')
asha_phone = '+919123456789'
cursor.execute("INSERT INTO patients (name, phone_number, age, gender, village, password_hash, asha_worker_phone) VALUES (?, ?, ?, ?, ?, ?, ?)", 
    ('Ramesh Patil', '+919876543210', 65, 'Male', 'Songir', hashed_password, asha_phone))

# Sample alert for demonstration
try:
    cursor.execute("""
    INSERT INTO patient_alerts (patient_id, alert_type, severity, message, vital_name, trend_data, is_acknowledged)
    VALUES (1, 'VITAL_TREND_WORSENING', 'HIGH', 'Blood pressure rising trend detected (30 points in 5 days)', 'BP', 
    '{"readings": [{"value": "130/85", "date": "2025-12-11"}, {"value": "145/90", "date": "2025-12-13"}, {"value": "160/95", "date": "2025-12-16"}]}', 0)
    """)
except Exception as e:
    print(f"Warning: Could not insert sample alert: {e}")

connection.commit()
connection.close()
print("Database `health.db` was reset with the complete schema, including the new AI prediction column and Agent System tables.")

