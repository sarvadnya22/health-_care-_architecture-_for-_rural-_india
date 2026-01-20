import sqlite3

def fix_advisory_table():
    print("Fixing ministry_advisories table schema...")
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    # Drop existing table
    cursor.execute("DROP TABLE IF EXISTS ministry_advisories")
    
    # Create new table with correct schema
    cursor.execute("""
        CREATE TABLE ministry_advisories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            village TEXT,
            district TEXT DEFAULT 'Dhule',
            urgency TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Recreated ministry_advisories table with 'district' and 'urgency' columns.")

if __name__ == "__main__":
    fix_advisory_table()
