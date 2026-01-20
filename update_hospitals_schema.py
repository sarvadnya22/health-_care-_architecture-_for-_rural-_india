import sqlite3

def update_schema():
    print("🏥 Updating Database Schema for Hospitals...")
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    try:
        # 1. Create Hospitals Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                district TEXT NOT NULL,
                location TEXT NOT NULL,
                type TEXT DEFAULT 'Government',
                contact_number TEXT
            )
        """)
        
        # 2. Seed Data (Avoid duplicates by checking first)
        hospitals = [
            ("Dhule Civil Hospital", "Dhule", "Sakri Road, Dhule", "02562-222222"),
            ("Rural Hospital Songir", "Dhule", "Main Road, Songir", "02562-233333"),
            ("Sassoon General Hospital", "Pune", "Station Road, Pune", "020-26128000"),
            ("District Hospital Nandurbar", "Nandurbar", "Patil Wadi, Nandurbar", "02564-222222"),
            ("Nabha Civil Hospital", "Pb", "Patiala Gate", "108") 
        ]
        
        count = 0
        for name, district, location, contact in hospitals:
            exists = cursor.execute("SELECT 1 FROM hospitals WHERE name = ?", (name,)).fetchone()
            if not exists:
                cursor.execute("""
                    INSERT INTO hospitals (name, district, location, contact_number)
                    VALUES (?, ?, ?, ?)
                """, (name, district, location, contact))
                count += 1
                
        conn.commit()
        print(f"✅ Schema updated. Added {count} new hospitals.")
        
        # Verify
        print("\n--- Available Hospitals ---")
        rows = cursor.execute("SELECT name, district FROM hospitals").fetchall()
        for r in rows:
            print(f"- {r[0]} ({r[1]})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_schema()
