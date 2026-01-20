import sqlite3

def fix_db():
    conn = sqlite3.connect('health.db')
    
    print("Dropping old table...")
    conn.execute("DROP TABLE IF EXISTS pharmacy_inventory")
    
    print("Creating new table...")
    conn.execute("""
        CREATE TABLE pharmacy_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pharmacy_id INTEGER,
            medication TEXT NOT NULL,
            stock_status TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(id)
        );
    """)
    
    # Reseed basic data
    print("Seeding data...")
    conn.execute("INSERT INTO pharmacy_inventory (pharmacy_id, medication, stock_status) VALUES (1, 'Paracetamol 500mg', 'In Stock')")
    conn.execute("INSERT INTO pharmacy_inventory (pharmacy_id, medication, stock_status) VALUES (1, 'Amoxicillin 250mg', 'Low Stock')")
    conn.execute("INSERT INTO pharmacy_inventory (pharmacy_id, medication, stock_status) VALUES (2, 'Insulin', 'Out of Stock')")
    
    conn.commit()
    conn.close()
    print("Database fixed successfully.")

if __name__ == "__main__":
    fix_db()
