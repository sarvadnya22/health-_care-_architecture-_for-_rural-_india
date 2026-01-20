import sqlite3

def seed_data():
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    try:
        # 1. Clear existing inventory (which likely has 'Unknown' medications)
        print("Clearing 'pharmacy_inventory'...")
        conn.execute("DELETE FROM pharmacy_inventory")
        
        # 2. Verify pharmacies exist
        cursor.execute("SELECT count(*) FROM pharmacies")
        count = cursor.fetchone()[0]
        if count == 0:
            print("Seeding pharmacies...")
            conn.execute("INSERT INTO pharmacies (id, name, location) VALUES (1, 'Jeevan Raksha Pharmacy', 'Main Market, Rampur')")
            conn.execute("INSERT INTO pharmacies (id, name, location) VALUES (2, 'City Medical Store', 'District Hospital Road')")
        
        # 3. Insert Inventory Data
        print("Inserting inventory data...")
        data = [
            (1, 'Paracetamol 500mg', 'In Stock'),
            (1, 'Amoxicillin 250mg', 'Low Stock'),
            (1, 'Metformin 500mg', 'In Stock'),
            (2, 'Insulin', 'In Stock')
        ]
        
        conn.executemany(
            "INSERT INTO pharmacy_inventory (pharmacy_id, medication, stock_status) VALUES (?, ?, ?)",
            data
        )
        
        conn.commit()
        print("Seeding complete.")
        
        # Verify
        cursor.execute("SELECT * FROM pharmacy_inventory")
        rows = cursor.fetchall()
        print("Current Inventory:")
        for row in rows:
            print(row)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_data()
