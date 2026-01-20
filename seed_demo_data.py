"""
Demo Data Seeder for Rural HealthGuard
Creates 50+ realistic patients with triage reports and readings
Preserves existing data - only INSERTs new records
"""
import sqlite3
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

import json

# Indian names for realistic data
FIRST_NAMES_MALE = ["Ramesh", "Suresh", "Ganesh", "Mahesh", "Dinesh", "Rajesh", "Prakash", "Anil", "Sunil", "Vijay", 
                    "Santosh", "Manoj", "Arun", "Vinod", "Sanjay", "Ajay", "Deepak", "Rohit", "Amit", "Nitin"]
FIRST_NAMES_FEMALE = ["Sunita", "Anita", "Kavita", "Savita", "Rekha", "Meena", "Leena", "Seema", "Neeta", "Geeta",
                      "Priya", "Pooja", "Anjali", "Swati", "Nisha", "Asha", "Usha", "Maya", "Lata", "Radha"]
LAST_NAMES = ["Patil", "Deshmukh", "Jadhav", "Pawar", "Kulkarni", "Shinde", "More", "Gaikwad", "Chavan", "Kamble",
              "Sonawane", "Bhosale", "Wagh", "Mane", "Yadav", "Sharma", "Gupta", "Singh", "Kumar", "Joshi"]

VILLAGES = ["Udane", "Shirpur", "Nandurbar", "Sakri", "Taloda"]
ASHA_PHONE = "+919834358534"  # New ASHA worker (Kapadne)

SYMPTOMS_POOL = [
    ("High fever for 3 days", ["fever", "headache", "body ache"]),
    ("Chronic cough and cold", ["cough", "cold", "sore throat"]),
    ("Severe stomach pain", ["stomach pain", "nausea", "vomiting"]),
    ("Chest discomfort", ["chest pain", "difficulty breathing", "fatigue"]),
    ("Skin rash and itching", ["skin rash", "itching", "redness"]),
    ("Joint pain and swelling", ["joint pain", "swelling", "stiffness"]),
    ("Diarrhea and dehydration", ["diarrhea", "weakness", "dehydration"]),
    ("Diabetic symptoms", ["frequent urination", "thirst", "fatigue"]),
    ("Hypertension symptoms", ["dizziness", "headache", "blurred vision"]),
    ("Malaria-like symptoms", ["high fever", "chills", "sweating"]),
]

