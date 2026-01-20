import sqlite3
from werkzeug.security import generate_password_hash

def recreate_and_seed():
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    try:
        print("Dropping pharmacy tables...")
        conn.execute("DROP TABLE IF EXISTS pharmacy_inventory")
        conn.execute("DROP TABLE IF EXISTS pharmacies")
        
        print("Creating 'pharmacies' table...")
        conn.execute("""
            CREATE TABLE pharmacies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                district TEXT NOT NULL,
                location TEXT,
                email TEXT UNIQUE,
                password_hash TEXT
            )
        """)

        print("Creating 'pharmacy_inventory' table...")
        conn.execute("""
            CREATE TABLE pharmacy_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pharmacy_id INTEGER,
                medication TEXT NOT NULL,
                stock_status TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(id)
            )
        """)
        
        print("Seeding pharmacies...")
        # Password for all: 'admin'
        pwd_hash = generate_password_hash("admin")
        
        pharmacies = [
            (1, 'Jeevan Raksha Pharmacy', 'Dhule', 'Main Market, Rampur', 'dhule@pharma.com', pwd_hash),
            (2, 'City Medical Store', 'Pune', 'District Hospital Road', 'pune@pharma.com', pwd_hash),
            (3, 'Rural care Pharmacy', 'Nandurbar', 'Bus Stand, Taloda', 'nandurbar@pharma.com', pwd_hash)
        ]
        
        conn.executemany(
            "INSERT INTO pharmacies (id, name, district, location, email, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
            pharmacies
        )

        print("Inserting inventory data...")
        # Common meds from seed_demo_data.py
        meds = [
            "Paracetamol 500mg", "Amoxicillin 250mg", "Metformin 500mg", 
            "Amlodipine 5mg", "Omeprazole 20mg", "Cetirizine 10mg", 
            "Ibuprofen 400mg", "Azithromycin 500mg", "Insulin"
        ]
        
        inventory_data = []
        for p_id, _, _, _, _, _ in pharmacies:
            for med in meds:
                # Randomize stock slightly
                status = 'In Stock'
                if p_id == 2 and med == 'Insulin': status = 'Out of Stock' # Test case
                inventory_data.append((p_id, med, status))
        
        conn.executemany(
            "INSERT INTO pharmacy_inventory (pharmacy_id, medication, stock_status) VALUES (?, ?, ?)",
            inventory_data
        )
        
        conn.commit()
        print("Recreation and seeding complete.")
        
        # Verify
        print("\n--- Verification ---")
        cursor.execute("SELECT name, district, email FROM pharmacies")
        for row in cursor.fetchall():
            print(f"Pharmacy: {row}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    recreate_and_seed()
