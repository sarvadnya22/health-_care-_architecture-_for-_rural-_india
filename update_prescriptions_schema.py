import sqlite3

def update_schema():
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    # Check current columns
    cursor.execute('PRAGMA table_info(prescriptions)')
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Current columns: {columns}")
    
    if 'status' not in columns:
        print("Adding 'status' column...")
        conn.execute("ALTER TABLE prescriptions ADD COLUMN status TEXT DEFAULT 'Pending'")
    
    if 'dispensed_at' not in columns:
        print("Adding 'dispensed_at' column...")
        conn.execute("ALTER TABLE prescriptions ADD COLUMN dispensed_at DATETIME")

    # Ensure foreign keys are correct (assuming table exists)
    # If table doesn't exist (unlikely if app runs), we'd need to create it.
    # But based on prev errors, app runs, so table likely exists or init_db creates it.
    
    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    update_schema()
