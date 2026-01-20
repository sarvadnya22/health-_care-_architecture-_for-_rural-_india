import sqlite3

def inspect():
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(pharmacy_inventory)")
    cols = cursor.fetchall()
    print("Pharmacy Inventory Columns:")
    for col in cols:
        print(col)
    conn.close()

if __name__ == "__main__":
    inspect()
