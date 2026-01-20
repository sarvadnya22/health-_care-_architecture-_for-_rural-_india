"""
Extended Seeder: ASHA Workers, Patient Assignments, and Referrals
Creates 5 additional ASHA workers with 10 patients each
Generates triage reports and doctor referrals for testing
"""
import sqlite3
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# ASHA Worker data
ASHA_WORKERS = [
    ("+919111111111", "Sunita Patil", "Udane"),
    ("+919222222222", "Meena Jadhav", "Shirpur"),
    ("+919333333333", "Kavita Shinde", "Nandurbar"),
    ("+919444444444", "Rekha Pawar", "Sakri"),
    ("+919555555555", "Anjali Deshmukh", "Taloda"),
]

# Patient names
FIRST_NAMES_MALE = ["Ramesh", "Suresh", "Ganesh", "Mahesh", "Dinesh", "Rajesh", "Prakash", "Anil", "Sunil", "Vijay"]
FIRST_NAMES_FEMALE = ["Sunita", "Anita", "Kavita", "Savita", "Rekha", "Meena", "Leena", "Seema", "Neeta", "Geeta"]
LAST_NAMES = ["Patil", "Deshmukh", "Jadhav", "Pawar", "Kulkarni", "Shinde", "More", "Gaikwad", "Chavan", "Kamble"]

SYMPTOMS_POOL = [
    ("High fever for 3 days", ["fever", "headache", "body ache"], "High"),
    ("Chronic cough and cold", ["cough", "cold", "sore throat"], "Moderate"),
    ("Severe stomach pain", ["stomach pain", "nausea", "vomiting"], "High"),
    ("Chest discomfort", ["chest pain", "difficulty breathing", "fatigue"], "Critical"),
    ("Skin rash and itching", ["skin rash", "itching", "redness"], "Low"),
    ("Joint pain and swelling", ["joint pain", "swelling", "stiffness"], "Moderate"),
    ("Diarrhea and dehydration", ["diarrhea", "weakness", "dehydration"], "High"),
    ("Diabetic symptoms", ["frequent urination", "thirst", "fatigue"], "Moderate"),
    ("Hypertension symptoms", ["dizziness", "headache", "blurred vision"], "High"),
    ("Malaria-like symptoms", ["high fever", "chills", "sweating"], "Critical"),
]

def get_db_connection():
    conn = sqlite3.connect('health.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"

def random_date_in_past(days_back=7):
    delta = timedelta(days=random.randint(1, days_back))
    return (datetime.now() - delta).strftime('%Y-%m-%d %H:%M:%S')

def seed_asha_workers_and_patients():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🚀 Extended Data Seeder: ASHA Workers & Referrals")
    print("=" * 60)
    
    all_created_patient_ids = []
    
    for asha_phone, asha_name, village in ASHA_WORKERS:
        print(f"\n👩‍⚕️ Creating ASHA Worker: {asha_name} ({asha_phone}) - {village}")
        
        # Create 10 patients for this ASHA worker
        patient_ids = []
        for i in range(10):
            gender = random.choice(["Male", "Female"])
            if gender == "Male":
                first_name = random.choice(FIRST_NAMES_MALE)
            else:
                first_name = random.choice(FIRST_NAMES_FEMALE)
            
            last_name = random.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"
            phone = generate_phone()
            age = random.randint(18, 75)
            password_hash = generate_password_hash("demo123")
            
            try:
                cursor.execute("""
                    INSERT INTO patients (name, phone_number, password_hash, age, gender, village, asha_worker_phone, district)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Dhule')
                """, (full_name, phone, password_hash, age, gender, village, asha_phone))
                
                patient_id = cursor.lastrowid
                patient_ids.append(patient_id)
                all_created_patient_ids.append(patient_id)
                print(f"   ✅ Patient: {full_name} (ID: {patient_id})")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Create triage reports for each patient
        print(f"   📋 Creating triage reports...")
        for patient_id in patient_ids:
            chief_complaint, symptoms, risk = random.choice(SYMPTOMS_POOL)
            symptoms_str = ", ".join(symptoms)
            notes = f"Patient visited ASHA worker {asha_name}. Symptoms observed."
            
            decision = {
                "Low": "Home Care",
                "Moderate": "ASHA Follow-up", 
                "High": "Doctor Consultation",
                "Critical": "Emergency"
            }[risk]
            
            ai_prediction = f"<b>Risk:</b> {risk}<br><b>Decision:</b> {decision}<br><b>Diagnosis:</b> {chief_complaint}"
            timestamp = random_date_in_past(7)
            
            try:
                cursor.execute("""
                    INSERT INTO triage_reports (patient_id, chief_complaint, symptoms, notes, ai_prediction, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (patient_id, chief_complaint, symptoms_str, notes, ai_prediction, timestamp))
            except Exception as e:
                print(f"   ❌ Triage error: {e}")
        
        # Create 2-3 referrals per ASHA worker (for high/critical cases)
        high_risk_patients = random.sample(patient_ids, min(3, len(patient_ids)))
        print(f"   🏥 Creating doctor referrals...")
        for patient_id in high_risk_patients:
            reason = random.choice([
                "Patient requires specialist consultation",
                "Symptoms worsening despite treatment",
                "High blood pressure detected",
                "Suspected infection requiring antibiotics",
                "Chest pain needs ECG evaluation"
            ])
            priority = random.choice(["Urgent", "Emergency", "Normal"])
            timestamp = random_date_in_past(3)
            
            try:
                cursor.execute("""
                    INSERT INTO referrals (patient_id, referred_by_asha, reason, priority, status, created_at)
                    VALUES (?, ?, ?, ?, 'Pending', ?)
                """, (patient_id, asha_phone, reason, priority, timestamp))
                print(f"      ➡️ Referral created for Patient ID {patient_id} ({priority})")
            except Exception as e:
                print(f"   ❌ Referral error: {e}")
    
    conn.commit()
    
    # Summary
    total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    total_referrals = conn.execute("SELECT COUNT(*) FROM referrals WHERE status = 'Pending'").fetchone()[0]
    total_triage = conn.execute("SELECT COUNT(*) FROM triage_reports").fetchone()[0]
    
    print("\n" + "=" * 60)
    print("✅ Seeding Complete!")
    print("=" * 60)
    print(f"   📊 Total Patients: {total_patients}")
    print(f"   📋 Total Triage Reports: {total_triage}")
    print(f"   🏥 Pending Referrals: {total_referrals}")
    print("\n🔑 ASHA Worker Logins (use these in the app):")
    for phone, name, village in ASHA_WORKERS:
        print(f"   {name}: {phone} (Village: {village})")
    print("\n   Password for all demo accounts: demo123")
    
    conn.close()

if __name__ == "__main__":
    seed_asha_workers_and_patients()
