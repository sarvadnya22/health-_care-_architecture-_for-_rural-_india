import sqlite3

def fix_database():
    db_path = 'health.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check 'prescriptions' table columns
        cursor.execute("PRAGMA table_info(prescriptions)")
        columns_info = cursor.fetchall()
        columns = [info[1] for info in columns_info]
        print(f"Current columns in 'prescriptions': {columns}")

        # List of columns to ensure exist
        # (Column Name, Type)
        required_columns = [
            ('dispensed_by', 'INTEGER'),
            ('is_active', 'BOOLEAN DEFAULT 1'),
            ('status', "TEXT DEFAULT 'Pending'"),
            ('dispensed_at', 'DATETIME') # From update_prescriptions_schema.py, seemingly needed
        ]

        for col_name, col_type in required_columns:
            if col_name not in columns:
                print(f"Adding missing column: {col_name} ({col_type})")
                try:
                    conn.execute(f"ALTER TABLE prescriptions ADD COLUMN {col_name} {col_type}")
                    print(f"Successfully added {col_name}")
                except Exception as e:
                    print(f"Error adding {col_name}: {e}")
            else:
                print(f"Column '{col_name}' already exists.")

        conn.commit()
        print("Database schema update completed.")
        
        # Verify
        cursor.execute("PRAGMA table_info(prescriptions)")
        final_columns = [info[1] for info in cursor.fetchall()]
        print(f"Final columns: {final_columns}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
