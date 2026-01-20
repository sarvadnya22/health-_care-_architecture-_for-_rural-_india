import sqlite3

def fix_prescriptions():
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    print("Checking prescriptions table schema...")
    try:
        cursor.execute("PRAGMA table_info(prescriptions)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add missing columns
        if 'medication' not in columns:
            print("Adding 'medication' column...")
            conn.execute("ALTER TABLE prescriptions ADD COLUMN medication TEXT")
            
        if 'dosage' not in columns:
            print("Adding 'dosage' column...")
            conn.execute("ALTER TABLE prescriptions ADD COLUMN dosage TEXT")
            
        if 'notes' not in columns:
            print("Adding 'notes' column...")
            conn.execute("ALTER TABLE prescriptions ADD COLUMN notes TEXT")
            
        if 'dispensed_by' not in columns:
            print("Adding 'dispensed_by' column...")
            conn.execute("ALTER TABLE prescriptions ADD COLUMN dispensed_by INTEGER")
            
        if 'is_active' not in columns:
            print("Adding 'is_active' column...")
            conn.execute("ALTER TABLE prescriptions ADD COLUMN is_active INTEGER DEFAULT 1")

        print("Prescriptions table fixed successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_prescriptions()