def get_db_connection():
    conn = sqlite3.connect('health.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"

def generate_email(name):
    return f"{name.lower().replace(' ', '.')}@patient.rural"

def random_date_in_past(days_back=30):
    delta = timedelta(days=random.randint(1, days_back))
    return (datetime.now() - delta).strftime('%Y-%m-%d %H:%M:%S')

def seed_patients(conn, count=50):
    """Create demo patients"""
    print(f"🌱 Seeding {count} demo patients...")
    cursor = conn.cursor()
    
    created = 0
    for i in range(count):
        gender = random.choice(["Male", "Female"])
        if gender == "Male":
            first_name = random.choice(FIRST_NAMES_MALE)
        else:
            first_name = random.choice(FIRST_NAMES_FEMALE)
        
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        phone = generate_phone()
        email = generate_email(full_name)
        village = random.choice(VILLAGES)
        age = random.randint(18, 75)
        
        # Hash a demo password
        password_hash = generate_password_hash("demo123")
        
        try:
            cursor.execute("""
                INSERT INTO patients (name, phone_number, email, password_hash, age, gender, village, asha_worker_phone, district)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Dhule')
            """, (full_name, phone, email, password_hash, age, gender, village, ASHA_PHONE))
            created += 1
        except Exception as e:
            # print(f"  Skip duplicate: {e}")
            pass
    
    conn.commit()
    print(f"  ✅ Created {created} patients")
    return created

def seed_triage_reports(conn, reports_per_patient=2):
    """Create triage reports for all patients"""
    print(f"🌱 Seeding triage reports...")
    cursor = conn.cursor()
    
    patients = cursor.execute("SELECT id, name, age FROM patients").fetchall()
    created = 0
    
    for patient in patients:
        for _ in range(random.randint(1, reports_per_patient)):
            chief_complaint, symptoms = random.choice(SYMPTOMS_POOL)
            symptoms_str = ", ".join(symptoms)
            notes = f"Patient {patient['name']} reported symptoms. Age: {patient['age']}"
            
            risk = random.choices(["Low", "Moderate", "High", "Critical"], weights=[40, 35, 20, 5])[0]
            decision = {
                "Low": "Home Care",
                "Moderate": "ASHA Follow-up", 
                "High": "Doctor Consultation",
                "Critical": "Emergency"
            }[risk]
            
            ai_prediction = f"<b>Risk:</b> {risk}<br><b>Decision:</b> {decision}<br><b>Diagnosis:</b> {chief_complaint}"
            
            timestamp = random_date_in_past(14)
            
            try:
                cursor.execute("""
                    INSERT INTO triage_reports (patient_id, chief_complaint, symptoms, notes, ai_prediction, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (patient['id'], chief_complaint, symptoms_str, notes, ai_prediction, timestamp))
                created += 1
            except Exception as e:
                print(f"  Report error: {e}")
    
    conn.commit()
    print(f"  ✅ Created {created} triage reports")
    return created

def seed_readings(conn, readings_per_patient=5):
    """Create BP and Sugar readings"""
    print(f"🌱 Seeding vital readings...")
    cursor = conn.cursor()
    
    patients = cursor.execute("SELECT id FROM patients").fetchall()
    created = 0
    
    for patient in patients:
        # BP readings
        for i in range(random.randint(2, readings_per_patient)):
            systolic = random.randint(100, 180)
            diastolic = random.randint(60, 100)
            timestamp = random_date_in_past(7)
            
            try:
                cursor.execute("""
                    INSERT INTO readings (patient_id, reading_type, value1, value2, timestamp)
                    VALUES (?, 'BP', ?, ?, ?)
                """, (patient['id'], systolic, diastolic, timestamp))
                created += 1
            except:
                pass
        
        # Sugar readings
        for i in range(random.randint(1, 3)):
            sugar = random.randint(80, 300)
            timestamp = random_date_in_past(7)
            
            try:
                cursor.execute("""
                    INSERT INTO readings (patient_id, reading_type, value1, value2, timestamp)
                    VALUES (?, 'SUGAR', ?, NULL, ?)
                """, (patient['id'], sugar, timestamp))
                created += 1
            except:
                pass
    
    conn.commit()
    print(f"  ✅ Created {created} readings")
    return created

def seed_prescriptions(conn):
    """Create sample prescriptions for some patients"""
    print(f"🌱 Seeding prescriptions...")
    cursor = conn.cursor()
    
    medications = ["Paracetamol 500mg", "Amoxicillin 250mg", "Metformin 500mg", "Amlodipine 5mg", 
                   "Omeprazole 20mg", "Cetirizine 10mg", "Ibuprofen 400mg", "Azithromycin 500mg"]
    dosages = ["1 tablet twice daily", "1 tablet thrice daily", "1 tablet once daily", "As needed"]
    
    patients = cursor.execute("SELECT id FROM patients").fetchall()
    created = 0
    
    for patient in random.sample(list(patients), min(30, len(patients))):
        medication = random.choice(medications)
        dosage = random.choice(dosages)
        status = random.choice(["Pending", "Dispensed"])
        timestamp = random_date_in_past(10)
        
        try:
            cursor.execute("""
                INSERT INTO prescriptions (patient_id, medication_name, medication, dosage, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient['id'], medication, medication, dosage, status, timestamp))
            created += 1
        except Exception as e:
            # print(f"  Prescription error: {e}")
            pass
    
    conn.commit()
    print(f"  ✅ Created {created} prescriptions")
    return created

def seed_agent_data(conn):
    """Seed updated Agentic AI tables: Workflows and Alerts"""
    print(f"🌱 Seeding Agent Workflows and Alerts...")
    cursor = conn.cursor()
    patients = cursor.execute("SELECT id, name FROM patients").fetchall()
    
    alert_created = 0
    workflow_created = 0
    
    for patient in random.sample(list(patients), min(15, len(patients))):
        # 1. Create a Workflow State
        state = random.choice(["MONITORING", "TRIAGE_NEEDED", "REFERRAL_PENDING", "TREATMENT"])
        action = "Monitor Vitals"
        status = "ACTIVE"
        
        if state == "REFERRAL_PENDING":
            action = "Coordinate with Doctor"
        elif state == "TRIAGE_NEEDED":
            action = "Conduct Triage Assessment"
            
        cursor.execute("""
            INSERT INTO care_workflows (patient_id, current_state, next_action, status)
            VALUES (?, ?, ?, ?)
        """, (patient['id'], state, action, status))
        workflow_created += 1
        
        # 2. Create Alerts (High/Severe for some)
        if random.random() > 0.6:
            severity = random.choice(["HIGH", "MEDIUM", "CRITICAL"])
            alert_type = "VITAL_TREND"
            msg = f"Abnormal vital signs detected for {patient['name']}"
            trend_data = json.dumps({
                "readings": [
                    {"value": "140/90", "date": "2023-10-01"},
                    {"value": "145/95", "date": "2023-10-03"}
                ]
            })
            
            cursor.execute("""
                INSERT INTO patient_alerts (patient_id, alert_type, severity, message, vital_name, trend_data)
                VALUES (?, ?, ?, ?, 'BP', ?)
            """, (patient['id'], alert_type, severity, msg, trend_data))
            alert_created += 1

    conn.commit()
    print(f"  ✅ Created {workflow_created} workflows and {alert_created} alerts")

def seed_referrals(conn):
    """Seed Doctor Referrals"""
    print(f"🌱 Seeding referrals...")
    cursor = conn.cursor()
    patients = cursor.execute("SELECT id FROM patients").fetchall()
    
    created = 0
    # Create tables if they don't exist (safety check, though setup_database should handle)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            referred_by_asha TEXT,
            doctor_id INTEGER,
            reason TEXT,
            priority TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    
    for patient in random.sample(list(patients), min(10, len(patients))):
        reason = random.choice(["Persistent Chest Pain", "Uncontrolled Diabetes", "Severe Infection", "High BP"])
        priority = random.choice(["Routine", "Urgent", "Emergency"])
        status = random.choice(["Pending", "Attended"])
        
        cursor.execute("""
            INSERT INTO referrals (patient_id, referred_by_asha, reason, priority, status)
            VALUES (?, ?, ?, ?, ?)
        """, (patient['id'], ASHA_PHONE, reason, priority, status))
        created += 1
        
    conn.commit()
    print(f"  ✅ Created {created} referrals")

def seed_advisories(conn):
    """Seed Ministry Advisories"""
    print(f"🌱 Seeding advisories...")
    cursor = conn.cursor()
    
    # Ensure advisory table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ministry_advisories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            village TEXT,
            district TEXT DEFAULT 'Dhule',
            urgency TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    advisories = [
        ("Dengue Outbreak Warning", "Increased dengue cases reported. Ensure no standing water.", "High"),
        ("Vaccination Drive", "Polio vaccination drive next Sunday at Community Center.", "Routine"),
        ("Heat Wave Alert", "Extreme temperatures expected. Advise hydration.", "Moderate")
    ]
    
    created = 0
    for title, content, severity in advisories:
        for village in VILLAGES:
            cursor.execute("""
                INSERT INTO ministry_advisories (title, content, village, district, urgency)
                VALUES (?, ?, ?, 'Dhule', ?)
            """, (title, content, village, severity))
            created += 1
            
    conn.commit()
    print(f"  ✅ Created {created} advisories")


def main():
    print("=" * 50)
    print("🚀 Rural HealthGuard Demo Data Seeder")
    print("=" * 50)
    print("⚠️  This will ADD data, not delete existing records.")
    print()
    
    conn = get_db_connection()
    
    # Count existing
    try:
        existing = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    except:
        existing = 0
    print(f"📊 Existing patients: {existing}")
    print()
    
    # Seed new data
    seed_patients(conn, count=30)
    seed_triage_reports(conn, reports_per_patient=2)
    seed_readings(conn, readings_per_patient=5)
    seed_prescriptions(conn)
    seed_agent_data(conn)
    seed_referrals(conn)
    seed_advisories(conn)
    
    # Final count
    new_total = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    print()
    print("=" * 50)
    print(f"✅ Complete! Total patients now: {new_total}")
    print("=" * 50)
    
    conn.close()

if __name__ == "__main__":
    main()
