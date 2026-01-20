import sqlite3

def fix_pharmacy_inventory():
    db_path = 'health.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check 'pharmacy_inventory' table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pharmacy_inventory'")
        if not cursor.fetchone():
            print("Table 'pharmacy_inventory' does not exist. Creating it...")
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
            print("Table 'pharmacy_inventory' created.")
        else:
            print("Table 'pharmacy_inventory' exists. Checking columns...")
            cursor.execute("PRAGMA table_info(pharmacy_inventory)")
            columns_info = cursor.fetchall()
            columns = [info[1] for info in columns_info]
            print(f"Current columns: {columns}")

            expected_columns = [
                ('pharmacy_id', 'INTEGER'),
                ('medication', 'TEXT NOT NULL DEFAULT "Unknown"'), # Default to avoid null issues on existing rows
                ('stock_status', 'TEXT'),
                ('last_updated', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
            ]

            for col_name, col_type in expected_columns:
                if col_name not in columns:
                    print(f"Adding missing column: {col_name}")
                    try:
                        conn.execute(f"ALTER TABLE pharmacy_inventory ADD COLUMN {col_name} {col_type}")
                        print(f"Added {col_name}")
                    except Exception as e:
                        print(f"Error adding {col_name}: {e}")

        conn.commit()
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_pharmacy_inventory()
