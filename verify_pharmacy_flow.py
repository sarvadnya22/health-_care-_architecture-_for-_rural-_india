import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
import time

def verify_pharmacy_logic():
    print("🧪 Starting Pharmacy Logic Verification...")
    conn = sqlite3.connect('health.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # 1. Setup Test Data
        print("\n[1] Setting up test patients and prescriptions...")
        
        # Patient A: Dhule
        cursor.execute("INSERT INTO patients (name, phone_number, district, village, password_hash) VALUES ('Test Dhule', '9999999991', 'Dhule', 'Rampur', 'dummyhash')")
        p_dhule_id = cursor.lastrowid
        
        # Patient B: Pune
        cursor.execute("INSERT INTO patients (name, phone_number, district, village, password_hash) VALUES ('Test Pune', '9999999992', 'Pune', 'Shivaji Nagar', 'dummyhash')")
        p_pune_id = cursor.lastrowid
        
        # Prescription for A
        cursor.execute("""
            INSERT INTO prescriptions (patient_id, medication_name, status, is_active)
            VALUES (?, 'Paracetamol', 'Pending', 1)
        """, (p_dhule_id,))
        
        # Prescription for B
        cursor.execute("""
            INSERT INTO prescriptions (patient_id, medication_name, status, is_active)
            VALUES (?, 'Insulin', 'Pending', 1)
        """, (p_pune_id,))
        
        conn.commit()
        
        # 2. Verify Login Logic
        print("\n[2] Verifying Login Logic...")
        # Get Dhule Pharmacy
        pharma = cursor.execute("SELECT * FROM pharmacies WHERE district = 'Dhule'").fetchone()
        if not pharma:
            print("❌ FAIL: Dhule pharmacy not found")
            return
            
        if check_password_hash(pharma['password_hash'], "admin"):
            print("✅ PASS: Password verification works")
        else:
            print("❌ FAIL: Password verification failed")

        # 3. Verify District Filtering Logic (Simulating app.py query)
        print("\n[3] Verifying District Filtering...")
        
        # Case A: Dhule Pharmacy View
        print("   Checking Dhule Pharmacy View...")
        dhule_view = cursor.execute("""
            SELECT pr.*, p.name 
            FROM prescriptions pr
            JOIN patients p ON pr.patient_id = p.id
            WHERE pr.status = 'Pending' AND pr.is_active = 1
            AND (p.district = 'Dhule' OR p.district IS NULL)
        """).fetchall()
        
        found_dhule = any(r['patient_id'] == p_dhule_id for r in dhule_view)
        found_pune = any(r['patient_id'] == p_pune_id for r in dhule_view)
        
        if found_dhule and not found_pune:
            print("✅ PASS: Dhule pharmacy sees ONLY Dhule patients")
        else:
            print(f"❌ FAIL: Dhule pharmacy visibility incorrect. Found Dhule: {found_dhule}, Found Pune: {found_pune}")
            print([dict(r) for r in dhule_view])

        # Case B: Pune Pharmacy View
        print("   Checking Pune Pharmacy View...")
        pune_view = cursor.execute("""
            SELECT pr.*, p.name 
            FROM prescriptions pr
            JOIN patients p ON pr.patient_id = p.id
            WHERE pr.status = 'Pending' AND pr.is_active = 1
            AND (p.district = 'Pune' OR p.district IS NULL)
        """).fetchall()
        
        found_dhule_p = any(r['patient_id'] == p_dhule_id for r in pune_view)
        found_pune_p = any(r['patient_id'] == p_pune_id for r in pune_view)
        
        if found_pune_p and not found_dhule_p:
            print("✅ PASS: Pune pharmacy sees ONLY Pune patients")
        else:
            print(f"❌ FAIL: Pune pharmacy visibility incorrect. Found Dhule: {found_dhule_p}, Found Pune: {found_pune_p}")
            
        print("\n-------------------------------------------")
        print("🎉 verification Complete!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        # Cleanup test data? Maybe keep for manual check.
        conn.close()

if __name__ == "__main__":
    verify_pharmacy_logic()
